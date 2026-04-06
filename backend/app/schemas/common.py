# backend/app/schemas/common.py
"""Shared schema patterns — Python 3.10+ syntax"""

from datetime import datetime, timezone
from typing import Generic, TypeVar
from pydantic import BaseModel, Field, ConfigDict, model_validator

T = TypeVar("T")


class BaseResponse(BaseModel):
    """Base for all responses"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Unique identifier")
    created_at: datetime = Field(..., description="Creation timestamp (UTC)")


class BaseResponseWithUpdated(BaseResponse):
    """For updatable resources"""

    updated_at: datetime | None = Field(
        None, description="When record was last updated (NULL until first UPDATE)"
    )


class BaseResponseWithDeleted(BaseResponseWithUpdated):
    """For soft-deletable resources"""

    deleted_at: datetime | None = Field(
        None,
        description="Soft-delete timestamp (NULL = active)",
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Paginated list response with auto-computed pagination metadata.

    Computed fields (auto-calculated):
    - pages: Total number of pages
    - has_next: Whether there's a next page
    - has_prev: Whether there's a previous page
    """

    data: list[T] = Field(default_factory=list, description="Items in this page")
    total: int = Field(..., ge=0, description="Total items across all pages")
    page: int = Field(default=1, ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    # Computed fields (not required in input, always present in output)
    pages: int = Field(default=0, ge=0, description="Total number of pages")
    has_next: bool = Field(default=False, description="Whether next page exists")
    has_prev: bool = Field(default=False, description="Whether previous page exists")

    @model_validator(mode="before")
    @classmethod
    def compute_pagination(cls, data):
        """
        Auto-compute pagination metadata before validation.

        This ensures pages, has_next, has_prev are always in sync with
        total, page, page_size — even if someone manually constructs the object.
        """
        if isinstance(data, dict):
            total = data.get("total", 0)
            page = data.get("page", 1)
            page_size = data.get("page_size", 20)

            # Compute derived values
            pages = max(0, (total + page_size - 1) // page_size)
            has_next = page < pages
            has_prev = page > 1

            # Always override with computed values
            data["pages"] = pages
            data["has_next"] = has_next
            data["has_prev"] = has_prev

        return data

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "data": [{"id": 1, "name": "Item 1"}],
                "total": 42,
                "page": 1,
                "page_size": 20,
                "pages": 3,
                "has_next": True,
                "has_prev": False,
            }
        },
    )


class ErrorDetail(BaseModel):
    """Single validation error"""

    field: str
    message: str


class ErrorResponse(BaseModel):
    """Standardized error format"""

    error: str
    message: str
    status_code: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    details: list[ErrorDetail] | None = None
    request_id: str | None = None


class ListQueryParams(BaseModel):
    """Base for query parameters"""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str | None = None


__all__ = [
    "BaseResponse",
    "BaseResponseWithUpdated",
    "BaseResponseWithDeleted",
    "PaginatedResponse",
    "ErrorResponse",
    "ErrorDetail",
    "ListQueryParams",
]
