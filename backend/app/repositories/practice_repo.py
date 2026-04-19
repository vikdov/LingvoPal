"""Practice repository — all ORM queries for the practice session flow."""

import logging
from datetime import datetime, timezone

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.enums import SessionStatus
from app.models.item import Item
from app.models.item_synonym import ItemSynonym
from app.models.pending_session import PendingSession
from app.models.set import Set
from app.models.set_item import SetItem
from app.models.study_review import StudyReview
from app.models.study_session import StudySession
from app.models.translation import Translation
from app.models.user import UserSettings
from app.models.user_progress import UserProgress
from app.models.user_set_library import UserSetLibrary

logger = logging.getLogger(__name__)


class PracticeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Set access ────────────────────────────────────────────────────────────

    async def get_set(self, set_id: int) -> Set | None:
        return await self._db.scalar(
            select(Set).where(Set.id == set_id, Set.deleted_at.is_(None))
        )

    async def check_library_access(self, user_id: int, set_id: int) -> bool:
        return (
            await self._db.scalar(
                select(UserSetLibrary).where(
                    UserSetLibrary.user_id == user_id,
                    UserSetLibrary.set_id == set_id,
                )
            )
        ) is not None

    async def get_user_settings(self, user_id: int) -> UserSettings | None:
        return await self._db.scalar(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )

    # ── Item selection ────────────────────────────────────────────────────────

    async def select_due_item_ids(
        self,
        user_id: int,
        set_id: int,
        limit: int,
        exclude_ids: set[int] | None = None,
    ) -> list[int]:
        now = datetime.now(timezone.utc)
        stmt = (
            select(UserProgress.item_id)
            .join(SetItem, SetItem.item_id == UserProgress.item_id)
            .join(Item, Item.id == UserProgress.item_id)
            .where(
                UserProgress.user_id == user_id,
                SetItem.set_id == set_id,
                UserProgress.next_review <= now,
                Item.deleted_at.is_(None),
            )
            .order_by(UserProgress.next_review.asc())
            .limit(limit)
        )
        if exclude_ids:
            stmt = stmt.where(UserProgress.item_id.notin_(exclude_ids))
        return [row[0] for row in (await self._db.execute(stmt)).fetchall()]

    async def select_new_item_ids(
        self,
        user_id: int,
        set_id: int,
        limit: int,
        exclude_ids: set[int] | None = None,
    ) -> list[int]:
        if limit <= 0:
            return []
        stmt = (
            select(Item.id)
            .join(SetItem, SetItem.item_id == Item.id)
            .outerjoin(
                UserProgress,
                and_(
                    UserProgress.item_id == Item.id,
                    UserProgress.user_id == user_id,
                ),
            )
            .where(
                SetItem.set_id == set_id,
                Item.deleted_at.is_(None),
                UserProgress.item_id.is_(None),  # hash anti-join: never seen
            )
            .order_by(Item.id.asc())
            .limit(limit)
        )
        if exclude_ids:
            stmt = stmt.where(Item.id.notin_(exclude_ids))
        return [row[0] for row in (await self._db.execute(stmt)).fetchall()]

    async def seed_progress_bulk(
        self,
        user_id: int,
        item_ids: list[int],
        *,
        ease_factor: float,
        interval: int,
        repetitions: int,
        lapsed_attempts: int,
    ) -> None:
        now = datetime.now(timezone.utc)
        stmt = (
            pg_insert(UserProgress)
            .values([
                {
                    "user_id": user_id,
                    "item_id": item_id,
                    "ease_factor": ease_factor,
                    "interval": interval,
                    "repetitions": repetitions,
                    "lapsed_attempts": lapsed_attempts,
                    "last_reviewed": None,
                    "next_review": now,
                }
                for item_id in item_ids
            ])
            .on_conflict_do_nothing(index_elements=["user_id", "item_id"])
        )
        await self._db.execute(stmt)
        await self._db.flush()

    # ── Item hints (single batch query + synonym enrichment) ─────────────────

    async def fetch_item_hints(
        self,
        item_ids: list[int],
        set_id: int,
        target_lang_id: int,
        user_id: int,
    ) -> dict[str, dict]:
        """
        Single JOIN query for all per-card data, then one synonym query.

        Returns dict[str(item_id), hint_dict] where hint_dict contains
        everything ItemHintSchema needs.
        """
        if not item_ids:
            return {}

        PinnedT = aliased(Translation, name="pinned_t")
        LangT = aliased(Translation, name="lang_t")

        stmt = (
            select(
                Item.id.label("item_id"),
                Item.term.label("answer"),
                Item.context.label("context"),
                Item.image_url.label("image_url"),
                Item.audio_url.label("audio_url"),
                Item.part_of_speech.label("part_of_speech"),
                func.coalesce(PinnedT.id, LangT.id).label("resolved_trans_id"),
                func.coalesce(PinnedT.term_trans, LangT.term_trans).label("prompt"),
                func.coalesce(
                    PinnedT.context_trans, LangT.context_trans
                ).label("context_trans"),
                UserProgress.last_reviewed.label("last_reviewed"),
            )
            .select_from(Item)
            .join(SetItem, and_(SetItem.item_id == Item.id, SetItem.set_id == set_id))
            .outerjoin(
                PinnedT,
                and_(
                    SetItem.translation_id.is_not(None),
                    PinnedT.id == SetItem.translation_id,
                ),
            )
            .outerjoin(
                LangT,
                and_(
                    SetItem.translation_id.is_(None),
                    LangT.item_id == Item.id,
                    LangT.language_id == target_lang_id,
                    LangT.deleted_at.is_(None),
                ),
            )
            .outerjoin(
                UserProgress,
                and_(
                    UserProgress.item_id == Item.id,
                    UserProgress.user_id == user_id,
                ),
            )
            .where(Item.id.in_(item_ids))
        )

        rows = (await self._db.execute(stmt)).fetchall()
        synonyms = await self._fetch_synonyms(item_ids)

        hints: dict[str, dict] = {}
        for row in rows:
            prompt = row.prompt if row.prompt is not None else row.answer
            pos = row.part_of_speech.value if row.part_of_speech is not None else None
            hints[str(row.item_id)] = {
                "prompt": prompt,
                "answer": row.answer,
                "context": row.context,
                "context_trans": row.context_trans,
                "image_url": row.image_url,
                "audio_url": row.audio_url,
                "part_of_speech": pos,
                "translation_id": row.resolved_trans_id,
                "last_reviewed": (
                    row.last_reviewed.isoformat() if row.last_reviewed else None
                ),
                "synonyms": synonyms.get(row.item_id, []),
            }

        return hints

    async def _fetch_synonyms(self, item_ids: list[int]) -> dict[int, list[str]]:
        """
        item_synonyms is a pair table with item_a_id < item_b_id.
        For each item in item_ids, collect the terms of its synonym partners.
        """
        if not item_ids:
            return {}

        ItemA = aliased(Item, name="item_a")
        ItemB = aliased(Item, name="item_b")

        stmt = (
            select(
                ItemSynonym.item_a_id,
                ItemSynonym.item_b_id,
                ItemA.term.label("term_a"),
                ItemB.term.label("term_b"),
            )
            .join(ItemA, ItemA.id == ItemSynonym.item_a_id)
            .join(ItemB, ItemB.id == ItemSynonym.item_b_id)
            .where(
                ItemSynonym.deleted_at.is_(None),
                or_(
                    ItemSynonym.item_a_id.in_(item_ids),
                    ItemSynonym.item_b_id.in_(item_ids),
                ),
            )
        )

        result: dict[int, list[str]] = {}
        for row in (await self._db.execute(stmt)).fetchall():
            if row.item_a_id in item_ids:
                result.setdefault(row.item_a_id, []).append(row.term_b)
            if row.item_b_id in item_ids:
                result.setdefault(row.item_b_id, []).append(row.term_a)
        return result

    # ── Session CRUD ──────────────────────────────────────────────────────────

    async def create_session(self, user_id: int, set_id: int) -> StudySession:
        db_session = StudySession(
            user_id=user_id,
            set_id=set_id,
            started_at=datetime.now(timezone.utc),
            status=SessionStatus.IN_PROGRESS,
            correct_count=0,
            incorrect_count=0,
            total_time_ms=0,
            items_reviewed=0,
        )
        self._db.add(db_session)
        await self._db.flush()  # assigns db_session.id; caller must commit
        return db_session

    async def get_session(self, session_id: int) -> StudySession | None:
        return await self._db.get(StudySession, session_id)

    async def get_active_db_session(self, user_id: int) -> StudySession | None:
        return await self._db.scalar(
            select(StudySession)
            .where(
                StudySession.user_id == user_id,
                StudySession.status == SessionStatus.IN_PROGRESS,
            )
            .order_by(StudySession.started_at.desc())
            .limit(1)
        )

    async def get_all_in_progress_sessions(self) -> list[StudySession]:
        result = await self._db.execute(
            select(StudySession).where(
                StudySession.status == SessionStatus.IN_PROGRESS
            )
        )
        return list(result.scalars().all())

    # ── Session reconstruction helpers ────────────────────────────────────────

    async def get_answered_ids_from_pending(self, session_id: int) -> list[int]:
        pending = await self._db.scalar(
            select(PendingSession).where(
                PendingSession.session_id == session_id,
                PendingSession.recovered == False,  # noqa: E712
            )
        )
        if pending is None:
            return []
        try:
            raw_list = pending.raw_events_json
            return [e["item_id"] for e in raw_list]
        except Exception:
            return []

    async def get_answered_ids_from_reviews(self, session_id: int) -> list[int]:
        result = await self._db.execute(
            select(StudyReview.item_id)
            .where(StudyReview.session_id == session_id)
            .order_by(StudyReview.reviewed_at.asc())
        )
        return [row[0] for row in result.fetchall()]

    # ── Pending session safety valve ──────────────────────────────────────────

    async def save_pending_session(
        self,
        session_id: int,
        user_id: int,
        raw_events_json: list,
        session_state_json: dict,
    ) -> None:
        now = datetime.now(timezone.utc)
        stmt = (
            pg_insert(PendingSession)
            .values(
                session_id=session_id,
                user_id=user_id,
                raw_events_json=raw_events_json,
                session_state_json=session_state_json,
                saved_at=now,
                recovered=False,
            )
            .on_conflict_do_update(
                index_elements=["session_id"],
                set_={
                    "raw_events_json": raw_events_json,
                    "session_state_json": session_state_json,
                    "saved_at": now,
                },
            )
        )
        await self._db.execute(stmt)
        await self._db.flush()

    async def get_pending_session(self, session_id: int) -> PendingSession | None:
        return await self._db.scalar(
            select(PendingSession).where(
                PendingSession.session_id == session_id,
                PendingSession.recovered == False,  # noqa: E712
            )
        )

    async def mark_pending_session_recovered(self, session_id: int) -> None:
        await self._db.execute(
            update(PendingSession)
            .where(PendingSession.session_id == session_id)
            .values(recovered=True)
        )

    async def get_session_reviews_summary(self, session_id: int) -> dict:
        row = (await self._db.execute(
            select(
                func.count().label("total"),
                func.count().filter(StudyReview.was_correct.is_(True)).label("correct"),
                func.avg(StudyReview.response_time).label("avg_ms"),
            )
            .where(StudyReview.session_id == session_id)
        )).one()
        total = row.total or 0
        correct = row.correct or 0
        avg_ms = int(row.avg_ms) if row.avg_ms else 0
        return {
            "total_reviewed": total,
            "correct_count": correct,
            "accuracy": round(correct / total, 4) if total else 0.0,
            "avg_response_ms": avg_ms,
        }


__all__ = ["PracticeRepository"]
