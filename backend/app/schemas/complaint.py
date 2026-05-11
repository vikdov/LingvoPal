# backend/app/schemas/complaint.py
"""Complaint request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ComplaintReason, ModerationTargetType
from app.schemas.common import BaseResponse


class ComplaintRequest(BaseModel):
    reason: ComplaintReason
    details: str | None = Field(None, max_length=500)


class ComplaintResponse(BaseResponse):
    id: int
    target_type: ModerationTargetType
    target_id: int
    reporter_id: int
    reason: ComplaintReason
    details: str | None
    created_at: datetime
