# backend/app/database/session_utils.py
"""Utilities for refreshing SQLAlchemy instances after database-side writes."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def refresh_related_async(
    db_session: AsyncSession, instance, relationship_names: list[str]
) -> None:
    """Refresh named relationship attributes on an instance in a single round-trip."""
    if not relationship_names:
        return
    await db_session.refresh(instance, relationship_names)


async def set_db_current_user(session: AsyncSession, user_id: int | str) -> None:
    """
    Injects the current user ID into the PostgreSQL session.
    Allows audit_log_content_changes() trigger to record who made the change.
    Must be called within the active transaction before modifying data.
    """
    await session.execute(
        text("SELECT set_config('app.current_user_id', :user_id, true)"),
        {"user_id": str(user_id)},
    )


__all__ = [
    "refresh_related_async",
    "set_db_current_user",
]
