# backend/app/schemas/set.py
"""Set schemas — request/response only, no business logic."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.models.enums import ContentStatus
from app.schemas.common import BaseResponseWithDeleted
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
    target_lang_id: int = Field(..., gt=0, description="Language to learn TO")

    @field_validator("target_lang_id")
    @classmethod
    def langs_must_differ(cls, v: int, info) -> int:
        if v == info.data.get("source_lang_id"):
            raise ValueError("source and target languages must be different")
        return v


class SetUpdateRequest(BaseModel):
    """PATCH /api/v1/sets/{set_id}"""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    difficulty: int | None = Field(None, ge=1, le=7)


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class SetResponse(BaseResponseWithDeleted):
    """Standard set response."""

    model_config = ConfigDict(from_attributes=True)

    title: str
    description: str | None
    difficulty: int | None
    status: ContentStatus
    creator_id: int | None
    source_lang_id: int
    target_lang_id: int
    item_count: int = Field(default=0, description="Number of active items in the set")

    @computed_field
    @property
    def is_public(self) -> bool:
        return self.status in (ContentStatus.APPROVED, ContentStatus.OFFICIAL)


class SetDetailResponse(SetResponse):
    """Set with resolved language objects."""

    source_language: LanguageResponse | None = None
    target_language: LanguageResponse | None = None


class SetLibraryEntryResponse(BaseModel):
    """A set as seen from the user's saved library."""

    model_config = ConfigDict(from_attributes=True)

    set_id: int
    added_at: datetime
    last_opened_at: datetime | None
    is_pinned: bool
    set: SetResponse


__all__ = [
    "SetCreateRequest",
    "SetUpdateRequest",
    "SetResponse",
    "SetDetailResponse",
    "SetLibraryEntryResponse",
]
