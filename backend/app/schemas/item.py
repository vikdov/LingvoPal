# backend/app/schemas/item.py
"""Item schemas — request/response only, no business logic."""

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.models.enums import ContentStatus, PartOfSpeech
from app.schemas.common import BaseResponseWithUpdated

_BLOCKED_URL_SCHEMES = ("javascript:", "data:", "vbscript:", "file:")


def _validate_media_url(v: str | None) -> str | None:
    if v is None:
        return v
    if v.lower().lstrip().startswith(_BLOCKED_URL_SCHEMES):
        raise ValueError("URL scheme not allowed")
    return v


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
    context_audio_url: str | None = Field(None, max_length=2048)

    @field_validator("image_url", "audio_url", "context_audio_url", mode="before")
    @classmethod
    def _check_url_scheme(cls, v: str | None) -> str | None:
        return _validate_media_url(v)


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
    context_audio_url: str | None = Field(None, max_length=2048)

    @field_validator("image_url", "audio_url", "context_audio_url", mode="before")
    @classmethod
    def _check_url_scheme(cls, v: str | None) -> str | None:
        return _validate_media_url(v)


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


class SynonymTermsRequest(BaseModel):
    """PUT /api/v1/items/{item_id}/synonyms"""

    model_config = ConfigDict(str_strip_whitespace=True)

    terms: list[str] = Field(default_factory=list)


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class ItemSummaryResponse(BaseModel):
    """Slim item shape for search/list views — no timestamps or audit fields."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    term: str
    language_id: int
    context: str | None
    difficulty: int | None
    part_of_speech: PartOfSpeech | None
    image_url: str | None
    status: ContentStatus


class ItemResponse(BaseResponseWithUpdated):
    """Standard item response — full fields, no translations."""

    model_config = ConfigDict(from_attributes=True)

    term: str
    language_id: int
    context: str | None
    difficulty: int | None
    part_of_speech: PartOfSpeech | None
    lemma: str | None
    image_url: str | None
    audio_url: str | None
    context_audio_url: str | None
    status: ContentStatus
    creator_id: int | None
    verified_by: int | None

    @computed_field
    @property
    def is_public(self) -> bool:
        return self.status in (ContentStatus.APPROVED, ContentStatus.OFFICIAL)


class TranslationResponse(BaseResponseWithUpdated):
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


class TranslationSuggestion(BaseModel):
    """Suggested translation."""

    text: str
    context_trans: str | None = None
    language: str | None = None


class ImageSuggestion(BaseModel):
    """Suggested image with metadata."""

    url: str
    thumbnail_url: str | None = None
    source: str | None = None


class SuggestItemMetadataRequest(BaseModel):
    """Request suggestions for item metadata."""

    term: str = Field(..., min_length=1, max_length=500)
    source_language: str = Field(..., min_length=1, max_length=100)
    source_language_code: str = Field(..., min_length=2, max_length=10)
    target_language: str | None = Field(None, max_length=100)
    context: str | None = Field(None, max_length=1000)


class SearchImagesRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)
    count: int = Field(4, ge=1, le=10)


class GenerateAudioRequest(BaseModel):
    """Request TTS audio for a term and optional context sentence."""

    term: str = Field(..., min_length=1, max_length=500)
    language_code: str = Field(..., min_length=2, max_length=10)
    context: str | None = Field(None, max_length=1000)


class GenerateAudioResponse(BaseModel):
    audio_url: str | None = None
    context_audio_url: str | None = None


class ItemMetadataSuggestion(BaseModel):
    """AI-suggested metadata (ready to fill item form)."""

    # System use
    lemma: str | None = None

    # Practice UI
    part_of_speech: str | None = None
    cefr_level: str | None = None
    context: str | None = None

    # Collections
    translations: list[TranslationSuggestion] = Field(default_factory=list)
    synonyms: list[str] = Field(default_factory=list)

    # Media
    tts_audio_url: str | None = None
    context_tts_audio_url: str | None = None
    image_suggestions: list[ImageSuggestion] = Field(default_factory=list)
    image_query: str | None = (
        None  # Query used for image search; pass back to /search_images for more
    )

    # Diagnostics
    warnings: list[str] = Field(default_factory=list)


__all__ = [
    "ItemCreateRequest",
    "ItemUpdateRequest",
    "AddExistingItemRequest",
    "TranslationCreateRequest",
    "TranslationUpdateRequest",
    "SynonymTermsRequest",
    "ItemSummaryResponse",
    "ItemResponse",
    "ItemDetailResponse",
    "TranslationResponse",
    "SetItemResponse",
    "TranslationSuggestion",
    "ImageSuggestion",
    "SuggestItemMetadataRequest",
    "ItemMetadataSuggestion",
    "GenerateAudioRequest",
    "GenerateAudioResponse",
    "SearchImagesRequest",
]
