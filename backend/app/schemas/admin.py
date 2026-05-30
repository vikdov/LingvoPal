# backend/app/schemas/admin.py
"""
Admin-only schemas for system operations.

Restricted to users with is_admin=True
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class UserListQueryParams(BaseModel):
    """GET /api/v1/admin/users query parameters"""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
    is_admin: bool | None = None
    email_verified: bool | None = None
    search: str | None = Field(None, max_length=100)


class RepairStatsRequest(BaseModel):
    """POST /api/v1/admin/repair-stats"""

    user_id: int | None = Field(None, description="Repair for specific user (or all if None)")
    language_id: int | None = Field(None, description="Repair for specific language")


class AdminDeleteContentRequest(BaseModel):
    """DELETE (via POST body) /api/v1/admin/items/{id} or /sets/{id}"""

    reason: str = Field(
        ..., min_length=1, max_length=500, description="Reason for removal (shown to creator)"
    )


class PromoteToOfficialRequest(BaseModel):
    """POST /api/v1/admin/items/{item_id}/promote"""

    override: bool = Field(
        False,
        description="Bypass quality threshold checks and force promotion",
    )


class AdminOverviewStats(BaseModel):
    community_count: int
    pending_queue_count: int
    total_complaints: int


class AuditLogEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    table_name: str
    record_id: int
    action: str
    old_values: dict[str, Any] | None
    new_values: dict[str, Any] | None
    user_id: int | None


__all__ = [
    "UserListQueryParams",
    "RepairStatsRequest",
    "AdminDeleteContentRequest",
    "PromoteToOfficialRequest",
    "AdminOverviewStats",
    "AuditLogEntry",
]
