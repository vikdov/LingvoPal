# backend/app/schemas/set.py
"""Set schemas — request/response only, no business logic."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.models.enums import ContentStatus
from app.schemas.common import BaseResponseWithUpdated
from app.schemas.language import LanguageResponse


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================


class SetCreateRequest(BaseModel):
    """POST /api/v1/sets"""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    difficulty: int | None = Field(None, ge=1, le=7)
    source_lang_id: int = Field(..., gt=0, description="Language to learn FROM")
    target_lang_id: int | None = Field(None, gt=0, description="Language to learn TO — omit for monolingual sets")

    @field_validator("target_lang_id")
    @classmethod
    def langs_must_differ(cls, v: int | None, info) -> int | None:
        if v is not None and v == info.data.get("source_lang_id"):
            raise ValueError("source and target languages must be different")
        return v


class SetUpdateRequest(BaseModel):
    """PATCH /api/v1/sets/{set_id}"""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    difficulty: int | None = Field(None, ge=1, le=7)
    source_lang_id: int | None = Field(None, gt=0)
    target_lang_id: int | None = Field(None, gt=0)

    @field_validator("target_lang_id")
    @classmethod
    def langs_must_differ(cls, v: int | None, info) -> int | None:
        if v is not None and v == info.data.get("source_lang_id"):
            raise ValueError("source and target languages must be different")
        return v


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class SetResponse(BaseResponseWithUpdated):
    """Standard set response."""

    model_config = ConfigDict(from_attributes=True)

    title: str
    description: str | None
    difficulty: int | None
    status: ContentStatus
    creator_id: int | None
    creator_username: str | None = None
    source_lang_id: int
    target_lang_id: int | None
    item_count: int = Field(default=0, description="Number of active items in the set")

    @computed_field
    @property
    def is_public(self) -> bool:
        return self.status in (ContentStatus.APPROVED, ContentStatus.OFFICIAL)


class SetDetailResponse(SetResponse):
    """Set with resolved language objects."""

    source_language: LanguageResponse | None = None
    target_language: LanguageResponse | None = None


class SetSummaryResponse(BaseModel):
    """Slim set shape for list/search/library views — no description or audit fields."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    difficulty: int | None
    status: ContentStatus
    source_lang_id: int
    target_lang_id: int | None
    item_count: int = 0
    creator_username: str | None = None


class CreatedSetSummaryResponse(SetSummaryResponse):
    """SetSummaryResponse augmented with the user's library pin state."""

    is_pinned: bool = False


class SetLibraryPinRequest(BaseModel):
    """PATCH /api/v1/sets/{set_id}/library — update pin state."""

    is_pinned: bool


class SetLibraryEntryResponse(BaseModel):
    """A set as seen from the user's saved library."""

    model_config = ConfigDict(from_attributes=True)

    set_id: int
    added_at: datetime
    last_opened_at: datetime | None
    is_pinned: bool
    set: SetSummaryResponse
    due_count: int = 0


class SetLibraryStatusResponse(BaseModel):
    in_library: bool


__all__ = [
    "SetCreateRequest",
    "SetUpdateRequest",
    "SetSummaryResponse",
    "CreatedSetSummaryResponse",
    "SetLibraryPinRequest",
    "SetResponse",
    "SetDetailResponse",
    "SetLibraryEntryResponse",
    "SetLibraryStatusResponse",
]
