# backend/app/database/session_utils.py
"""Utilities for refreshing SQLAlchemy instances after database-side writes."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import text


async def refresh_after_trigger_async(
    db_session: AsyncSession, instance, attribute_names: list[str] | None = None
) -> None:
    """Refresh model instance after a database-side write (e.g. updated_at trigger)."""
    await db_session.refresh(instance, attribute_names)


def refresh_after_trigger_sync(
    db_session: Session, instance, attribute_names: list[str] | None = None
) -> None:
    """Synchronous version of refresh_after_trigger_async."""
    db_session.refresh(instance, attribute_names)


async def refresh_related_async(
    db_session: AsyncSession, instance, relationship_names: list[str]
) -> None:
    """Refresh named relationship attributes on an instance."""
    for rel_name in relationship_names:
        if hasattr(instance, rel_name):
            await db_session.refresh(instance, [rel_name])


async def set_db_current_user(session: AsyncSession, user_id: int | str) -> None:
    """
    Injects the current user ID into the PostgreSQL session.
    This allows the audit_log_content_changes() database trigger to record
    who made the INSERT/UPDATE/DELETE.

    Must be called within the active transaction before modifying data.
    """
    # SET LOCAL scopes the variable to the current transaction only
    await session.execute(
        text("SELECT set_config('app.current_user_id', :user_id, true)"),
        {"user_id": str(user_id)},
    )


__all__ = [
    "refresh_after_trigger_async",
    "refresh_after_trigger_sync",
    "refresh_related_async",
    "set_db_current_user",
]
