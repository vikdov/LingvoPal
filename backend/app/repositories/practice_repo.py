"""Practice repository — all ORM queries for the practice session flow."""

import logging
import re
from datetime import datetime, timezone

from sqlalchemy import and_, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.enums import SessionStatus
from app.models.item import Item
from app.models.item_synonym_term import ItemSynonymTerm
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


def _split_cloze(context: str | None, term: str) -> tuple[str | None, str | None, str | None]:
    """
    Split context into (prefix, surface_word, suffix) for cloze display.

    Prefers explicit {{surface_form}} annotation; falls back to word-boundary
    search for term. Returns (None, None, None) when no match found.

    Returns strings, not integer offsets, to avoid Python code-point vs JS UTF-16
    index mismatch for non-ASCII content.
    """
    if not context or not term:
        return None, None, None
    marker = re.search(r"\{\{(.+?)\}\}", context)
    if marker:
        s, e = marker.start(), marker.end()
        return context[:s], marker.group(1), context[e:]
    match = re.search(r"\b" + re.escape(term) + r"\b", context, re.IGNORECASE)
    if not match:
        return None, None, None
    s, e = match.start(), match.end()
    return context[:s], context[s:e], context[e:]


class PracticeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Set access ────────────────────────────────────────────────────────────

    async def get_set(self, set_id: int) -> Set | None:
        return await self._db.scalar(select(Set).where(Set.id == set_id, Set.deleted_at.is_(None)))

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
        return await self._db.scalar(select(UserSettings).where(UserSettings.user_id == user_id))

    # ── Item selection ────────────────────────────────────────────────────────

    async def select_due_item_ids(
        self,
        user_id: int,
        set_id: int | None,
        limit: int,
        exclude_ids: set[int] | None = None,
        source_lang_id: int | None = None,
        force: bool = False,
    ) -> list[int]:
        now = datetime.now(timezone.utc)

        if set_id is not None:
            where = [
                UserProgress.user_id == user_id,
                SetItem.set_id == set_id,
                Item.deleted_at.is_(None),
            ]
            if not force:
                where.append(UserProgress.next_review <= now)
            stmt = (
                select(UserProgress.item_id)
                .join(SetItem, SetItem.item_id == UserProgress.item_id)
                .join(Item, Item.id == UserProgress.item_id)
                .where(*where)
                .order_by(UserProgress.next_review.asc())
                .limit(limit)
            )
        else:
            # "practice all": items from all library sets for source_lang_id
            eligible = (
                select(SetItem.item_id)
                .join(Set, Set.id == SetItem.set_id)
                .join(
                    UserSetLibrary,
                    and_(
                        UserSetLibrary.set_id == Set.id,
                        UserSetLibrary.user_id == user_id,
                    ),
                )
                .where(Set.source_lang_id == source_lang_id)
                .distinct()
                .scalar_subquery()
            )
            where_all = [
                UserProgress.user_id == user_id,
                Item.deleted_at.is_(None),
                UserProgress.item_id.in_(eligible),
            ]
            if not force:
                where_all.append(UserProgress.next_review <= now)
            stmt = (
                select(UserProgress.item_id)
                .join(Item, Item.id == UserProgress.item_id)
                .where(*where_all)
                .order_by(UserProgress.next_review.asc())
                .limit(limit)
            )

        if exclude_ids:
            stmt = stmt.where(UserProgress.item_id.notin_(exclude_ids))
        return [row[0] for row in (await self._db.execute(stmt)).fetchall()]

    async def count_due_items_by_set(self, user_id: int, set_ids: list[int]) -> dict[int, int]:
        """Return {set_id: due_count} for items currently due for review."""
        if not set_ids:
            return {}
        now = datetime.now(timezone.utc)
        result = await self._db.execute(
            select(SetItem.set_id, func.count(UserProgress.item_id).label("due_count"))
            .join(UserProgress, UserProgress.item_id == SetItem.item_id)
            .join(Item, Item.id == SetItem.item_id)
            .where(
                UserProgress.user_id == user_id,
                SetItem.set_id.in_(set_ids),
                Item.deleted_at.is_(None),
                UserProgress.next_review <= now,
            )
            .group_by(SetItem.set_id)
        )
        counts = {row.set_id: row.due_count for row in result.fetchall()}
        return {sid: counts.get(sid, 0) for sid in set_ids}

    async def get_next_review_at(self, user_id: int, set_id: int) -> datetime | None:
        stmt = (
            select(func.min(UserProgress.next_review))
            .join(SetItem, SetItem.item_id == UserProgress.item_id)
            .where(
                UserProgress.user_id == user_id,
                SetItem.set_id == set_id,
            )
        )
        return (await self._db.execute(stmt)).scalar_one_or_none()

    async def select_new_item_ids(
        self,
        user_id: int,
        set_id: int | None,
        limit: int,
        exclude_ids: set[int] | None = None,
        source_lang_id: int | None = None,
    ) -> list[int]:
        if limit <= 0:
            return []

        if set_id is not None:
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
                    UserProgress.item_id.is_(None),  # anti-join: never seen
                )
                .order_by(Item.id.asc())
                .limit(limit)
            )
        else:
            # "practice all": new items across all library sets for source_lang_id
            eligible = (
                select(SetItem.item_id)
                .join(Set, Set.id == SetItem.set_id)
                .join(
                    UserSetLibrary,
                    and_(
                        UserSetLibrary.set_id == Set.id,
                        UserSetLibrary.user_id == user_id,
                    ),
                )
                .where(Set.source_lang_id == source_lang_id)
                .distinct()
                .scalar_subquery()
            )
            stmt = (
                select(Item.id)
                .outerjoin(
                    UserProgress,
                    and_(
                        UserProgress.item_id == Item.id,
                        UserProgress.user_id == user_id,
                    ),
                )
                .where(
                    Item.deleted_at.is_(None),
                    UserProgress.item_id.is_(None),
                    Item.id.in_(eligible),
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
            .values(
                [
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
                ]
            )
            .on_conflict_do_nothing(index_elements=["user_id", "item_id"])
        )
        await self._db.execute(stmt)
        await self._db.flush()

    # ── Item hints (single batch query + synonym enrichment) ─────────────────

    async def fetch_item_hints(
        self,
        item_ids: list[int],
        set_id: int | None,
        target_lang_id: int,
        user_id: int,
    ) -> dict[str, dict]:
        """
        Single JOIN query for all per-card data, then one synonym query.

        When set_id is None ("practice all"), skips SetItem join and pinned
        translation — falls back to language-based translation lookup only.

        Returns dict[str(item_id), hint_dict] where hint_dict contains
        everything ItemHintSchema needs.
        """
        if not item_ids:
            return {}

        LangT = aliased(Translation, name="lang_t")

        if set_id is not None:
            PinnedT = aliased(Translation, name="pinned_t")
            stmt = (
                select(
                    Item.id.label("item_id"),
                    Item.term.label("answer"),
                    Item.context.label("context"),
                    Item.image_url.label("image_url"),
                    Item.audio_url.label("audio_url"),
                    Item.context_audio_url.label("context_audio_url"),
                    Item.part_of_speech.label("part_of_speech"),
                    Item.creator_id.label("creator_id"),
                    Item.status.label("item_status"),
                    func.coalesce(PinnedT.id, LangT.id).label("resolved_trans_id"),
                    func.coalesce(PinnedT.term_trans, LangT.term_trans).label("prompt"),
                    func.coalesce(PinnedT.context_trans, LangT.context_trans).label(
                        "context_trans"
                    ),
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
        else:
            # "practice all": no set context, language-based translation only
            stmt = (
                select(
                    Item.id.label("item_id"),
                    Item.term.label("answer"),
                    Item.context.label("context"),
                    Item.image_url.label("image_url"),
                    Item.audio_url.label("audio_url"),
                    Item.context_audio_url.label("context_audio_url"),
                    Item.part_of_speech.label("part_of_speech"),
                    Item.creator_id.label("creator_id"),
                    Item.status.label("item_status"),
                    LangT.id.label("resolved_trans_id"),
                    LangT.term_trans.label("prompt"),
                    LangT.context_trans.label("context_trans"),
                    UserProgress.last_reviewed.label("last_reviewed"),
                )
                .select_from(Item)
                .outerjoin(
                    LangT,
                    and_(
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
            pos = row.part_of_speech.value if row.part_of_speech is not None else None
            cloze_prefix, cloze_word, cloze_suffix = _split_cloze(row.context, row.answer)
            hints[str(row.item_id)] = {
                "prompt": row.prompt,  # None when no translation found; caller applies fallback
                "answer": row.answer,
                "context": row.context,
                "context_trans": row.context_trans,
                "image_url": row.image_url,
                "audio_url": row.audio_url,
                "context_audio_url": row.context_audio_url,
                "part_of_speech": pos,
                "creator_id": row.creator_id,
                "item_status": row.item_status.value if row.item_status is not None else "DRAFT",
                "translation_id": row.resolved_trans_id,
                "last_reviewed": (row.last_reviewed.isoformat() if row.last_reviewed else None),
                "synonyms": synonyms.get(row.item_id, []),
                "cloze_prefix": cloze_prefix,
                "cloze_word": cloze_word,
                "cloze_suffix": cloze_suffix,
            }

        return hints

    async def _fetch_synonyms(self, item_ids: list[int]) -> dict[int, list[str]]:
        if not item_ids:
            return {}
        stmt = (
            select(ItemSynonymTerm.item_id, ItemSynonymTerm.term)
            .where(ItemSynonymTerm.item_id.in_(item_ids))
            .order_by(ItemSynonymTerm.term)
        )
        result: dict[int, list[str]] = {}
        for row in (await self._db.execute(stmt)).fetchall():
            result.setdefault(row.item_id, []).append(row.term)
        return result

    # ── Session CRUD ──────────────────────────────────────────────────────────

    async def create_session(
        self,
        user_id: int,
        set_id: int | None,
        source_lang_id: int | None = None,
    ) -> StudySession:
        db_session = StudySession(
            user_id=user_id,
            set_id=set_id,
            source_lang_id=source_lang_id,
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

    async def get_active_db_session_for_context(
        self,
        user_id: int,
        set_id: int | None,
        source_lang_id: int | None,
    ) -> StudySession | None:
        if set_id is not None:
            q = (
                select(StudySession)
                .where(
                    StudySession.user_id == user_id,
                    StudySession.set_id == set_id,
                    StudySession.status == SessionStatus.IN_PROGRESS,
                )
                .order_by(StudySession.started_at.desc())
                .limit(1)
            )
        else:
            q = (
                select(StudySession)
                .where(
                    StudySession.user_id == user_id,
                    StudySession.set_id.is_(None),
                    StudySession.source_lang_id == source_lang_id,
                    StudySession.status == SessionStatus.IN_PROGRESS,
                )
                .order_by(StudySession.started_at.desc())
                .limit(1)
            )
        return await self._db.scalar(q)

    async def get_all_in_progress_sessions(self) -> list[StudySession]:
        result = await self._db.execute(
            select(StudySession).where(StudySession.status == SessionStatus.IN_PROGRESS)
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
        row = (
            await self._db.execute(
                select(
                    func.count().label("total"),
                    func.count().filter(StudyReview.was_correct.is_(True)).label("correct"),
                    func.avg(StudyReview.response_time).label("avg_ms"),
                ).where(StudyReview.session_id == session_id)
            )
        ).one()
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
