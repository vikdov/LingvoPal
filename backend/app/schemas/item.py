# backend/app/schemas/item.py
"""Item schemas — request/response only, no business logic."""

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.enums import ContentStatus, PartOfSpeech
from app.schemas.common import BaseResponseWithDeleted


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================


class ItemCreateRequest(BaseModel):
    """POST /api/v1/sets/{set_id}/items"""

    model_config = ConfigDict(str_strip_whitespace=True)

    term: str = Field(..., min_length=1, max_length=500)
    language_id: int = Field(..., gt=0)
    context: str | None = Field(None, max_length=1000)
    difficulty: int | None = Field(None, ge=1, le=7)
    part_of_speech: PartOfSpeech | None = None
    lemma: str | None = Field(None, max_length=500)
    image_url: str | None = Field(None, max_length=2048)
    audio_url: str | None = Field(None, max_length=2048)


class ItemUpdateRequest(BaseModel):
    """PATCH /api/v1/items/{item_id}"""

    model_config = ConfigDict(str_strip_whitespace=True)

    term: str | None = Field(None, min_length=1, max_length=500)
    context: str | None = Field(None, max_length=1000)
    difficulty: int | None = Field(None, ge=1, le=7)
    part_of_speech: PartOfSpeech | None = None
    lemma: str | None = Field(None, max_length=500)
    image_url: str | None = Field(None, max_length=2048)
    audio_url: str | None = Field(None, max_length=2048)


class AddExistingItemRequest(BaseModel):
    """Body for POST /api/v1/sets/{set_id}/items/{item_id} — add existing item to set."""

    sort_order: int = Field(default=0, ge=0)


class TranslationCreateRequest(BaseModel):
    """POST /api/v1/items/{item_id}/translations"""

    model_config = ConfigDict(str_strip_whitespace=True)

    language_id: int = Field(..., gt=0)
    term_trans: str = Field(..., min_length=1, max_length=500)
    context_trans: str | None = Field(None, max_length=1000)


class TranslationUpdateRequest(BaseModel):
    """PATCH /api/v1/items/{item_id}/translations/{trans_id}"""

    model_config = ConfigDict(str_strip_whitespace=True)

    term_trans: str | None = Field(None, min_length=1, max_length=500)
    context_trans: str | None = Field(None, max_length=1000)


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class ItemResponse(BaseResponseWithDeleted):
    """Standard item response."""

    model_config = ConfigDict(from_attributes=True)

    term: str
    language_id: int
    context: str | None
    difficulty: int | None
    part_of_speech: PartOfSpeech | None
    lemma: str | None
    image_url: str | None
    audio_url: str | None
    status: ContentStatus
    creator_id: int | None
    verified_by: int | None

    @computed_field
    @property
    def is_public(self) -> bool:
        return self.status in (ContentStatus.APPROVED, ContentStatus.OFFICIAL)


class TranslationResponse(BaseResponseWithDeleted):
    """Translation of an item."""

    model_config = ConfigDict(from_attributes=True)

    item_id: int
    language_id: int
    term_trans: str
    context_trans: str | None
    status: ContentStatus
    creator_id: int | None
    verified_by: int | None


class ItemDetailResponse(ItemResponse):
    """Item with its translations loaded."""

    translations: list[TranslationResponse] = Field(default_factory=list)

    @computed_field
    @property
    def translation_count(self) -> int:
        return len(self.translations)


class SetItemResponse(BaseModel):
    """An item as it appears within a set, including sort order and translations."""

    model_config = ConfigDict(from_attributes=True)

    set_id: int
    item_id: int
    sort_order: int
    item: ItemDetailResponse


__all__ = [
    "ItemCreateRequest",
    "ItemUpdateRequest",
    "AddExistingItemRequest",
    "TranslationCreateRequest",
    "TranslationUpdateRequest",
    "ItemResponse",
    "SetItemResponse",
    "TranslationResponse",
    "ItemDetailResponse",
]
