# backend/app/repositories/item_repo.py
"""Item repository — raw DB access only. No business logic."""

from collections.abc import Collection
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import case, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import outerjoin, selectinload

from app.models.enums import ContentStatus, PartOfSpeech
from app.models.item import Item
from app.models.item_quality_metrics import ItemQualityMetrics
from app.models.item_synonym_term import ItemSynonymTerm
from app.models.language import Language
from app.models.set_item import SetItem
from app.models.translation import Translation

_PUBLIC_STATUSES = (ContentStatus.COMMUNITY, ContentStatus.APPROVED, ContentStatus.OFFICIAL)


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

    async def find_by_content_hashes(self, hashes: Collection[str]) -> dict[str, Item]:
        """Bulk-fetch non-deleted items by content_hash. Returns {hash: Item}."""
        if not hashes:
            return {}
        result = await self._session.execute(
            select(Item)
            .where(Item.content_hash.in_(hashes), Item.deleted_at.is_(None))
            .order_by(Item.created_at)
        )
        return {item.content_hash: item for item in result.scalars().all() if item.content_hash}

    async def find_by_content_hash(self, h: str) -> Item | None:
        """Single-hash lookup — used in IntegrityError recovery path."""
        result = await self._session.execute(
            select(Item).where(Item.content_hash == h, Item.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_language_code(self, language_id: int) -> str | None:
        """Return ISO 639-1 code for a language ID. Used for language detection."""
        result = await self._session.execute(
            select(Language.code).where(Language.id == language_id)
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Set membership
    # ------------------------------------------------------------------

    async def get_set_items(
        self, set_id: int, skip: int = 0, limit: int = 20
    ) -> Sequence[SetItem]:
        """Return a page of active SetItem rows for a set with items and translations."""
        result = await self._session.execute(
            select(SetItem)
            .join(Item, SetItem.item_id == Item.id)
            .where(SetItem.set_id == set_id, Item.deleted_at.is_(None))
            .options(selectinload(SetItem.item).selectinload(Item.translations))
            .order_by(SetItem.sort_order, Item.id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_set_items(self, set_id: int) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(SetItem)
            .join(Item, SetItem.item_id == Item.id)
            .where(SetItem.set_id == set_id, Item.deleted_at.is_(None))
        )
        return result.scalar_one()

    async def get_distinct_item_languages(self, set_id: int) -> list[int]:
        """Return the distinct language_ids of all active items in a set."""
        result = await self._session.execute(
            select(Item.language_id)
            .join(SetItem, SetItem.item_id == Item.id)
            .where(SetItem.set_id == set_id, Item.deleted_at.is_(None))
            .distinct()
        )
        return list(result.scalars().all())

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
        status_weight = case(
            (Item.status == ContentStatus.OFFICIAL, 1.0),
            (Item.status == ContentStatus.APPROVED, 0.7),
            else_=0.3,
        )
        quality_score = (
            status_weight
            * (
                0.4 * func.coalesce(ItemQualityMetrics.global_success_rate, 0.0)
                + 0.3 * func.log(func.coalesce(ItemQualityMetrics.learner_count, 0) + 1)
                + 0.3 * func.least(func.coalesce(ItemQualityMetrics.avg_interval, 0.0) / 120.0, 1.0)
            )
        )
        stmt = stmt.outerjoin(
            ItemQualityMetrics, ItemQualityMetrics.item_id == Item.id
        )
        result = await self._session.execute(
            stmt.order_by(quality_score.desc(), Item.term).offset(skip).limit(limit)
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

    async def get_created_by_user(
        self, user_id: int, *, query: str | None = None, skip: int = 0, limit: int = 20
    ) -> Sequence[Item]:
        stmt = (
            select(Item)
            .where(Item.creator_id == user_id, Item.deleted_at.is_(None))
            .options(selectinload(Item.translations))
            .order_by(Item.created_at.desc())
        )
        if query:
            stmt = stmt.where(Item.term.ilike(f"%{query}%"))
        result = await self._session.execute(stmt.offset(skip).limit(limit))
        return result.scalars().all()

    async def count_created_by_user(self, user_id: int, *, query: str | None = None) -> int:
        stmt = (
            select(func.count())
            .select_from(Item)
            .where(Item.creator_id == user_id, Item.deleted_at.is_(None))
        )
        if query:
            stmt = stmt.where(Item.term.ilike(f"%{query}%"))
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def count_external_set_memberships(self, item_id: int, owner_id: int) -> int:
        """Count SetItem rows for this item in sets NOT owned by owner_id."""
        from app.models.set import Set  # local import avoids circular
        result = await self._session.execute(
            select(func.count())
            .select_from(SetItem)
            .join(Set, Set.id == SetItem.set_id)
            .where(
                SetItem.item_id == item_id,
                Set.creator_id != owner_id,
                Set.deleted_at.is_(None),
            )
        )
        return result.scalar_one()

    async def release_to_community(self, item_id: int) -> None:
        """Remove creator ownership — item remains public but is no longer 'mine'."""
        await self._session.execute(
            update(Item).where(Item.id == item_id).values(creator_id=None)
        )

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
        context_audio_url: str | None = None,
        status: ContentStatus = ContentStatus.DRAFT,
        content_hash: str | None = None,
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
            context_audio_url=context_audio_url,
            status=status,
            content_hash=content_hash,
        )
        self._session.add(item)
        await self._session.flush()
        return item

    async def update(self, item_id: int, **kwargs) -> None:
        """Update item fields. Pass None to clear a nullable field."""
        allowed = frozenset({
            "term", "context", "difficulty", "part_of_speech",
            "lemma", "image_url", "audio_url", "context_audio_url",
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
        self,
        set_id: int,
        item_id: int,
        sort_order: int = 0,
        translation_id: int | None = None,
    ) -> SetItem:
        set_item = SetItem(
            set_id=set_id,
            item_id=item_id,
            sort_order=sort_order,
            translation_id=translation_id,
        )
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

    async def get_orphaned_item_ids(self, set_id: int, owner_id: int) -> list[int]:
        """Return IDs of items owned by owner_id that are ONLY in set_id (no other SetItem rows)."""
        other_sets = (
            select(SetItem.item_id)
            .where(SetItem.set_id != set_id)
            .scalar_subquery()
        )
        result = await self._session.execute(
            select(Item.id)
            .join(SetItem, SetItem.item_id == Item.id)
            .where(
                SetItem.set_id == set_id,
                Item.creator_id == owner_id,
                Item.deleted_at.is_(None),
                Item.id.not_in(other_sets),
            )
        )
        return list(result.scalars().all())

    async def soft_delete_bulk(self, item_ids: list[int]) -> None:
        if not item_ids:
            return
        await self._session.execute(
            update(Item)
            .where(Item.id.in_(item_ids))
            .values(deleted_at=datetime.now(timezone.utc))
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

    # ------------------------------------------------------------------
    # Synonyms (string terms)
    # ------------------------------------------------------------------

    async def get_synonym_terms(self, item_id: int) -> list[str]:
        result = await self._session.execute(
            select(ItemSynonymTerm.term)
            .where(ItemSynonymTerm.item_id == item_id)
            .order_by(ItemSynonymTerm.term)
        )
        return list(result.scalars().all())

    async def set_synonym_terms(self, item_id: int, language_id: int, terms: list[str]) -> None:
        """Replace all synonym terms for an item atomically."""
        await self._session.execute(
            delete(ItemSynonymTerm).where(ItemSynonymTerm.item_id == item_id)
        )
        for term in terms:
            self._session.add(ItemSynonymTerm(item_id=item_id, language_id=language_id, term=term))
        await self._session.flush()

    async def search_synonym_suggestions(self, q: str, language_id: int, limit: int = 10) -> list[str]:
        """Return distinct synonym terms matching q for autocomplete."""
        result = await self._session.execute(
            select(ItemSynonymTerm.term)
            .where(
                ItemSynonymTerm.language_id == language_id,
                ItemSynonymTerm.term.ilike(f"%{q}%"),
            )
            .distinct()
            .order_by(ItemSynonymTerm.term)
            .limit(limit)
        )
        return list(result.scalars().all())


__all__ = ["ItemRepository"]
