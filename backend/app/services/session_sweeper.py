"""
Session Sweeper — background safety net for buffered practice sessions.

Runs two jobs:

1. Periodic sweep (every SWEEP_INTERVAL_SECONDS):
   - Finds all IN_PROGRESS sessions in DB.
   - For each, checks Redis TTL.
   - If TTL < FLUSH_THRESHOLD_SECONDS, triggers finalise (saves partial progress).

2. Shutdown flush (called from lifespan on app shutdown):
   - Flushes every remaining IN_PROGRESS session (best-effort).
   - Runs before the DB/Redis connections are closed.

Idempotency:
   flush_lock (Redis SET NX) prevents the sweeper and a concurrent user
   finalize call from processing the same session twice.
   ON CONFLICT DO NOTHING on study_reviews handles any duplicate rows.
"""

import asyncio
import logging
from datetime import datetime, timezone

import redis.asyncio as aioredis

from app.models.enums import SessionStatus
from app.repositories.practice_repo import PracticeRepository
from app.services.progress_updater import ProgressUpdater
from app.services.session_manager import (
    BatchConfig,
    INTENSITY_MAP,
    RawAnswerEvent,
    SessionManager,
    SessionState,
    TTL_SECONDS,
    make_session_state,
)

logger = logging.getLogger(__name__)

SWEEP_INTERVAL_SECONDS = 300        # run every 5 minutes
FLUSH_THRESHOLD_SECONDS = 3600      # flush if < 1 hour of TTL remains (~23 h old)
INACTIVITY_TIMEOUT_SECONDS = 1800   # flush after 30 minutes of no answers


def _build_sweeper_config(settings, target_lang_id: int) -> BatchConfig:
    """Build BatchConfig from UserSettings, falling back to defaults."""
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


class SessionSweeper:
    def __init__(self, db_factory, redis: aioredis.Redis) -> None:
        """
        db_factory — zero-arg async callable that yields an AsyncSession.
        Matches the signature of app.database.session.get_session.
        """
        self._db_factory = db_factory
        self._redis = redis
        self._task: asyncio.Task | None = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        self._task = asyncio.create_task(self._loop(), name="session_sweeper")
        logger.info("session_sweeper_started")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("session_sweeper_stopped")

    # ── Shutdown flush (called synchronously from lifespan) ───────────────────

    async def flush_all_active(self) -> None:
        """Best-effort: flush every IN_PROGRESS session before shutdown."""
        logger.info("sweeper_shutdown_flush_starting")
        async with self._db_factory() as db:
            sessions = await PracticeRepository(db).get_all_in_progress_sessions()

        flushed = 0
        for db_session in sessions:
            try:
                await self._flush_one(db_session.id, db_session.user_id)
                flushed += 1
            except Exception as exc:
                logger.warning(
                    "sweeper_shutdown_flush_failed",
                    extra={"session_id": db_session.id, "error": str(exc)},
                )
        logger.info("sweeper_shutdown_flush_done", extra={"flushed": flushed})

    # ── Background loop ───────────────────────────────────────────────────────

    async def _loop(self) -> None:
        while True:
            try:
                await asyncio.sleep(SWEEP_INTERVAL_SECONDS)
                await self._sweep()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("sweeper_loop_error", extra={"error": str(exc)})

    async def _sweep(self) -> None:
        mgr = SessionManager(self._redis)
        async with self._db_factory() as db:
            sessions = await PracticeRepository(db).get_all_in_progress_sessions()

        to_flush: list[tuple[int, int]] = []
        for db_session in sessions:
            ttl = await mgr.session_ttl_seconds(db_session.id)
            should_flush = ttl < 0 or ttl < FLUSH_THRESHOLD_SECONDS
            if not should_flush:
                should_flush = await self._is_inactive(mgr, db_session.id)
            if should_flush:
                to_flush.append((db_session.id, db_session.user_id))

        flushed = 0
        for session_id, user_id in to_flush:
            try:
                await self._flush_one(session_id, user_id)
                flushed += 1
            except Exception as exc:
                logger.warning(
                    "sweeper_flush_failed",
                    extra={"session_id": session_id, "error": str(exc)},
                )

        if flushed:
            logger.info("sweeper_sweep_done", extra={"flushed": flushed})

    async def _is_inactive(self, mgr: SessionManager, session_id: int) -> bool:
        """Return True if the session has had no answers for INACTIVITY_TIMEOUT_SECONDS."""
        state = await mgr.load_session(session_id)
        if state is None or state.last_answered_at is None:
            return False
        try:
            last = datetime.fromisoformat(state.last_answered_at)
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            idle = (datetime.now(timezone.utc) - last).total_seconds()
            return idle > INACTIVITY_TIMEOUT_SECONDS
        except (ValueError, TypeError):
            return False

    async def _flush_one(self, session_id: int, user_id: int) -> None:
        mgr = SessionManager(self._redis)

        if not await mgr.acquire_flush_lock(session_id):
            logger.debug(
                "sweeper_lock_contention", extra={"session_id": session_id}
            )
            return

        try:
            async with self._db_factory() as db:
                await self._flush_one_with_db(db, mgr, session_id, user_id)
        finally:
            await mgr.release_flush_lock(session_id)

    async def _flush_one_with_db(self, db, mgr: SessionManager, session_id: int, user_id: int) -> None:
        repo = PracticeRepository(db)
        db_session = await repo.get_session(session_id)
        if db_session is None or db_session.ended_at is not None:
            return

        state = await mgr.load_session(session_id)
        raw_events = await mgr.get_raw_answers(session_id)

        if state is not None and raw_events:
            # Redis is live — checkpoint to pending_sessions before finalising
            # so the events survive a crash between here and the finalize commit.
            await repo.save_pending_session(
                session_id=session_id,
                user_id=user_id,
                raw_events_json=[e.to_dict() for e in raw_events],
                session_state_json=state.to_dict(),
            )
            await db.commit()
            # Re-fetch db_session: SQLAlchemy expires ORM objects on commit
            db_session = await repo.get_session(session_id)
            if db_session is None or db_session.ended_at is not None:
                return

        elif state is None:
            # Redis expired — recover from pending_sessions if available
            pending = await repo.get_pending_session(session_id)
            if pending is not None:
                try:
                    state = SessionState.from_dict(pending.session_state_json)
                    raw_events = [
                        RawAnswerEvent.from_dict(e)
                        for e in pending.raw_events_json
                    ]
                except Exception:
                    logger.warning(
                        "sweeper_pending_corrupt",
                        extra={"session_id": session_id},
                    )
                    state = None
                    raw_events = []

            if state is None:
                # Last resort: rebuild minimal state from DB review log
                answered_ids = await repo.get_answered_ids_from_reviews(session_id)
                settings = await repo.get_user_settings(user_id)
                db_set = await repo.get_set(db_session.set_id)
                target_lang_id = db_set.target_lang_id if db_set else 0
                config = _build_sweeper_config(settings, target_lang_id)
                item_hints = await repo.fetch_item_hints(
                    answered_ids, db_session.set_id, target_lang_id, user_id
                )
                state = make_session_state(
                    session_id=session_id,
                    user_id=user_id,
                    set_id=db_session.set_id,
                    item_order=answered_ids,
                    config=config,
                    item_hints=item_hints,
                )
                raw_events = []

        updater = ProgressUpdater(db)
        await updater.finalise_batch(
            state=state,
            raw_events=raw_events,
            db_session=db_session,
            session_mgr=mgr,
            final_status=SessionStatus.COMPLETED,
        )
        # finalise_batch committed; mark pending record recovered.
        # get_session() auto-commits on clean exit, persisting this UPDATE.
        await repo.mark_pending_session_recovered(session_id)
        await mgr.clear_active(user_id)
        logger.info("sweeper_flushed", extra={"session_id": session_id})


__all__ = ["SessionSweeper", "SWEEP_INTERVAL_SECONDS", "FLUSH_THRESHOLD_SECONDS", "INACTIVITY_TIMEOUT_SECONDS"]
