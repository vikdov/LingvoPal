# backend/app/schemas/set.py
"""
Set (collection of items) schemas.

Sets are thematic collections: "Workplace Vocabulary", "Travel Phrases", etc.
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, computed_field
from datetime import datetime

from app.models.enums import ContentStatus
from app.schemas.language import LanguageResponse


# ============================================================================
# TIER 1: BASE
# ============================================================================


class SetBase(BaseModel):
    """Common fields for Set"""

    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    difficulty: Optional[int] = Field(None, ge=1, le=7)
    source_lang_id: int = Field(..., gt=0, description="Language to learn FROM")
    target_lang_id: int = Field(..., gt=0, description="Language to learn TO")


# ============================================================================
# TIER 2: INPUT SCHEMAS
# ============================================================================


class SetCreateRequest(SetBase):
    """POST /api/v1/sets"""

    # Inherited from SetBase
    pass


class SetUpdateRequest(BaseModel):
    """PATCH /api/v1/sets/{set_id}"""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    difficulty: int | None = Field(None, ge=1, le=7)


# ============================================================================
# TIER 3: OUTPUT SCHEMAS (List view)
# ============================================================================


class SetListResponse(SetBase):
    """GET /api/v1/sets (paginated)"""

    id: int
    status: ContentStatus
    creator_id: Optional[int]

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# TIER 4: OUTPUT SCHEMAS (Standard detail)
# ============================================================================


class SetResponse(SetBase):
    """GET /api/v1/sets/{set_id}"""

    id: int
    status: ContentStatus
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    creator_id: Optional[int]
    verified_by: Optional[int]

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# TIER 5: OUTPUT SCHEMAS (Extended with relationships)
# ============================================================================


class SetItemReference(BaseModel):
    """Lightweight item reference within a set"""

    id: int
    term: str
    language_id: int
    difficulty: Optional[int]

    model_config = ConfigDict(from_attributes=True)


class SetDetailResponse(SetResponse):
    """GET /api/v1/sets/{set_id}?expand=items"""

    source_language: Optional[LanguageResponse] = None
    target_language: Optional[LanguageResponse] = None
    items: list[SetItemReference] = Field(default_factory=list)

    @computed_field
    @property
    def item_count(self) -> int:
        return len(self.items)


# ============================================================================
# QUERY PARAMETERS
# ============================================================================


class SetListQueryParams(BaseModel):
    """GET /api/v1/sets query parameters"""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    source_lang_id: Optional[int] = Field(None, gt=0)
    target_lang_id: Optional[int] = Field(None, gt=0)
    status: Optional[ContentStatus] = None
    difficulty_min: Optional[int] = Field(None, ge=1, le=7)
    difficulty_max: Optional[int] = Field(None, ge=1, le=7)
    search: Optional[str] = Field(None, min_length=1, max_length=100)
    creator_id: Optional[int] = Field(None, gt=0)


__all__ = [
    "SetBase",
    "SetCreateRequest",
    "SetUpdateRequest",
    "SetListResponse",
    "SetResponse",
    "SetDetailResponse",
    "SetItemReference",
    "SetListQueryParams",
]
