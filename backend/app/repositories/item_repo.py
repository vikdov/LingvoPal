# backend/app/repositories/item_repo.py
"""Item repository — raw DB access only. No business logic."""

from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import ContentStatus, PartOfSpeech
from app.models.item import Item
from app.models.set_item import SetItem
from app.models.translation import Translation

_PUBLIC_STATUSES = (ContentStatus.APPROVED, ContentStatus.OFFICIAL)


class ItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Single-item lookups
    # ------------------------------------------------------------------

    async def get_by_id(self, item_id: int) -> Item | None:
        result = await self._session.execute(
            select(Item).where(Item.id == item_id, Item.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_translations(self, item_id: int) -> Item | None:
        result = await self._session.execute(
            select(Item)
            .where(Item.id == item_id, Item.deleted_at.is_(None))
            .options(selectinload(Item.translations))
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Set membership
    # ------------------------------------------------------------------

    async def get_set_items(self, set_id: int) -> Sequence[SetItem]:
        """Return all active SetItem rows for a set with items and translations."""
        result = await self._session.execute(
            select(SetItem)
            .join(Item, SetItem.item_id == Item.id)
            .where(SetItem.set_id == set_id, Item.deleted_at.is_(None))
            .options(
                selectinload(SetItem.item).selectinload(Item.translations)
            )
            .order_by(SetItem.sort_order, Item.id)
        )
        return result.scalars().all()

    async def get_set_item(self, set_id: int, item_id: int) -> SetItem | None:
        result = await self._session.execute(
            select(SetItem).where(
                SetItem.set_id == set_id,
                SetItem.item_id == item_id,
            )
        )
        return result.scalar_one_or_none()

    async def set_item_exists(self, set_id: int, item_id: int) -> bool:
        result = await self._session.execute(
            select(SetItem.item_id).where(
                SetItem.set_id == set_id,
                SetItem.item_id == item_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_item_ids_for_set(self, set_id: int) -> list[tuple[int, int]]:
        """Return [(item_id, sort_order), ...] for forking a set."""
        result = await self._session.execute(
            select(SetItem.item_id, SetItem.sort_order)
            .where(SetItem.set_id == set_id)
            .order_by(SetItem.sort_order)
        )
        return [(row.item_id, row.sort_order) for row in result]

    # ------------------------------------------------------------------
    # Public discovery
    # ------------------------------------------------------------------

    async def search_public(
        self,
        *,
        query: str | None = None,
        language_id: int | None = None,
        part_of_speech: PartOfSpeech | None = None,
        difficulty: int | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Sequence[Item]:
        stmt = select(Item).where(
            Item.deleted_at.is_(None),
            Item.status.in_(_PUBLIC_STATUSES),
        )
        if query:
            stmt = stmt.where(Item.term.ilike(f"%{query}%"))
        if language_id:
            stmt = stmt.where(Item.language_id == language_id)
        if part_of_speech:
            stmt = stmt.where(Item.part_of_speech == part_of_speech)
        if difficulty is not None:
            stmt = stmt.where(Item.difficulty == difficulty)
        result = await self._session.execute(
            stmt.order_by(Item.term).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def count_public(
        self,
        *,
        query: str | None = None,
        language_id: int | None = None,
        part_of_speech: PartOfSpeech | None = None,
        difficulty: int | None = None,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(Item)
            .where(
                Item.deleted_at.is_(None),
                Item.status.in_(_PUBLIC_STATUSES),
            )
        )
        if query:
            stmt = stmt.where(Item.term.ilike(f"%{query}%"))
        if language_id:
            stmt = stmt.where(Item.language_id == language_id)
        if part_of_speech:
            stmt = stmt.where(Item.part_of_speech == part_of_speech)
        if difficulty is not None:
            stmt = stmt.where(Item.difficulty == difficulty)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    # ------------------------------------------------------------------
    # Item writes
    # ------------------------------------------------------------------

    async def create(
        self,
        *,
        term: str,
        language_id: int,
        creator_id: int,
        context: str | None = None,
        difficulty: int | None = None,
        part_of_speech: PartOfSpeech | None = None,
        lemma: str | None = None,
        image_url: str | None = None,
        audio_url: str | None = None,
        status: ContentStatus = ContentStatus.DRAFT,
    ) -> Item:
        item = Item(
            term=term,
            language_id=language_id,
            creator_id=creator_id,
            context=context,
            difficulty=difficulty,
            part_of_speech=part_of_speech,
            lemma=lemma,
            image_url=image_url,
            audio_url=audio_url,
            status=status,
        )
        self._session.add(item)
        await self._session.flush()
        return item

    async def update(self, item_id: int, **kwargs) -> None:
        """Update item fields. Pass None to clear a nullable field."""
        allowed = frozenset({
            "term", "context", "difficulty", "part_of_speech",
            "lemma", "image_url", "audio_url",
        })
        values = {k: v for k, v in kwargs.items() if k in allowed}
        if not values:
            return
        await self._session.execute(
            update(Item).where(Item.id == item_id).values(**values)
        )

    async def update_status(self, item_id: int, status: ContentStatus) -> None:
        await self._session.execute(
            update(Item).where(Item.id == item_id).values(status=status)
        )

    async def soft_delete(self, item_id: int) -> None:
        await self._session.execute(
            update(Item)
            .where(Item.id == item_id)
            .values(deleted_at=datetime.now(timezone.utc))
        )

    # ------------------------------------------------------------------
    # Set membership writes
    # ------------------------------------------------------------------

    async def add_to_set(
        self, set_id: int, item_id: int, sort_order: int = 0
    ) -> SetItem:
        set_item = SetItem(set_id=set_id, item_id=item_id, sort_order=sort_order)
        self._session.add(set_item)
        await self._session.flush()
        return set_item

    async def remove_from_set(self, set_id: int, item_id: int) -> None:
        await self._session.execute(
            delete(SetItem).where(
                SetItem.set_id == set_id,
                SetItem.item_id == item_id,
            )
        )

    # ------------------------------------------------------------------
    # Translation lookups
    # ------------------------------------------------------------------

    async def get_translation(self, translation_id: int) -> Translation | None:
        result = await self._session.execute(
            select(Translation).where(
                Translation.id == translation_id,
                Translation.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_item_translation_by_language(
        self, item_id: int, language_id: int
    ) -> Translation | None:
        """Get the active translation for an item in a specific language."""
        result = await self._session.execute(
            select(Translation).where(
                Translation.item_id == item_id,
                Translation.language_id == language_id,
                Translation.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Translation writes
    # ------------------------------------------------------------------

    async def create_translation(
        self,
        *,
        item_id: int,
        language_id: int,
        term_trans: str,
        context_trans: str | None,
        creator_id: int,
        status: ContentStatus = ContentStatus.DRAFT,
    ) -> Translation:
        t = Translation(
            item_id=item_id,
            language_id=language_id,
            term_trans=term_trans,
            context_trans=context_trans,
            creator_id=creator_id,
            status=status,
        )
        self._session.add(t)
        await self._session.flush()
        return t

    async def update_translation_fields(
        self, translation_id: int, **kwargs
    ) -> None:
        """Update translation fields; pass None to clear a nullable field."""
        allowed = frozenset({"term_trans", "context_trans"})
        values = {k: v for k, v in kwargs.items() if k in allowed}
        if not values:
            return
        await self._session.execute(
            update(Translation)
            .where(Translation.id == translation_id)
            .values(**values)
        )

    async def update_translation_status(
        self, translation_id: int, status: ContentStatus
    ) -> None:
        await self._session.execute(
            update(Translation)
            .where(Translation.id == translation_id)
            .values(status=status)
        )

    async def soft_delete_translation(self, translation_id: int) -> None:
        await self._session.execute(
            update(Translation)
            .where(Translation.id == translation_id)
            .values(deleted_at=datetime.now(timezone.utc))
        )


__all__ = ["ItemRepository"]
