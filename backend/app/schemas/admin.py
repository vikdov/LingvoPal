# backend/app/schemas/admin.py
"""
Admin-only schemas for system operations.

Restricted to users with is_admin=True
"""

from typing import Optional
from pydantic import BaseModel, Field


class UserListQueryParams(BaseModel):
    """GET /api/v1/admin/users query parameters"""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
    is_admin: Optional[bool] = None
    email_verified: Optional[bool] = None
    search: Optional[str] = Field(None, max_length=100)


class RepairStatsRequest(BaseModel):
    """POST /api/v1/admin/repair-stats"""

    user_id: Optional[int] = Field(
        None, description="Repair for specific user (or all if None)"
    )
    language_id: Optional[int] = Field(None, description="Repair for specific language")


__all__ = [
    "UserListQueryParams",
    "RepairStatsRequest",
]
