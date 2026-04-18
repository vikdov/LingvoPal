# backend/app/schemas/moderation.py
"""
Content moderation schemas.

Lifecycle:
  DRAFT → (submit) → PENDING_REVIEW → (approve) → APPROVED
                                     → (reject)  → DRAFT  (resubmittable)
"""

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field, ConfigDict

from app.models.enums import ModerationTargetType, ModerationStatus
from app.schemas.common import BaseResponse


# ============================================================================
# USER INPUT SCHEMAS
# ============================================================================


class SubmitForReviewRequest(BaseModel):
    """POST /api/v1/moderation/sets/{set_id}/submit
       POST /api/v1/moderation/items/{item_id}/submit"""

    feedback: Optional[str] = Field(
        None,
        max_length=2000,
        description="Optional note to the reviewer",
    )


# ============================================================================
# ADMIN INPUT SCHEMAS
# ============================================================================


class ApproveModerationRequest(BaseModel):
    """POST /api/v1/admin/moderation/{moderation_id}/approve"""

    resolution_feedback: Optional[str] = Field(
        None, max_length=1000, description="Optional approval note"
    )


class RejectModerationRequest(BaseModel):
    """POST /api/v1/admin/moderation/{moderation_id}/reject"""

    resolution_feedback: str = Field(
        ..., min_length=1, max_length=1000, description="Reason for rejection (required)"
    )


# ============================================================================
# QUERY PARAMS
# ============================================================================


class ModerationListQueryParams(BaseModel):
    target_type: Optional[ModerationTargetType] = None
    status: Optional[ModerationStatus] = None
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


# ============================================================================
# OUTPUT SCHEMAS
# ============================================================================


class ModerationSubmissionResponse(BaseResponse):
    """Returned to the user after submitting — and for viewing submission status."""

    model_config = ConfigDict(from_attributes=True)

    target_type: ModerationTargetType
    target_id: int
    status: ModerationStatus
    feedback: Optional[str] = None
    resolution_feedback: Optional[str] = None
    resolved_at: Optional[datetime] = None


class PendingModerationResponse(BaseResponse):
    """Full moderation entry — returned to admins."""

    model_config = ConfigDict(from_attributes=True)

    target_type: ModerationTargetType = Field(
        ..., description="What type of content (item, translation, set)"
    )
    target_id: int = Field(..., description="ID of content being reviewed")
    creator_id: int
    status: ModerationStatus
    feedback: Optional[str] = Field(None, description="Creator's note to reviewer")
    patch_data: dict[str, Any] = Field(..., description="Content snapshot at submission time")
    resolved_at: Optional[datetime] = None
    moderator_id: Optional[int] = None
    resolution_feedback: Optional[str] = None


__all__ = [
    "SubmitForReviewRequest",
    "ApproveModerationRequest",
    "RejectModerationRequest",
    "ModerationListQueryParams",
    "ModerationSubmissionResponse",
    "PendingModerationResponse",
]
