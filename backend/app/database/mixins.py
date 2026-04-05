# backend/app/database/mixins.py
"""
Shared ORM mixins for common patterns.

Extracted to prevent repetition and ensure consistency across all models.
"""

from datetime import datetime, timezone

from sqlalchemy import FetchedValue
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class CreatedAtMixin:
    """
    Adds only created_at: Set once on INSERT, database-driven.

    Use for immutable or append-only models (e.g., logs, events).
    """

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
        comment="When this record was created (UTC, database time)",
    )


class TimestampMixin(CreatedAtMixin):
    """
    Adds created_at (from CreatedAtMixin) and updated_at.

    Use for models that can be updated after creation.
    """

    # created_at inherited from CreatedAtMixin

    updated_at: Mapped[datetime | None] = mapped_column(
        server_onupdate=FetchedValue(),  # DB manages this, fetch after UPDATE
        nullable=True,
        comment="When this record was last updated (UTC, set by trigger)",
    )


class SoftDeleteTimestampMixin(TimestampMixin):
    """
    Implements soft deletes and TimestampMixin via deleted_at, created_at updated_at columns.

    Records are marked deleted (deleted_at = NOW()) but not removed from database.
    Queries must filter: WHERE deleted_at IS NULL

    Provides is_deleted property for convenience.
    """

    # created_at and updated_at inherited from TimestampMixin

    deleted_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        index=True,
        comment="When this record was soft-deleted (NULL = active)",
    )

    @property
    def is_deleted(self) -> bool:
        """Check if record is soft-deleted"""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark the record as deleted using aware UTC datetime."""
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.deleted_at = None


__all__ = ["CreatedAtMixin", "TimestampMixin", "SoftDeleteTimestampMixin"]
