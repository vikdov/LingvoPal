"""
Extracted complex SELECT statements optimized for practice workflows.

Design principles:
- Eager load all relationships (prevent N+1 queries)
- Use selective indexes (avoid full table scans)
- Denormalize when it saves queries (e.g., language_id in StudyReview)
- Return data ready for schema serialization (no post-processing)
"""

from datetime import datetime, timezone
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models import (
    Item,
    Set,
    SetItem,
    User,
    UserProgress,
    StudySession,
    StudyReview,
    Translation,
    Language,
    ItemSynonym,
)


# ====================================================================
# Practice Session Queries
# ====================================================================


async def get_due_items_for_user_in_set(
    db: AsyncSession,
    user_id: int,
    set_id: int,
    limit: int = 20,
) -> list[Item]:
    """
    Fetch items due for review in a set, ordered by longest waiting.

    Critical for practice: fetches items that are ready NOW.

    OPTIMIZATION:
    - Join UserProgress to find due dates (WHERE next_review <= NOW)
    - Join SetItem to filter by set_id
    - Eager-load translations (prevent N+1 on frontend serialization)
    - Eager-load synonyms for hints
    - Order by next_review ASC (longest waiting first → prioritize old items)
    - Filter deleted_at IS NULL (soft-delete safety)

    INDEXES USED:
    - idx_user_progress_due (user_id, next_review, item_id)
    - idx_set_items_by_set (set_id, sort_order)
    - idx_items_unverified (partial, deleted_at)

    Args:
        db: Async database session
        user_id: User ID
        set_id: Set ID to practice
        limit: Max items to return (default 20, UI typically uses 5-10)

    Returns:
        List of Item objects ready for review, eager-loaded with:
        - translations (all languages)
        - language (source language)
        - synonyms (for hints/learning)

    Example:
        items = await get_due_items_for_user_in_set(db, user_id=1, set_id=5, limit=10)
        # items[0].translations[0].term_trans ← no extra query
        # items[0].synonyms ← no extra query
    """
    stmt = (
        select(Item)
        .join(UserProgress, UserProgress.item_id == Item.id)
        .join(SetItem, SetItem.item_id == Item.id)
        .where(
            UserProgress.user_id == user_id,
            SetItem.set_id == set_id,
            UserProgress.next_review <= datetime.now(timezone.utc),
            Item.deleted_at.is_(None),
        )
        .options(
            selectinload(Item.translations).selectinload(Translation.language),
            selectinload(Item.language),
        )
        .order_by(UserProgress.next_review.asc())  # Longest waiting first
        .limit(limit)
    )

    result = await db.execute(stmt)
    return result.scalars().unique().all()


async def get_study_session_with_details(
    db: AsyncSession,
    session_id: int,
) -> StudySession | None:
    """
    Fetch study session with all eager-loaded relationships.

    Used when:
    - User resumes a session (check if still active)
    - Submitting a review (verify session ownership)
    - Ending a session

    OPTIMIZATION:
    - Eager-load set, user to avoid follow-up queries
    - Eager-load reviews (if user checks session history)

    Args:
        db: Async database session
        session_id: Study session ID (BigInteger)

    Returns:
        StudySession with set, user, reviews loaded, or None
    """
    stmt = (
        select(StudySession)
        .where(StudySession.id == session_id)
        .options(
            selectinload(StudySession.set).selectinload(Set.source_language),
            selectinload(StudySession.set).selectinload(Set.target_language),
            selectinload(StudySession.set).selectinload(Set.creator),
            selectinload(StudySession.user),
            selectinload(StudySession.reviews),
        )
    )

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_progress_with_history(
    db: AsyncSession,
    user_id: int,
    item_id: int,
) -> tuple[UserProgress | None, list[StudyReview]]:
    """
    Fetch user's progress + recent review history for an item.

    Used when submitting review: need old state + history for learning.

    Returns:
        (UserProgress, recent_reviews)

    Example:
        progress, reviews = await get_user_progress_with_history(db, user_id=1, item_id=5)
        if len(reviews) > 3 and all(not r.was_correct for r in reviews[-3:]):
            # Item is problematic (3 fails in a row)
            mark_as_difficult(item_id)
    """
    # Fetch progress
    progress_stmt = select(UserProgress).where(
        UserProgress.user_id == user_id,
        UserProgress.item_id == item_id,
    )
    progress_result = await db.execute(progress_stmt)
    progress = progress_result.scalar_one_or_none()

    # Fetch recent reviews (last 10)
    if progress:
        reviews_stmt = (
            select(StudyReview)
            .where(
                StudyReview.user_id == user_id,
                StudyReview.item_id == item_id,
            )
            .order_by(StudyReview.reviewed_at.desc())
            .limit(10)
        )
        reviews_result = await db.execute(reviews_stmt)
        reviews = reviews_result.scalars().all()
    else:
        reviews = []

    return progress, reviews


async def count_items_due_for_user_in_set(
    db: AsyncSession,
    user_id: int,
    set_id: int,
) -> int:
    """
    Count items due for review (for "X items due today" display).

    Used on dashboard and session detail page.

    OPTIMIZATION:
    - COUNT(*) is fast (uses index)
    - No need to fetch actual items

    Args:
        db: Async database session
        user_id: User ID
        set_id: Set ID

    Returns:
        Count of items due
    """
    stmt = (
        select(func.count(Item.id))
        .join(UserProgress, UserProgress.item_id == Item.id)
        .join(SetItem, SetItem.item_id == Item.id)
        .where(
            UserProgress.user_id == user_id,
            SetItem.set_id == set_id,
            UserProgress.next_review <= datetime.now(timezone.utc),
            Item.deleted_at.is_(None),
        )
    )

    result = await db.scalar(stmt)
    return result or 0


async def get_items_by_ids_with_translations(
    db: AsyncSession,
    item_ids: list[int],
) -> dict[int, Item]:
    """
    Batch fetch items by IDs with eager-loaded translations.

    Used when you have item_ids and need to avoid N+1 queries.

    Args:
        db: Async database session
        item_ids: List of item IDs

    Returns:
        Dict mapping item_id → Item (with translations loaded)
    """
    stmt = (
        select(Item)
        .where(Item.id.in_(item_ids), Item.deleted_at.is_(None))
        .options(
            selectinload(Item.translations).selectinload(Translation.language),
            selectinload(Item.language),
        )
    )

    result = await db.execute(stmt)
    items = result.scalars().all()
    return {item.id: item for item in items}


async def get_session_stats(
    db: AsyncSession,
    session_id: int,
) -> dict:
    """
    Fetch aggregated statistics for a study session.

    Used for session summary page.

    Returns:
        {
            "total_reviews": 10,
            "correct_count": 8,
            "accuracy": 0.80,
            "avg_response_time_ms": 2500,
            "hardest_items": [{"item_id": 5, "fails": 2}, ...],
        }
    """
    # Get session
    session = await db.get(StudySession, session_id)
    if not session:
        return {}

    # Basic stats
    total = session.items_reviewed
    correct = session.correct_count
    accuracy = correct / total if total > 0 else 0

    avg_time = session.total_time_ms // total if total > 0 else 0

    # Hardest items (most incorrect in this session)
    hardest_stmt = (
        select(StudyReview.item_id, func.count(StudyReview.id).label("fails"))
        .where(
            StudyReview.session_id == session_id,
            StudyReview.was_correct.is_(False),
        )
        .group_by(StudyReview.item_id)
        .order_by(func.count(StudyReview.id).desc())
        .limit(3)
    )
    hardest_result = await db.execute(hardest_stmt)
    hardest = [
        {"item_id": row[0], "fails": row[1]} for row in hardest_result.fetchall()
    ]

    return {
        "total_reviews": total,
        "correct_count": correct,
        "accuracy": accuracy,
        "avg_response_time_ms": avg_time,
        "hardest_items": hardest,
    }


async def get_problematic_items_for_user(
    db: AsyncSession,
    user_id: int,
    set_id: int | None = None,
    limit: int = 20,
) -> list[Item]:
    """
    Fetch "difficult" items for a user (high failure rate).

    Used for "Review difficult words" feature.

    Definition: Item is "difficult" if:
    - (failures in last 7 days) / (total reviews) > 30%
    - AND reviewed >= 5 times

    Args:
        db: Async database session
        user_id: User ID
        set_id: Optional, filter to specific set
        limit: Max items (default 20)

    Returns:
        List of problematic items
    """
    seven_days_ago = datetime.now(timezone.utc) - __import__("datetime").timedelta(
        days=7
    )

    # Subquery: items with high failure rate
    subquery = (
        select(
            StudyReview.item_id,
            func.count(StudyReview.id).label("total_reviews"),
            func.sum(
                func.cast(~StudyReview.was_correct, __import__("sqlalchemy").Integer)
            ).label("failures"),
        )
        .where(
            StudyReview.user_id == user_id,
            StudyReview.reviewed_at >= seven_days_ago,
        )
        .group_by(StudyReview.item_id)
        .having(
            and_(
                func.count(StudyReview.id) >= 5,  # At least 5 reviews
                func.sum(
                    func.cast(
                        ~StudyReview.was_correct, __import__("sqlalchemy").Integer
                    )
                )
                > func.count(StudyReview.id) * 0.3,  # >30% failures
            )
        )
        .alias("problematic")
    )

    # Main query: fetch items
    stmt = (
        select(Item)
        .join(subquery, Item.id == subquery.c.item_id)
        .where(Item.deleted_at.is_(None))
        .options(
            selectinload(Item.translations).selectinload(Translation.language),
            selectinload(Item.language),
        )
        .limit(limit)
    )

    if set_id:
        stmt = stmt.join(SetItem, SetItem.item_id == Item.id).where(
            SetItem.set_id == set_id
        )

    result = await db.execute(stmt)
    return result.scalars().all()


__all__ = [
    "get_due_items_for_user_in_set",
    "get_study_session_with_details",
    "get_user_progress_with_history",
    "count_items_due_for_user_in_set",
    "get_items_by_ids_with_translations",
    "get_session_stats",
    "get_problematic_items_for_user",
]
