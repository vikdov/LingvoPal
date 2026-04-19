# backend/app/repositories/set_repo.py
"""Set repository — raw DB access only. No business logic."""

from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import ContentStatus
from app.models.item import Item
from app.models.set import Set
from app.models.set_item import SetItem
from app.models.user_set_library import UserSetLibrary

_PUBLIC_STATUSES = (ContentStatus.APPROVED, ContentStatus.OFFICIAL)


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
            .where(Set.creator_id == user_id, Set.deleted_at.is_(None))
            .order_by(Set.created_at.desc())
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
        result = await self._session.execute(
            stmt.order_by(Set.created_at.desc()).offset(skip).limit(limit)
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
        target_lang_id: int,
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
            .where(UserSetLibrary.user_id == user_id)
            .options(selectinload(UserSetLibrary.set))
            .order_by(
                UserSetLibrary.is_pinned.desc(),
                UserSetLibrary.added_at.desc(),
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def save_to_library(self, user_id: int, set_id: int) -> UserSetLibrary:
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


__all__ = ["SetRepository"]
