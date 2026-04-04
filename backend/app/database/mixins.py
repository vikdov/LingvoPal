# backend/app/database/mixins.py
"""
Shared ORM mixins for common patterns.

Extracted to prevent repetition and ensure consistency across all models.
"""

from datetime import datetime

from sqlalchemy import DateTime, FetchedValue
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class TimestampMixin:
    """
    Automatically manages created_at and updated_at timestamps.

    created_at: Set once at creation (never changes)
    updated_at: Updated on every modification by PostgreSQL trigger

    Uses database time (func.now()) for consistency across distributed systems.

    IMPORTANT: updated_at uses server_onupdate=FetchedValue() so SQLAlchemy
    knows to refresh this field after any UPDATE statement. This is critical
    because the field is updated by a PostgreSQL trigger, not by the ORM.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
        comment="When this record was created (UTC, database time)",
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_onupdate=FetchedValue(),  # ✅ Tells SQLAlchemy: DB manages this, fetch after UPDATE
        nullable=True,
        comment="When this record was last updated (UTC, set by trigger)",
    )


class SoftDeleteMixin:
    """
    Implements soft deletes via deleted_at column.

    Records are marked deleted (deleted_at = NOW()) but not removed from database.
    Queries must filter: WHERE deleted_at IS NULL

    Provides is_deleted property for convenience.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="When this record was soft-deleted (NULL = active)",
    )

    @property
    def is_deleted(self) -> bool:
        """Check if record is soft-deleted"""
        return self.deleted_at is not None


__all__ = ["TimestampMixin", "SoftDeleteMixin"]
