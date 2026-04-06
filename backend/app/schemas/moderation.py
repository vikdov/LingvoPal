# backend/app/schemas/moderation.py
"""
Content moderation schemas.

Workflow:
1. User creates content (auto-private)
2. Content marked for review (PENDING_REVIEW status)
3. Admin approves or rejects
4. If approved → becomes public or official
"""

from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

from app.models.enums import ModerationTargetType
from app.schemas.common import BaseResponse


# ============================================================================
# INPUT SCHEMAS
# ============================================================================


class ApproveModerationRequest(BaseModel):
    """POST /api/v1/admin/moderation/{moderation_id}/approve"""

    resolution_feedback: Optional[str] = Field(
        None, max_length=1000, description="Reason for approval"
    )


class RejectModerationRequest(BaseModel):
    """POST /api/v1/admin/moderation/{moderation_id}/reject"""

    resolution_feedback: str = Field(
        ..., max_length=1000, description="Reason for rejection (required)"
    )


# ============================================================================
# OUTPUT SCHEMAS
# ============================================================================


class PendingModerationResponse(BaseResponse):
    """Item pending moderator review"""

    target_type: ModerationTargetType = Field(
        ..., description="What type of content (item, translation, set)"
    )
    target_id: int = Field(..., description="ID of content being reviewed")
    creator_id: int
    feedback: Optional[str] = Field(None, description="Creator's feedback")
    patch_data: dict[str, Any] = Field(..., description="What changed (diff)")
    resolved_at: Optional[datetime] = None
    moderator_id: Optional[int] = None
    resolution_feedback: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "ApproveModerationRequest",
    "RejectModerationRequest",
    "PendingModerationResponse",
]
