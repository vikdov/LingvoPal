# backend/app/database/session_utils.py
"""
Utilities for working with triggers and database-computed values.

Because SQLAlchemy is unaware of database triggers that update other tables,
you must explicitly refresh related objects after inserts that trigger cascading updates.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import text


async def refresh_after_trigger_async(
    db_session: AsyncSession, instance, attribute_names: list[str] | None = None
) -> None:
    """
    Refresh model instance attributes after database trigger updates.

    Use this after inserting a StudyReview, which triggers sync to UserDailyStats.

    Args:
        db_session: SQLAlchemy async session
        instance: Model instance to refresh
        attribute_names: Specific attributes to refresh (None = all)

    Example:
        review = StudyReview(user_id=1, item_id=5, ...)
        db.add(review)
        await db.commit()
        await refresh_after_trigger_async(db, review)
        # Now review attributes are fresh
    """
    await db_session.refresh(instance, attribute_names)


def refresh_after_trigger_sync(
    db_session: Session, instance, attribute_names: list[str] | None = None
) -> None:
    """
    Synchronous version of refresh_after_trigger_async.
    """
    db_session.refresh(instance, attribute_names)


async def refresh_related_async(
    db_session: AsyncSession, instance, relationship_names: list[str]
) -> None:
    """
    Refresh related objects after trigger updates.

    Use this to re-fetch UserDailyStats/UserStatsTotal after StudyReview insert.

    Args:
        db_session: SQLAlchemy async session
        instance: Model instance
        relationship_names: Relationship attributes to refresh

    Example:
        await refresh_related_async(db, study_session, ["user_daily_stats"])
    """
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
    await session.execute(text(f"SET LOCAL app.current_user_id = '{user_id}'"))


__all__ = [
    "refresh_after_trigger_async",
    "refresh_after_trigger_sync",
    "refresh_related_async",
    "set_db_current_user",
]
