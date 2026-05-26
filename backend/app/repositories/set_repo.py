# backend/app/repositories/set_repo.py
"""Set repository — raw DB access only. No business logic."""

from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import case, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import ContentStatus
from app.models.item import Item
from app.models.set import Set
from app.models.set_item import SetItem
from app.models.user_set_library import UserSetLibrary

_MISSING = object()  # sentinel — distinguishes "not provided" from None

_PUBLIC_STATUSES = (ContentStatus.COMMUNITY, ContentStatus.APPROVED, ContentStatus.OFFICIAL)


class SetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Single-set lookups
    # ------------------------------------------------------------------

    async def get_by_id(self, set_id: int) -> Set | None:
        result = await self._session.execute(
            select(Set).where(Set.id == set_id, Set.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Owned sets
    # ------------------------------------------------------------------

    async def get_owned(
        self,
        user_id: int,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> Sequence[Set]:
        result = await self._session.execute(
            select(Set)
            .outerjoin(
                UserSetLibrary,
                (UserSetLibrary.set_id == Set.id) & (UserSetLibrary.user_id == user_id),
            )
            .where(Set.creator_id == user_id, Set.deleted_at.is_(None))
            .order_by(
                func.coalesce(UserSetLibrary.is_pinned, False).desc(),
                func.coalesce(UserSetLibrary.last_opened_at, Set.created_at).desc(),
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_owned(self, user_id: int) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(Set)
            .where(Set.creator_id == user_id, Set.deleted_at.is_(None))
        )
        return result.scalar_one()

    # ------------------------------------------------------------------
    # Public discovery
    # ------------------------------------------------------------------

    async def search_public(
        self,
        *,
        query: str | None = None,
        source_lang_id: int | None = None,
        target_lang_id: int | None = None,
        difficulty: int | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Sequence[Set]:
        stmt = select(Set).where(
            Set.deleted_at.is_(None),
            Set.status.in_(_PUBLIC_STATUSES),
        )
        if query:
            stmt = stmt.where(Set.title.ilike(f"%{query}%"))
        if source_lang_id:
            stmt = stmt.where(Set.source_lang_id == source_lang_id)
        if target_lang_id:
            stmt = stmt.where(Set.target_lang_id == target_lang_id)
        if difficulty is not None:
            stmt = stmt.where(Set.difficulty == difficulty)
        status_rank = case(
            (Set.status == ContentStatus.OFFICIAL, 1),
            (Set.status == ContentStatus.APPROVED, 2),
            else_=3,
        )
        result = await self._session.execute(
            stmt.order_by(status_rank, Set.created_at.desc()).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def count_public(
        self,
        *,
        query: str | None = None,
        source_lang_id: int | None = None,
        target_lang_id: int | None = None,
        difficulty: int | None = None,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(Set)
            .where(
                Set.deleted_at.is_(None),
                Set.status.in_(_PUBLIC_STATUSES),
            )
        )
        if query:
            stmt = stmt.where(Set.title.ilike(f"%{query}%"))
        if source_lang_id:
            stmt = stmt.where(Set.source_lang_id == source_lang_id)
        if target_lang_id:
            stmt = stmt.where(Set.target_lang_id == target_lang_id)
        if difficulty is not None:
            stmt = stmt.where(Set.difficulty == difficulty)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    # ------------------------------------------------------------------
    # Item count helper (used by service to annotate responses)
    # ------------------------------------------------------------------

    async def count_items(self, set_id: int) -> int:
        """Count active (non-soft-deleted) items in a set."""
        result = await self._session.execute(
            select(func.count())
            .select_from(SetItem)
            .join(Item, SetItem.item_id == Item.id)
            .where(SetItem.set_id == set_id, Item.deleted_at.is_(None))
        )
        return result.scalar_one()

    async def count_items_batch(self, set_ids: list[int]) -> dict[int, int]:
        """Count active items for multiple sets in one query."""
        if not set_ids:
            return {}
        result = await self._session.execute(
            select(SetItem.set_id, func.count().label("cnt"))
            .join(Item, SetItem.item_id == Item.id)
            .where(SetItem.set_id.in_(set_ids), Item.deleted_at.is_(None))
            .group_by(SetItem.set_id)
        )
        counts = {row.set_id: row.cnt for row in result.fetchall()}
        return {sid: counts.get(sid, 0) for sid in set_ids}

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    async def create(
        self,
        *,
        title: str,
        source_lang_id: int,
        target_lang_id: int | None,
        creator_id: int,
        description: str | None = None,
        difficulty: int | None = None,
        status: ContentStatus = ContentStatus.DRAFT,
    ) -> Set:
        s = Set(
            title=title,
            description=description,
            difficulty=difficulty,
            source_lang_id=source_lang_id,
            target_lang_id=target_lang_id,
            creator_id=creator_id,
            status=status,
        )
        self._session.add(s)
        await self._session.flush()
        return s

    async def update(
        self,
        set_id: int,
        *,
        title: str | None = None,
        description: str | None = None,
        difficulty: int | None = None,
        status: ContentStatus | None = None,
        source_lang_id: int | None = None,
        target_lang_id: object = _MISSING,
    ) -> None:
        values: dict = {}
        if title is not None:
            values["title"] = title
        if description is not None:
            values["description"] = description
        if difficulty is not None:
            values["difficulty"] = difficulty
        if status is not None:
            values["status"] = status
        if source_lang_id is not None:
            values["source_lang_id"] = source_lang_id
        if target_lang_id is not _MISSING:
            values["target_lang_id"] = target_lang_id  # allows explicit None (clear)
        if not values:
            return
        await self._session.execute(
            update(Set).where(Set.id == set_id).values(**values)
        )

    async def soft_delete(self, set_id: int) -> None:
        await self._session.execute(
            update(Set)
            .where(Set.id == set_id)
            .values(deleted_at=datetime.now(timezone.utc))
        )

    async def restore(self, set_id: int) -> None:
        await self._session.execute(
            update(Set).where(Set.id == set_id).values(deleted_at=None)
        )

    async def find_by_title_and_langs(
        self,
        title: str,
        source_lang_id: int,
        target_lang_id: int | None,
    ) -> Sequence[Set]:
        """Find sets (including soft-deleted) matching title + lang pair."""
        cond = [Set.title == title, Set.source_lang_id == source_lang_id]
        if target_lang_id is None:
            cond.append(Set.target_lang_id.is_(None))
        else:
            cond.append(Set.target_lang_id == target_lang_id)
        result = await self._session.execute(select(Set).where(*cond))
        return result.scalars().all()

    async def get_ordered_item_hashes(self, set_id: int) -> list[str | None]:
        """Get content_hashes of set items ordered by sort_order."""
        result = await self._session.execute(
            select(Item.content_hash)
            .join(SetItem, SetItem.item_id == Item.id)
            .where(SetItem.set_id == set_id)
            .order_by(SetItem.sort_order)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # User set library
    # ------------------------------------------------------------------

    async def get_library_entry(
        self, user_id: int, set_id: int
    ) -> UserSetLibrary | None:
        result = await self._session.execute(
            select(UserSetLibrary).where(
                UserSetLibrary.user_id == user_id,
                UserSetLibrary.set_id == set_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_user_library(
        self,
        user_id: int,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> Sequence[UserSetLibrary]:
        """Load library entries with their sets eagerly (avoids raise_on_sql)."""
        result = await self._session.execute(
            select(UserSetLibrary)
            .join(Set, Set.id == UserSetLibrary.set_id)
            .where(UserSetLibrary.user_id == user_id, Set.deleted_at.is_(None))
            .options(selectinload(UserSetLibrary.set))
            .order_by(
                UserSetLibrary.is_pinned.desc(),
                func.coalesce(UserSetLibrary.last_opened_at, UserSetLibrary.added_at).desc(),
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def save_to_library(self, user_id: int, set_id: int) -> UserSetLibrary:
        existing = await self.get_library_entry(user_id, set_id)
        if existing:
            return existing
        entry = UserSetLibrary(user_id=user_id, set_id=set_id)
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def remove_from_library(self, user_id: int, set_id: int) -> None:
        await self._session.execute(
            delete(UserSetLibrary).where(
                UserSetLibrary.user_id == user_id,
                UserSetLibrary.set_id == set_id,
            )
        )

    async def count_user_library(self, user_id: int) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(UserSetLibrary)
            .join(Set, Set.id == UserSetLibrary.set_id)
            .where(UserSetLibrary.user_id == user_id, Set.deleted_at.is_(None))
        )
        return result.scalar_one()

    async def touch_library_entry(self, user_id: int, set_id: int) -> None:
        """Update last_opened_at when a user opens a set from their library."""
        await self._session.execute(
            update(UserSetLibrary)
            .where(
                UserSetLibrary.user_id == user_id,
                UserSetLibrary.set_id == set_id,
            )
            .values(last_opened_at=datetime.now(timezone.utc))
        )

    async def get_library_pins_batch(
        self, user_id: int, set_ids: list[int]
    ) -> dict[int, bool]:
        """Return {set_id: is_pinned} for each set_id that has a library entry."""
        if not set_ids:
            return {}
        result = await self._session.execute(
            select(UserSetLibrary.set_id, UserSetLibrary.is_pinned).where(
                UserSetLibrary.user_id == user_id,
                UserSetLibrary.set_id.in_(set_ids),
            )
        )
        return {row.set_id: row.is_pinned for row in result}

    async def set_pin(self, user_id: int, set_id: int, is_pinned: bool) -> None:
        await self._session.execute(
            update(UserSetLibrary)
            .where(
                UserSetLibrary.user_id == user_id,
                UserSetLibrary.set_id == set_id,
            )
            .values(is_pinned=is_pinned)
        )


__all__ = ["SetRepository"]
