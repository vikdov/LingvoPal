# backend/app/schemas/item.py
"""Item schemas — Python 3.10+ union syntax"""

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, computed_field

from app.models.enums import PartOfSpeech, ContentStatus
from app.schemas.common import BaseResponseWithDeleted


class ItemBase(BaseModel):
    """Common fields for Item"""

    term: str = Field(..., min_length=1, max_length=500)
    language_id: int = Field(..., gt=0)
    difficulty: int | None = Field(None, ge=1, le=7)  # ← Pure 3.10+
    context: str | None = Field(None, max_length=1000)
    part_of_speech: PartOfSpeech | None = None
    lemma: str | None = Field(None, max_length=500)


class ItemCreateRequest(ItemBase):
    """POST /api/v1/items"""

    pass


class TranslationCreateRequest(BaseModel):
    """Nested translation creation"""

    language_id: int = Field(..., gt=0)
    term_trans: str = Field(..., min_length=1, max_length=500)
    context_trans: str | None = Field(None, max_length=1000)


# Add this at the bottom of the file
class ItemListQueryParams(BaseModel):
    """GET /api/v1/items query parameters"""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    language_id: int | None = Field(None, gt=0)
    status: ContentStatus | None = None
    difficulty_min: int | None = Field(None, ge=1, le=7)
    difficulty_max: int | None = Field(None, ge=1, le=7)
    part_of_speech: PartOfSpeech | None = None
    search: str | None = Field(None, min_length=1, max_length=100)
    sort_by: str | None = None


class ItemUpdateRequest(BaseModel):
    """PATCH /api/v1/items/{item_id}"""

    term: str | None = Field(None, min_length=1, max_length=500)
    difficulty: int | None = Field(None, ge=1, le=7)
    context: str | None = Field(None, max_length=1000)
    part_of_speech: PartOfSpeech | None = None
    lemma: str | None = Field(None, max_length=500)


class ItemListResponse(ItemBase):
    """GET /api/v1/items (list view)"""

    id: int
    status: ContentStatus
    creator_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class ItemResponse(ItemBase):
    """GET /api/v1/items/{id} (standard detail)"""

    id: int
    status: ContentStatus
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    term: str
    creator_id: int | None = None
    verified_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


class TranslationResponse(BaseResponseWithDeleted):
    """Translation of an item"""

    item_id: int
    language_id: int
    term_trans: str
    context_trans: str | None = None
    status: ContentStatus
    creator_id: int | None = None
    verified_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


class ItemDetailResponse(ItemResponse):
    """GET /api/v1/items/{id} (with translations)"""

    translations: list[TranslationResponse] = Field(default_factory=list)

    @computed_field
    @property
    def translation_count(self) -> int:
        return len(self.translations)


__all__ = [
    "ItemBase",
    "ItemCreateRequest",
    "ItemUpdateRequest",
    "ItemListResponse",
    "ItemResponse",
    "ItemDetailResponse",
    "TranslationResponse",
    "TranslationCreateRequest",
    "ItemListQueryParams",
]
