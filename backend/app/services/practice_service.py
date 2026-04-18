"""
Practice Service — buffered session orchestrator.

Buffered architecture:
  Per Answer (fast path, Redis-only):
    submit_answer() → evaluate correctness (Levenshtein similarity)
                    → RPUSH RawAnswerEvent to Redis list
                    → return 202 with minimal feedback
                    → NO PostgreSQL writes, NO SM-2 computation

  Finalize / Abandon (batch path, single DB transaction):
    _flush_session() → LRANGE all raw events from Redis
                     → compute SM-2 for each item in one pass
                     → UPDATE UserProgress for all items
                     → INSERT StudyReview rows (ON CONFLICT DO NOTHING)
                     → UPDATE StudySession aggregates + status
                     → COMMIT
                     → DELETE Redis keys

Study direction:
  User sees:  translation.term_trans  (target language — e.g. "book")
  User types: item.term               (source language — e.g. "libro")

Full batch delivery:
  At session start ALL item hints are fetched and returned in the response.
  The frontend practices entirely offline — no per-card round-trips.
  item_hints are also cached in Redis SessionState for reconstruction.

Session recovery:
  GET /practice/sessions/active
    1. Check Redis practice:active:{user_id} → session_id
    2. If miss, query DB study_sessions WHERE status = 'in_progress'
    3. If found, reconstruct state from DB + pending_sessions safety valve

Flush lock:
  practice:flushing:{session_id} (Redis SET NX) prevents two concurrent
  callers (user + sweeper) from running _flush_session simultaneously.
"""

import logging
from datetime import datetime, timezone

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BusinessRuleViolationError,
    NotAuthorizedToStudyError,
    ResourceNotFoundError,
)
from app.models.enums import EvaluationMode, SessionStatus
from app.models.set import Set
from app.repositories.practice_repo import PracticeRepository
from app.schemas.practice import (
    ComparisonConfig,
    ItemHintSchema,
    SessionStartedResponse,
)
from app.services.answer_evaluator import (
    DEFAULT_EXPECTED_MS,
    EvaluationContext,
    evaluate as eval_answer,
)
from app.services.progress_updater import ProgressUpdater
from app.services.session_manager import (
    BatchConfig,
    INTENSITY_MAP,
    RawAnswerEvent,
    SessionManager,
    SessionState,
    make_session_state,
)
from app.services.sm2_engine import initial_state

logger = logging.getLogger(__name__)


# ── Request DTO ───────────────────────────────────────────────────────────────


class SubmitAnswerRequest:
    """
    Internal DTO for answer submission.

    Correct answer is NOT included — it is read from the item_hints cache
    to prevent clients from injecting tampered values.
    """

    __slots__ = (
        "item_id",
        "user_answer",
        "response_time_ms",
        "confidence_override",
        "answer_id",
    )

    def __init__(
        self,
        *,
        item_id: int,
        user_answer: str,
        response_time_ms: int,
        confidence_override: int | None = None,
        answer_id: str = "",
    ) -> None:
        self.item_id = item_id
        self.user_answer = user_answer
        self.response_time_ms = response_time_ms
        self.confidence_override = confidence_override
        self.answer_id = answer_id


# ── Orchestrator ──────────────────────────────────────────────────────────────


class PracticeService:
    """Stateless per-request orchestrator. Delegates DB work to repos."""

    def __init__(self, db: AsyncSession, redis: aioredis.Redis, user_id: int) -> None:
        self._db = db
        self._redis = redis
        self._user_id = user_id
        self._repo = PracticeRepository(db)
        self._session_mgr = SessionManager(redis)
        self._updater = ProgressUpdater(db)

    # ── Start ─────────────────────────────────────────────────────────────────

    async def start_session(self, set_id: int) -> SessionStartedResponse:
        """
        Initialise a new practice session and return the full item batch.

        1. Verify the set exists and the user has access.
        2. Block if user already has an in-progress session.
        3. Select items (due reviews first, then new items).
        4. Seed UserProgress rows for brand-new items.
        5. Fetch ALL item hints in a single batch query.
        6. Create a StudySession DB record (source of truth).
        7. Seed Redis state.
        8. Return SessionStartedResponse with full items + comparison_config.
        """
        await self._assert_no_active_session()

        db_set = await self._repo.get_set(set_id)
        if db_set is None:
            raise ResourceNotFoundError("Set", set_id)
        if not await self._user_can_study_set(db_set):
            raise NotAuthorizedToStudyError(set_id, self._user_id)

        config = await self._build_batch_config(db_set)
        item_ids = await self._select_items(set_id, config)

        if not item_ids:
            raise ResourceNotFoundError("due items", f"set {set_id}")

        item_hints = await self._repo.fetch_item_hints(
            item_ids, set_id, config.target_lang_id, self._user_id
        )

        # Flush the session row to get its ID; commit happens AFTER Redis writes
        # so a Redis failure rolls back the DB record atomically.
        db_session = await self._repo.create_session(self._user_id, set_id)

        state = make_session_state(
            session_id=db_session.id,
            user_id=self._user_id,
            set_id=set_id,
            item_order=item_ids,
            config=config,
            item_hints=item_hints,
        )
        try:
            await self._session_mgr.save_session(state)
            await self._session_mgr.set_active(self._user_id, db_session.id)
        except Exception:
            # Redis failed — rollback DB to avoid orphaned in-progress session
            await self._db.rollback()
            raise

        await self._db.commit()

        logger.info(
            "session_started",
            extra={
                "session_id": db_session.id,
                "user_id": self._user_id,
                "set_id": set_id,
                "item_count": len(item_ids),
            },
        )

        items = [
            ItemHintSchema(
                item_id=item_id,
                **{
                    k: v
                    for k, v in (item_hints.get(str(item_id)) or {}).items()
                    if k != "item_id"
                },
            )
            for item_id in item_ids
        ]

        return SessionStartedResponse(
            session_id=db_session.id,
            set_id=set_id,
            items=items,
            comparison_config=_config_to_comparison(config),
        )

    # ── Submit answer (fast Redis-only path) ──────────────────────────────────

    async def submit_answer(
        self,
        session_id: int,
        req: SubmitAnswerRequest,
    ) -> tuple[bool, float, str, SessionState]:
        """
        Buffer one answer event.

        Returns (is_correct, similarity, correct_answer, updated_state).
        The route returns a minimal 202; the frontend already has the answer
        from the initial batch so correctness is only for UX convenience.
        """
        state = await self._load_state_or_raise(session_id)

        if state.is_complete:
            raise ResourceNotFoundError("pending item", session_id)

        if req.item_id != state.next_item_id:
            raise ValueError(
                f"Expected item {state.next_item_id}, got {req.item_id}. "
                "Submit answers in order."
            )

        hint = state.get_hint(req.item_id)
        if hint is None:
            hint = await self._repo.fetch_item_hints(
                [req.item_id], state.set_id, state.config.target_lang_id, self._user_id
            )
            hint = (hint or {}).get(str(req.item_id))

        correct_answer = hint["answer"] if hint else ""
        translation_id: int | None = hint.get("translation_id") if hint else None

        evaluation_mode = EvaluationMode(state.config.evaluation_mode)
        ctx = EvaluationContext(
            user_answer=req.user_answer,
            correct_answer=correct_answer,
            response_time_ms=req.response_time_ms,
            expected_time_ms=DEFAULT_EXPECTED_MS,
            evaluation_mode=evaluation_mode,
            confidence_override=req.confidence_override,
        )
        eval_result = eval_answer(ctx)

        event = RawAnswerEvent(
            item_id=req.item_id,
            translation_id=translation_id,
            user_answer=req.user_answer,
            response_time_ms=req.response_time_ms,
            confidence_override=req.confidence_override,
            answered_at=datetime.now(timezone.utc).isoformat(),
            is_correct=eval_result.is_correct,
            similarity=eval_result.similarity,
            correct_answer=correct_answer,
            answer_id=req.answer_id,
        )

        updated_state = await self._session_mgr.append_raw_answer(session_id, event)
        if updated_state is None:
            updated_state = await self._reconstruct_state(session_id)

        logger.info(
            "answer_buffered",
            extra={
                "session_id": session_id,
                "item_id": req.item_id,
                "is_correct": eval_result.is_correct,
                "similarity": round(eval_result.similarity, 4),
            },
        )

        return (
            eval_result.is_correct,
            eval_result.similarity,
            correct_answer,
            updated_state,
        )

    # ── Finalize / Abandon ────────────────────────────────────────────────────

    async def finalize_session(self, session_id: int) -> dict:
        """Flush session with COMPLETED status."""
        return await self._flush_session(session_id, status=SessionStatus.COMPLETED)

    async def abandon_session(self, session_id: int) -> dict:
        """
        Flush session with ABANDONED status.

        Same DB write path as finalize: buffered answers are persisted and
        SM-2 is computed for all answered items. The session is simply marked
        abandoned rather than completed.
        """
        return await self._flush_session(session_id, status=SessionStatus.ABANDONED)

    async def _flush_session(self, session_id: int, *, status: SessionStatus) -> dict:
        """
        Shared finalize/abandon logic.

        Uses a Redis flush lock (SET NX) to prevent two concurrent callers
        (e.g. user + sweeper) from processing the same session simultaneously.
        """
        db_session = await self._repo.get_session(session_id)
        if db_session is None:
            raise ResourceNotFoundError("StudySession", session_id)
        if db_session.user_id != self._user_id:
            raise NotAuthorizedToStudyError(session_id, self._user_id)

        # Idempotency: already flushed
        if db_session.ended_at is not None:
            await self._session_mgr.clear_active(self._user_id)
            return await self._build_summary_from_db(session_id)

        # Acquire flush lock — prevents double-processing
        if not await self._session_mgr.acquire_flush_lock(session_id):
            raise BusinessRuleViolationError(
                f"Session {session_id} is already being finalised."
            )

        try:
            state = await self._load_state_or_raise(session_id)
            raw_events = await self._session_mgr.get_raw_answers(session_id)

            summary = await self._updater.finalise_batch(
                state=state,
                raw_events=raw_events,
                db_session=db_session,
                session_mgr=self._session_mgr,
                final_status=status,
            )
        finally:
            await self._session_mgr.release_flush_lock(session_id)

        await self._session_mgr.clear_active(self._user_id)
        summary["status"] = status.value
        return summary

    # ── Summary ───────────────────────────────────────────────────────────────

    async def get_session_summary(self, session_id: int) -> dict:
        state = await self._session_mgr.load_session(session_id)
        if state is not None:
            if state.user_id != self._user_id:
                raise NotAuthorizedToStudyError(session_id, self._user_id)
            raw_events = await self._session_mgr.get_raw_answers(session_id)
            return _build_summary_from_raw(session_id, raw_events)

        return await self._build_summary_from_db(session_id)

    # ── Active session recovery ───────────────────────────────────────────────

    async def get_active_session(self) -> SessionState | None:
        session_id = await self._session_mgr.get_active_session_id(self._user_id)
        if session_id is not None:
            state = await self._session_mgr.load_session(session_id)
            if state is not None:
                return state

        db_session = await self._repo.get_active_db_session(self._user_id)
        if db_session is None:
            return None

        try:
            return await self._reconstruct_state(db_session.id)
        except Exception:
            logger.warning(
                "session_reconstruction_failed",
                extra={"session_id": db_session.id, "user_id": self._user_id},
            )
            return None

    async def get_state(self, session_id: int) -> SessionState:
        return await self._load_state_or_raise(session_id)

    async def refresh_comparison_config(self, session_id: int) -> "ComparisonConfig":
        """
        Re-read UserSettings and update the session's comparison/hint config in Redis.

        Call this after the user changes settings mid-session. The updated
        ComparisonConfig is returned so the frontend can re-render hint controls.
        """
        state = await self._load_state_or_raise(session_id)
        if state.user_id != self._user_id:
            raise NotAuthorizedToStudyError(session_id, self._user_id)

        db_set = await self._repo.get_set(state.set_id)
        new_config = await self._build_batch_config(db_set)

        updated_state = SessionState(
            session_id=state.session_id,
            user_id=state.user_id,
            set_id=state.set_id,
            item_order=state.item_order,
            current_index=state.current_index,
            config=new_config,
            started_at=state.started_at,
            item_hints=state.item_hints,
            last_answered_at=state.last_answered_at,
        )
        await self._session_mgr.save_session(updated_state)
        return _config_to_comparison(new_config)

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _assert_no_active_session(self) -> None:
        # Fast path: Redis active pointer
        session_id = await self._session_mgr.get_active_session_id(self._user_id)
        if session_id is not None:
            existing = await self._session_mgr.load_session(session_id)
            if existing is not None and not existing.is_complete:
                raise BusinessRuleViolationError(
                    f"Session {session_id} is still in progress. "
                    "Finalise or abandon it before starting a new one."
                )

        # Slow path: Redis cold or TTL-expired — orphaned DB session.
        # Redis state is gone (24h TTL or eviction), so any buffered answers are
        # already lost. Auto-abandon to unblock the user rather than raising.
        db_session = await self._repo.get_active_db_session(self._user_id)
        if db_session is not None:
            db_session.status = SessionStatus.ABANDONED
            db_session.ended_at = datetime.now(timezone.utc)
            await self._db.flush()
            await self._session_mgr.clear_active(self._user_id)
            logger.warning(
                "orphaned_session_auto_abandoned",
                extra={"session_id": db_session.id, "user_id": self._user_id},
            )

    async def _load_state_or_raise(self, session_id: int) -> SessionState:
        state = await self._session_mgr.load_session(session_id)
        if state is not None:
            return state
        logger.warning(
            "session_redis_miss_reconstructing",
            extra={"session_id": session_id, "user_id": self._user_id},
        )
        return await self._reconstruct_state(session_id)

    async def _reconstruct_state(self, session_id: int) -> SessionState:
        db_session = await self._repo.get_session(session_id)
        if db_session is None:
            raise ResourceNotFoundError("StudySession", session_id)
        if db_session.user_id != self._user_id:
            raise NotAuthorizedToStudyError(db_session.set_id, self._user_id)

        db_set = await self._repo.get_set(db_session.set_id)
        if db_set is None:
            raise ResourceNotFoundError("Set", db_session.set_id)
        config = await self._build_batch_config(db_set)

        answered_ids = await self._repo.get_answered_ids_from_pending(session_id)
        if not answered_ids:
            answered_ids = await self._repo.get_answered_ids_from_reviews(session_id)

        remaining_ids = await self._select_items(
            db_session.set_id, config, exclude_ids=set(answered_ids)
        )

        item_order = answered_ids + remaining_ids
        item_hints = await self._repo.fetch_item_hints(
            item_order, db_session.set_id, config.target_lang_id, self._user_id
        )

        state = SessionState(
            session_id=session_id,
            user_id=self._user_id,
            set_id=db_session.set_id,
            item_order=item_order,
            current_index=len(answered_ids),
            config=config,
            started_at=db_session.started_at.isoformat(),
            item_hints=item_hints,
        )

        await self._session_mgr.save_session(state)
        await self._session_mgr.set_active(self._user_id, session_id)
        logger.info(
            "session_reconstructed",
            extra={"session_id": session_id, "answered": len(answered_ids)},
        )
        return state

    async def _build_summary_from_db(self, session_id: int) -> dict:
        db_session = await self._repo.get_session(session_id)
        if db_session is None:
            raise ResourceNotFoundError("StudySession", session_id)
        if db_session.user_id != self._user_id:
            raise NotAuthorizedToStudyError(session_id, self._user_id)

        summary = await self._repo.get_session_reviews_summary(session_id)
        return {
            "session_id": session_id,
            "status": db_session.status.value,
            **summary,
            "leech_item_ids": [],
        }

    async def _user_can_study_set(self, db_set: Set) -> bool:
        if db_set.creator_id == self._user_id:
            return True
        return await self._repo.check_library_access(self._user_id, db_set.id)

    async def _build_batch_config(self, db_set: Set | None) -> BatchConfig:
        settings = await self._repo.get_user_settings(self._user_id)
        target_lang_id = db_set.target_lang_id if db_set else 0

        if settings is None:
            return BatchConfig(target_lang_id=target_lang_id)

        return BatchConfig(
            evaluation_mode=settings.evaluation_mode.value,
            review_intensity=INTENSITY_MAP.get(settings.learning_intensity.value, 1.0),
            batch_size=settings.daily_study_goal,
            new_items_per_session=settings.new_items_per_session,
            target_lang_id=target_lang_id,
            show_hints_on_fails=settings.show_hints_on_fails,
            show_translations=settings.show_translations,
            show_images=settings.show_images,
            show_synonyms=settings.show_synonyms,
            show_part_of_speech=settings.show_part_of_speech,
            auto_play_audio=settings.auto_play_audio,
        )

    async def _select_items(
        self,
        set_id: int,
        config: BatchConfig,
        *,
        exclude_ids: set[int] | None = None,
    ) -> list[int]:
        due_ids = await self._repo.select_due_item_ids(
            self._user_id, set_id, config.batch_size, exclude_ids
        )

        slots_for_new = min(
            config.new_items_per_session,
            config.batch_size - len(due_ids),
        )
        new_ids: list[int] = []

        if slots_for_new > 0:
            combined_exclude = (exclude_ids or set()) | set(due_ids)
            new_ids = await self._repo.select_new_item_ids(
                self._user_id, set_id, slots_for_new, combined_exclude
            )
            if new_ids:
                init = initial_state()
                await self._repo.seed_progress_bulk(
                    self._user_id,
                    new_ids,
                    ease_factor=float(init.ease_factor),
                    interval=init.interval_days,
                    repetitions=init.repetitions,
                    lapsed_attempts=init.lapsed_attempts,
                )

        return due_ids + new_ids


# ── Pure helpers ──────────────────────────────────────────────────────────────


def _config_to_comparison(config: BatchConfig) -> ComparisonConfig:
    return ComparisonConfig(
        evaluation_mode=config.evaluation_mode,
        show_hints_on_fails=config.show_hints_on_fails,
        show_translations=config.show_translations,
        show_images=config.show_images,
        show_synonyms=config.show_synonyms,
        show_part_of_speech=config.show_part_of_speech,
        auto_play_audio=config.auto_play_audio,
    )


def _build_summary_from_raw(session_id: int, raw_events: list[RawAnswerEvent]) -> dict:
    total = len(raw_events)
    correct = sum(1 for e in raw_events if e.is_correct)
    avg_ms = sum(e.response_time_ms for e in raw_events) // total if total else 0
    return {
        "session_id": session_id,
        "status": "in_progress",
        "total_reviewed": total,
        "correct_count": correct,
        "accuracy": round(correct / total, 4) if total else 0.0,
        "avg_response_ms": avg_ms,
        "leech_item_ids": [],
    }


__all__ = ["PracticeService", "SubmitAnswerRequest"]
