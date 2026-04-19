# backend/app/services/progress_updater.py
"""
Progress Updater — atomic PostgreSQL persistence for session finalisation.

Batch SM-2 processing path (called from PracticeService.finalize_session):

  1. For each RawAnswerEvent:
       a. Load UserProgress (SELECT … FOR UPDATE).
       b. Compute expected response time (4-level hierarchy).
       c. Compute quality score from stored similarity + timing.
       d. Apply long-absence EF decay if applicable.
       e. Run SM-2 update → new state + next_review_at.
       f. Update UserProgress (flush, NOT committed yet).

  2. Bulk INSERT StudyReview rows (ON CONFLICT DO NOTHING — idempotent).
  3. Upsert UserDailyStats.
  4. UPDATE StudySession: ended_at, status=COMPLETED, aggregate counters.
  5. COMMIT (all of the above in ONE transaction).
  6. DELETE Redis keys (AFTER the commit — never before).

Idempotency:
  The unique index on study_reviews(session_id, item_id) ensures duplicate
  finalisation calls (e.g. user + sweeper both trigger) are safe.

SM-2 note:
  UserProgress rows are updated here — not per-answer in submit_answer().
  This is the key difference from the old architecture. All SM-2 work is
  deferred until finalize, keeping the per-answer path Redis-only.
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import Float, cast, case, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import Item
from app.models.study_review import StudyReview
from app.models.study_session import StudySession
from app.models.user_daily_stats import UserDailyStats
from app.models.user_progress import UserProgress
from app.models.user_stats_total import UserStatsTotal
from app.models.enums import SessionStatus
from app.services.answer_evaluator import (
    DEFAULT_EXPECTED_MS,
    T_MAX_MS,
    map_quality,
)
from app.services.session_manager import RawAnswerEvent, SessionManager, SessionState
from app.services.sm2_engine import (
    SM2State,
    apply_absence_decay_for_days,
    initial_state,
    update as sm2_update,
)

logger = logging.getLogger(__name__)

# ============================================================================
# Constants
# ============================================================================

LEECH_FAILURE_RATE_THRESHOLD = 0.5
LEECH_MIN_REVIEWS = 5


# ============================================================================
# Public interface
# ============================================================================


class ProgressUpdater:
    """Handles batch SM-2 computation and DB writes for session finalisation."""

    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    async def finalise_batch(
        self,
        state: SessionState,
        raw_events: list[RawAnswerEvent],
        db_session: StudySession,
        session_mgr: SessionManager,
        final_status: SessionStatus = SessionStatus.COMPLETED,
    ) -> dict:
        """
        Process all buffered answers and persist to PostgreSQL.

        Steps (all within one transaction):
          1. SM-2 update + UserProgress flush for each event.
          2. Bulk INSERT StudyReview rows.
          3. Upsert UserDailyStats.
          4. UPDATE StudySession.
          5. COMMIT.
          6. DELETE Redis keys (post-commit).

        Returns a summary dict.
        """
        if not raw_events:
            logger.info(
                "finalise_skipped_no_answers",
                extra={"session_id": state.session_id},
            )
            await self._close_session(db_session, status=final_status)
            await self._db.commit()
            await session_mgr.delete_session(state.session_id)
            return _empty_summary(state.session_id)

        # Defensive overflow guard: truncate events that exceed the item list
        if len(raw_events) > len(state.item_order):
            logger.warning(
                "finalise_overflow_truncated",
                extra={
                    "session_id": state.session_id,
                    "events": len(raw_events),
                    "items": len(state.item_order),
                },
            )
            raw_events = raw_events[: len(state.item_order)]

        # ── 1. SM-2 updates (flush after each, commit at end) ─────────────────
        processed, new_words_count = await self._run_sm2_batch(
            state.user_id, raw_events, review_intensity=state.config.review_intensity
        )

        language_id = await self._resolve_language_id(raw_events) or 0

        # ── 2. Bulk insert StudyReview rows ───────────────────────────────────
        await self._insert_reviews(state, processed, language_id)

        # ── 3. Upsert UserDailyStats + UserStatsTotal ─────────────────────────
        await self._upsert_daily_stats(state, raw_events, language_id, new_words_count)

        # ── 4. Update StudySession ────────────────────────────────────────────
        correct = sum(1 for e in raw_events if e.is_correct)
        incorrect = len(raw_events) - correct
        total_ms = sum(min(e.response_time_ms, T_MAX_MS) for e in raw_events)

        db_session.ended_at = datetime.now(timezone.utc)
        db_session.status = final_status
        db_session.correct_count = correct
        db_session.incorrect_count = incorrect
        db_session.items_reviewed = len(raw_events)
        db_session.total_time_ms = total_ms
        await self._db.flush()

        # ── 5. Detect leeches ─────────────────────────────────────────────────
        leeches = await self._detect_leeches(state.user_id, raw_events)

        # ── 6. Commit ─────────────────────────────────────────────────────────
        await self._db.commit()

        # ── 7. Delete Redis keys (AFTER commit) ───────────────────────────────
        await session_mgr.delete_session(state.session_id)

        logger.info(
            "session_finalised",
            extra={
                "session_id": state.session_id,
                "user_id": state.user_id,
                "reviews": len(raw_events),
                "leeches": len(leeches),
            },
        )

        return _build_summary(state.session_id, raw_events, leeches)

    # ── Private helpers ──────────────────────────────────────────────────────

    async def _run_sm2_batch(
        self,
        user_id: int,
        raw_events: list[RawAnswerEvent],
        *,
        review_intensity: float = 1.0,
    ) -> tuple[list[dict], int]:
        """
        Run SM-2 for each event.

        Returns (processed_events, new_words_count) where new_words_count is
        the number of items seen for the first time in this session.
        """
        item_ids = [e.item_id for e in raw_events]
        expected_times = await self._bulk_expected_times(user_id, item_ids)
        progress_map = await self._bulk_lock_progress(user_id, item_ids)

        processed: list[dict] = []
        new_words_count = 0

        for event in raw_events:
            progress = progress_map[event.item_id]

            # Count items being reviewed for the first time
            if progress.last_reviewed is None:
                new_words_count += 1

            ease_before = progress.ease_factor
            interval_before = progress.interval

            expected_ms = expected_times.get(event.item_id, DEFAULT_EXPECTED_MS)
            capped_ms = min(event.response_time_ms, T_MAX_MS)
            time_ratio = capped_ms / expected_ms if expected_ms > 0 else 1.0
            quality = map_quality(
                event.is_correct, time_ratio, event.confidence_override
            )

            sm2_state = SM2State(
                interval_days=progress.interval,
                ease_factor=Decimal(str(progress.ease_factor)),
                repetitions=progress.repetitions,
                lapsed_attempts=progress.lapsed_attempts,
            )

            # Apply long-absence EF decay before scheduling
            if progress.last_reviewed is not None:
                days_since = (datetime.now(timezone.utc) - progress.last_reviewed).days
                if days_since > 60:
                    sm2_state = SM2State(
                        interval_days=sm2_state.interval_days,
                        ease_factor=apply_absence_decay_for_days(
                            sm2_state.ease_factor, days_since
                        ),
                        repetitions=sm2_state.repetitions,
                        lapsed_attempts=sm2_state.lapsed_attempts,
                    )

            sm2_result = sm2_update(
                sm2_state,
                quality,
                review_intensity=review_intensity,
            )

            progress.ease_factor = float(sm2_result.new_state.ease_factor)
            progress.interval = sm2_result.new_state.interval_days
            progress.repetitions = sm2_result.new_state.repetitions
            progress.lapsed_attempts = sm2_result.new_state.lapsed_attempts
            progress.last_reviewed = datetime.now(timezone.utc)
            progress.next_review = sm2_result.next_review_at
            await self._db.flush()

            processed.append(
                {
                    "item_id": event.item_id,
                    "translation_id": event.translation_id,
                    "user_answer": event.user_answer,
                    "response_time_ms": event.response_time_ms,
                    "capped_response_ms": capped_ms,
                    "was_correct": event.is_correct,
                    "similarity": event.similarity,
                    "quality": quality,
                    "ease_before": ease_before,
                    "ease_after": float(sm2_result.new_state.ease_factor),
                    "interval_before": interval_before,
                    "interval_after": sm2_result.new_state.interval_days,
                    "reviewed_at": datetime.fromisoformat(event.answered_at),
                }
            )

        return processed, new_words_count

    async def _bulk_expected_times(
        self, user_id: int, item_ids: list[int]
    ) -> dict[int, int]:
        """
        Pre-compute expected response times for all items in at most 4 queries.

        Hierarchy (first match wins per item):
          1. User × item average response time
          2. User × part-of-speech average response time
          3. Global item average response time
          4. DEFAULT_EXPECTED_MS
        """
        if not item_ids:
            return {}

        # Level 1: user-item averages
        l1_rows = (
            await self._db.execute(
                select(StudyReview.item_id, func.avg(StudyReview.response_time))
                .where(
                    StudyReview.user_id == user_id,
                    StudyReview.item_id.in_(item_ids),
                )
                .group_by(StudyReview.item_id)
            )
        ).fetchall()
        user_item: dict[int, int] = {r[0]: int(r[1]) for r in l1_rows}

        missing: list[int] = [iid for iid in item_ids if iid not in user_item]
        if not missing:
            return {iid: user_item[iid] for iid in item_ids}

        # Level 2: user × POS averages
        pos_rows = (
            await self._db.execute(
                select(Item.id, Item.part_of_speech).where(Item.id.in_(missing))
            )
        ).fetchall()
        item_to_pos: dict[int, Any] = {r[0]: r[1] for r in pos_rows}
        pos_set = {p for p in item_to_pos.values() if p is not None}

        user_pos: dict[Any, int] = {}
        if pos_set:
            pos_avg_rows = (
                await self._db.execute(
                    select(Item.part_of_speech, func.avg(StudyReview.response_time))
                    .join(Item, Item.id == StudyReview.item_id)
                    .where(
                        StudyReview.user_id == user_id,
                        Item.part_of_speech.in_(pos_set),
                    )
                    .group_by(Item.part_of_speech)
                )
            ).fetchall()
            user_pos = {r[0]: int(r[1]) for r in pos_avg_rows}

        pos_resolved: dict[int, int] = {}
        still_missing: list[int] = []
        for iid in missing:
            pos = item_to_pos.get(iid)
            if pos is not None and pos in user_pos:
                pos_resolved[iid] = user_pos[pos]
            else:
                still_missing.append(iid)

        # Level 3: global item averages
        global_avgs: dict[int, int] = {}
        if still_missing:
            g_rows = (
                await self._db.execute(
                    select(StudyReview.item_id, func.avg(StudyReview.response_time))
                    .where(StudyReview.item_id.in_(still_missing))
                    .group_by(StudyReview.item_id)
                )
            ).fetchall()
            global_avgs = {r[0]: int(r[1]) for r in g_rows}

        # Level 4: default for anything still unresolved
        result: dict[int, int] = {}
        for iid in item_ids:
            if iid in user_item:
                result[iid] = user_item[iid]
            elif iid in pos_resolved:
                result[iid] = pos_resolved[iid]
            elif iid in global_avgs:
                result[iid] = global_avgs[iid]
            else:
                result[iid] = DEFAULT_EXPECTED_MS
        return result

    async def _bulk_lock_progress(
        self, user_id: int, item_ids: list[int]
    ) -> dict[int, UserProgress]:
        """
        Single SELECT … FOR UPDATE for all items, then bulk-create missing rows.

        Returns a dict mapping item_id → locked UserProgress row.
        """
        if not item_ids:
            return {}

        rows = (
            (
                await self._db.execute(
                    select(UserProgress)
                    .where(
                        UserProgress.user_id == user_id,
                        UserProgress.item_id.in_(item_ids),
                    )
                    .with_for_update()
                )
            )
            .scalars()
            .all()
        )

        existing: dict[int, UserProgress] = {r.item_id: r for r in rows}
        missing = [iid for iid in item_ids if iid not in existing]

        if missing:
            init = initial_state()
            now = datetime.now(timezone.utc)
            new_rows = [
                UserProgress(
                    user_id=user_id,
                    item_id=iid,
                    ease_factor=float(init.ease_factor),
                    interval=init.interval_days,
                    repetitions=init.repetitions,
                    lapsed_attempts=init.lapsed_attempts,
                    last_reviewed=None,
                    next_review=now,
                )
                for iid in missing
            ]
            for row in new_rows:
                self._db.add(row)
            await self._db.flush()
            for row in new_rows:
                existing[row.item_id] = row

        return existing

    async def _insert_reviews(
        self, state: SessionState, processed: list[dict], language_id: int
    ) -> int:
        """Single bulk INSERT for all reviews — ON CONFLICT DO NOTHING is idempotent."""
        if not processed:
            return 0

        stmt = (
            pg_insert(StudyReview)
            .values(
                [
                    {
                        "user_id": state.user_id,
                        "item_id": p["item_id"],
                        "language_id": language_id,
                        "translation_id": p["translation_id"],
                        "set_id": state.set_id,
                        "session_id": state.session_id,
                        "was_correct": p["was_correct"],
                        "user_answer": p["user_answer"],
                        "response_time": p["response_time_ms"],
                        "ease_before": p["ease_before"],
                        "interval_before": p["interval_before"],
                        "ease_after": p["ease_after"],
                        "interval_after": p["interval_after"],
                        "reviewed_at": p["reviewed_at"],
                    }
                    for p in processed
                ]
            )
            .on_conflict_do_nothing(index_elements=["session_id", "item_id"])
        )
        result = await self._db.execute(stmt)
        return result.rowcount

    async def _upsert_daily_stats(
        self,
        state: SessionState,
        raw_events: list[RawAnswerEvent],
        language_id: int,
        new_words_count: int = 0,
    ) -> None:
        if not language_id:
            return

        today = datetime.now(timezone.utc).date()
        correct = sum(1 for e in raw_events if e.is_correct)
        incorrect = len(raw_events) - correct
        total_seconds = Decimal(
            sum(min(e.response_time_ms, T_MAX_MS) for e in raw_events)
        ) / Decimal(1000)

        await self._db.execute(
            pg_insert(UserDailyStats)
            .values(
                user_id=state.user_id,
                language_id=language_id,
                stat_date=today,
                correct_count=correct,
                incorrect_count=incorrect,
                new_words_count=new_words_count,
                seconds_spent=total_seconds,
            )
            .on_conflict_do_update(
                index_elements=["user_id", "language_id", "stat_date"],
                set_={
                    "correct_count": UserDailyStats.correct_count + correct,
                    "incorrect_count": UserDailyStats.incorrect_count + incorrect,
                    "new_words_count": UserDailyStats.new_words_count + new_words_count,
                    "seconds_spent": UserDailyStats.seconds_spent + total_seconds,
                },
            )
        )

        await self._db.execute(
            pg_insert(UserStatsTotal)
            .values(
                user_id=state.user_id,
                language_id=language_id,
                total_seconds=total_seconds,
                total_words=new_words_count,
            )
            .on_conflict_do_update(
                index_elements=["user_id", "language_id"],
                set_={
                    "total_seconds": UserStatsTotal.total_seconds + total_seconds,
                    "total_words": UserStatsTotal.total_words + new_words_count,
                },
            )
        )

    async def _close_session(
        self, db_session: StudySession, *, status: SessionStatus
    ) -> None:
        if db_session.ended_at is None:
            db_session.ended_at = datetime.now(timezone.utc)
        db_session.status = status
        await self._db.flush()

    async def _detect_leeches(
        self, user_id: int, raw_events: list[RawAnswerEvent]
    ) -> list[int]:
        failed_ids = list({e.item_id for e in raw_events if not e.is_correct})
        if not failed_ids:
            return []

        # CTE 1: rank the last 10 reviews per item by recency
        rn_col = (
            func.row_number()
            .over(
                partition_by=StudyReview.item_id,
                order_by=StudyReview.reviewed_at.desc(),
            )
            .label("rn")
        )
        ranked_cte = (
            select(StudyReview.item_id, StudyReview.was_correct, rn_col)
            .where(
                StudyReview.user_id == user_id,
                StudyReview.item_id.in_(failed_ids),
            )
            .cte("ranked")
        )

        # CTE 2: aggregate counts within the top-10 window
        counts_cte = (
            select(
                ranked_cte.c.item_id,
                func.count().label("total"),
                # COUNT(CASE WHEN NOT was_correct THEN 1 END) counts only failures
                func.count(
                    case((ranked_cte.c.was_correct == False, 1))  # noqa: E712
                ).label("incorrect"),
            )
            .where(ranked_cte.c.rn <= 10)
            .group_by(ranked_cte.c.item_id)
            .cte("counts")
        )

        stmt = select(counts_cte.c.item_id).where(
            counts_cte.c.total >= LEECH_MIN_REVIEWS,
            cast(counts_cte.c.incorrect, Float) / cast(counts_cte.c.total, Float)
            >= LEECH_FAILURE_RATE_THRESHOLD,
        )

        leech_ids = list((await self._db.execute(stmt)).scalars().all())
        for item_id in leech_ids:
            logger.warning(
                "leech_detected", extra={"user_id": user_id, "item_id": item_id}
            )
        return leech_ids

    async def _resolve_language_id(
        self, raw_events: list[RawAnswerEvent]
    ) -> int | None:
        if not raw_events:
            return None
        item = await self._db.get(Item, raw_events[0].item_id)
        return item.language_id if item else None


# ============================================================================
# Pure helpers
# ============================================================================


def _empty_summary(session_id: int) -> dict:
    return {
        "session_id": session_id,
        "total_reviewed": 0,
        "correct_count": 0,
        "accuracy": 0.0,
        "avg_response_ms": 0,
        "leech_item_ids": [],
    }


def _build_summary(
    session_id: int,
    raw_events: list[RawAnswerEvent],
    leeches: list[int],
) -> dict:
    total = len(raw_events)
    correct = sum(1 for e in raw_events if e.is_correct)
    avg_ms = sum(e.response_time_ms for e in raw_events) // total if total else 0
    return {
        "session_id": session_id,
        "total_reviewed": total,
        "correct_count": correct,
        "accuracy": round(correct / total, 4) if total else 0.0,
        "avg_response_ms": avg_ms,
        "leech_item_ids": leeches,
    }


__all__ = ["ProgressUpdater", "LEECH_FAILURE_RATE_THRESHOLD", "LEECH_MIN_REVIEWS"]
