# backend/app/services/item_service.py
"""
Item service — all business logic for items, translations, and set membership.
"""

import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DuplicateResourceError,
    LingvoPalError,
    NotAuthorizedError,
    ResourceNotFoundError,
)
from app.models.enums import ContentStatus, PartOfSpeech
from app.models.item import Item
from app.models.set_item import SetItem
from app.models.translation import Translation
from app.repositories.item_repo import ItemRepository
from app.repositories.set_repo import SetRepository
from app.schemas.item import (
    ItemCreateRequest,
    ItemUpdateRequest,
    TranslationCreateRequest,
    TranslationUpdateRequest,
)

_PUBLIC_STATUSES = (ContentStatus.APPROVED, ContentStatus.OFFICIAL)
_ALLOWED_IMAGE_TYPES = frozenset({
    "image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"
})
_MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB
_UPLOAD_DIR = Path("static/uploads")


class ItemService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._items = ItemRepository(session)
        self._sets = SetRepository(session)

    # ------------------------------------------------------------------
    # Private guards
    # ------------------------------------------------------------------

    async def _require_owned_set(self, user_id: int, set_id: int):
        s = await self._sets.get_by_id(set_id)
        if not s:
            raise ResourceNotFoundError("Set", set_id)
        if s.creator_id != user_id:
            raise NotAuthorizedError("modify items in this set")
        return s

    async def _require_owned_item(self, user_id: int, item_id: int) -> Item:
        item = await self._items.get_by_id(item_id)
        if not item:
            raise ResourceNotFoundError("Item", item_id)
        if item.creator_id != user_id:
            raise NotAuthorizedError("modify this item")
        return item

    async def _require_owned_translation(
        self, user_id: int, item_id: int, translation_id: int
    ) -> Translation:
        t = await self._items.get_translation(translation_id)
        if not t or t.item_id != item_id:
            raise ResourceNotFoundError("Translation", translation_id)
        if t.creator_id != user_id:
            raise NotAuthorizedError("modify this translation")
        return t

    # ------------------------------------------------------------------
    # Item CRUD
    # ------------------------------------------------------------------

    async def create_item(
        self, user_id: int, set_id: int, data: ItemCreateRequest
    ) -> tuple[Item, SetItem]:
        await self._require_owned_set(user_id, set_id)
        item = await self._items.create(
            term=data.term,
            language_id=data.language_id,
            creator_id=user_id,
            context=data.context,
            difficulty=data.difficulty,
            part_of_speech=data.part_of_speech,
            lemma=data.lemma,
            image_url=data.image_url,
            audio_url=data.audio_url,
            status=ContentStatus.DRAFT,
        )
        set_item = await self._items.add_to_set(set_id, item.id)
        await self._session.commit()
        await self._session.refresh(item)
        return item, set_item

    async def get_set_items(self, user_id: int, set_id: int) -> list[SetItem]:
        s = await self._sets.get_by_id(set_id)
        if not s:
            raise ResourceNotFoundError("Set", set_id)
        if s.creator_id != user_id and s.status not in _PUBLIC_STATUSES:
            raise ResourceNotFoundError("Set", set_id)
        return list(await self._items.get_set_items(set_id))

    async def update_item(
        self, user_id: int, item_id: int, data: ItemUpdateRequest
    ) -> Item:
        await self._require_owned_item(user_id, item_id)
        values = data.model_dump(exclude_unset=True)
        # Treat explicitly empty strings as None for nullable string fields
        for field in ("context", "lemma", "audio_url"):
            if field in values and values[field] == "":
                values[field] = None
        if values:
            await self._items.update(item_id, **values)
        await self._session.commit()
        return await self._items.get_by_id_with_translations(item_id)

    async def delete_item(self, user_id: int, item_id: int) -> None:
        await self._require_owned_item(user_id, item_id)
        await self._items.soft_delete(item_id)
        await self._session.commit()

    async def submit_item(self, user_id: int, item_id: int) -> Item:
        """Transition item from DRAFT → PENDING_REVIEW."""
        item = await self._require_owned_item(user_id, item_id)
        if item.status != ContentStatus.DRAFT:
            raise LingvoPalError(
                f"Item is already {item.status.value} and cannot be submitted."
            )
        await self._items.update_status(item_id, ContentStatus.PENDING_REVIEW)
        await self._session.commit()
        return await self._items.get_by_id_with_translations(item_id)

    async def upload_item_image(
        self, user_id: int, item_id: int, file: UploadFile, base_url: str
    ) -> Item:
        await self._require_owned_item(user_id, item_id)

        content_type = file.content_type or ""
        if content_type not in _ALLOWED_IMAGE_TYPES:
            raise LingvoPalError(
                "Invalid file type. Allowed: JPEG, PNG, WebP, GIF."
            )

        data = await file.read()
        if len(data) > _MAX_IMAGE_BYTES:
            raise LingvoPalError("Image exceeds 5 MB limit.")

        ext = (file.filename or "image").rsplit(".", 1)[-1].lower()
        if ext not in {"jpg", "jpeg", "png", "webp", "gif"}:
            ext = "jpg"

        _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid.uuid4().hex}.{ext}"
        (_UPLOAD_DIR / filename).write_bytes(data)

        image_url = f"{base_url.rstrip('/')}/static/uploads/{filename}"
        await self._items.update(item_id, image_url=image_url)
        await self._session.commit()
        return await self._items.get_by_id_with_translations(item_id)

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    async def search_public_items(
        self,
        *,
        query: str | None = None,
        language_id: int | None = None,
        part_of_speech: PartOfSpeech | None = None,
        difficulty: int | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Item], int]:
        items = list(
            await self._items.search_public(
                query=query,
                language_id=language_id,
                part_of_speech=part_of_speech,
                difficulty=difficulty,
                skip=skip,
                limit=limit,
            )
        )
        total = await self._items.count_public(
            query=query,
            language_id=language_id,
            part_of_speech=part_of_speech,
            difficulty=difficulty,
        )
        return items, total

    # ------------------------------------------------------------------
    # Set membership
    # ------------------------------------------------------------------

    async def add_item_to_set(
        self, user_id: int, set_id: int, item_id: int, sort_order: int = 0
    ) -> SetItem:
        await self._require_owned_set(user_id, set_id)
        item = await self._items.get_by_id(item_id)
        if not item:
            raise ResourceNotFoundError("Item", item_id)
        if item.creator_id != user_id and item.status not in _PUBLIC_STATUSES:
            raise ResourceNotFoundError("Item", item_id)
        if await self._items.set_item_exists(set_id, item_id):
            raise DuplicateResourceError("SetItem", "item_id", str(item_id))
        set_item = await self._items.add_to_set(set_id, item_id, sort_order)
        await self._session.commit()
        return set_item

    async def remove_item_from_set(
        self, user_id: int, set_id: int, item_id: int
    ) -> None:
        await self._require_owned_set(user_id, set_id)
        if not await self._items.set_item_exists(set_id, item_id):
            raise ResourceNotFoundError("Item in set", item_id)
        await self._items.remove_from_set(set_id, item_id)
        await self._session.commit()

    async def fork_item_into_set(
        self, user_id: int, set_id: int, item_id: int
    ) -> tuple[Item, SetItem]:
        await self._require_owned_set(user_id, set_id)
        source = await self._items.get_by_id(item_id)
        if not source:
            raise ResourceNotFoundError("Item", item_id)
        if source.status not in _PUBLIC_STATUSES:
            raise NotAuthorizedError("fork this item (it is not public)")
        forked = await self._items.create(
            term=source.term,
            language_id=source.language_id,
            creator_id=user_id,
            context=source.context,
            difficulty=source.difficulty,
            part_of_speech=source.part_of_speech,
            lemma=source.lemma,
            image_url=source.image_url,
            audio_url=source.audio_url,
            status=ContentStatus.DRAFT,
        )
        set_item = await self._items.add_to_set(set_id, forked.id)
        await self._session.commit()
        await self._session.refresh(forked)
        return forked, set_item

    # ------------------------------------------------------------------
    # Translations
    # ------------------------------------------------------------------

    async def add_translation(
        self, user_id: int, item_id: int, data: TranslationCreateRequest
    ) -> Translation:
        await self._require_owned_item(user_id, item_id)
        existing = await self._items.get_item_translation_by_language(
            item_id, data.language_id
        )
        if existing:
            raise DuplicateResourceError(
                "Translation", "language_id", str(data.language_id)
            )
        t = await self._items.create_translation(
            item_id=item_id,
            language_id=data.language_id,
            term_trans=data.term_trans,
            context_trans=data.context_trans,
            creator_id=user_id,
        )
        await self._session.commit()
        await self._session.refresh(t)
        return t

    async def update_translation(
        self,
        user_id: int,
        item_id: int,
        translation_id: int,
        data: TranslationUpdateRequest,
    ) -> Translation:
        t = await self._require_owned_translation(user_id, item_id, translation_id)
        values = data.model_dump(exclude_unset=True)
        if "context_trans" in values and values["context_trans"] == "":
            values["context_trans"] = None
        if values:
            await self._items.update_translation_fields(translation_id, **values)
        await self._session.commit()
        return await self._items.get_translation(translation_id)

    async def delete_translation(
        self, user_id: int, item_id: int, translation_id: int
    ) -> None:
        await self._require_owned_translation(user_id, item_id, translation_id)
        await self._items.soft_delete_translation(translation_id)
        await self._session.commit()

    async def submit_translation(
        self, user_id: int, item_id: int, translation_id: int
    ) -> Translation:
        t = await self._require_owned_translation(user_id, item_id, translation_id)
        if t.status != ContentStatus.DRAFT:
            raise LingvoPalError(
                f"Translation is already {t.status.value} and cannot be submitted."
            )
        await self._items.update_translation_status(
            translation_id, ContentStatus.PENDING_REVIEW
        )
        await self._session.commit()
        return await self._items.get_translation(translation_id)


__all__ = ["ItemService"]
