# backend/app/repositories/stats_repo.py
"""
Stats repository — raw DB access only.

No business logic. No defaults. No computed fields.
All computation happens in the service layer.
"""

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import Float, case, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import Item
from app.models.user_daily_stats import UserDailyStats
from app.models.user_stats_total import UserStatsTotal
from app.models.study_review import StudyReview


class StatsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Daily stats ──────────────────────────────────────────────────────────

    async def get_daily_stats(
        self,
        user_id: int,
        language_id: int,
        *,
        limit: int = 30,
        offset: int = 0,
    ) -> list[UserDailyStats]:
        """Most-recent daily stats first (DESC), paginated."""
        result = await self._session.execute(
            select(UserDailyStats)
            .where(
                UserDailyStats.user_id == user_id,
                UserDailyStats.language_id == language_id,
            )
            .order_by(UserDailyStats.stat_date.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_daily_stats_range(
        self,
        user_id: int,
        language_id: int,
        start_date: date,
        end_date: date,
    ) -> list[UserDailyStats]:
        """All daily stats within [start_date, end_date], ordered ASC."""
        result = await self._session.execute(
            select(UserDailyStats)
            .where(
                UserDailyStats.user_id == user_id,
                UserDailyStats.language_id == language_id,
                UserDailyStats.stat_date >= start_date,
                UserDailyStats.stat_date <= end_date,
            )
            .order_by(UserDailyStats.stat_date.asc())
        )
        return list(result.scalars().all())

    async def get_today_stats(
        self, user_id: int, language_id: int
    ) -> UserDailyStats | None:
        return await self._session.scalar(
            select(UserDailyStats).where(
                UserDailyStats.user_id == user_id,
                UserDailyStats.language_id == language_id,
                UserDailyStats.stat_date == date.today(),
            )
        )

    # ── Lifetime totals ──────────────────────────────────────────────────────

    async def get_total_stats(self, user_id: int) -> list[UserStatsTotal]:
        """All lifetime stats rows for a user (one per language they've studied)."""
        result = await self._session.execute(
            select(UserStatsTotal)
            .where(UserStatsTotal.user_id == user_id)
            .order_by(UserStatsTotal.language_id.asc())
        )
        return list(result.scalars().all())

    async def get_total_stats_for_language(
        self, user_id: int, language_id: int
    ) -> UserStatsTotal | None:
        return await self._session.scalar(
            select(UserStatsTotal).where(
                UserStatsTotal.user_id == user_id,
                UserStatsTotal.language_id == language_id,
            )
        )

    # ── Streak ────────────────────────────────────────────────────────────────

    async def get_streak(self, user_id: int, language_id: int) -> int:
        """
        Current consecutive-day study streak for (user, language).

        Counts backward from today: a day counts if it has at least one review
        (correct + incorrect > 0) in user_daily_stats.

        Returns 0 if the user hasn't studied today or yesterday.
        """
        streaks = await self.get_streak_batch(user_id, [language_id])
        return streaks.get(language_id, 0)

    async def get_streak_batch(
        self, user_id: int, language_ids: list[int]
    ) -> dict[int, int]:
        """
        Current consecutive-day streaks for multiple languages in one query.

        Returns a dict mapping language_id → streak_days (0 if broken/never studied).
        """
        if not language_ids:
            return {}

        today = date.today()
        result = await self._session.execute(
            select(
                UserDailyStats.language_id,
                UserDailyStats.stat_date,
                UserDailyStats.correct_count,
                UserDailyStats.incorrect_count,
            )
            .where(
                UserDailyStats.user_id == user_id,
                UserDailyStats.language_id.in_(language_ids),
            )
            .order_by(UserDailyStats.stat_date.desc())
        )
        rows = result.fetchall()

        by_lang: dict[int, set[date]] = {}
        for lang_id in language_ids:
            by_lang[lang_id] = set()
        for row in rows:
            if (row.correct_count + row.incorrect_count) > 0:
                by_lang[row.language_id].add(row.stat_date)

        streaks: dict[int, int] = {}
        yesterday = today - timedelta(days=1)
        for lang_id in language_ids:
            active_dates = by_lang[lang_id]
            if today in active_dates:
                start = today
            elif yesterday in active_dates:
                start = yesterday
            else:
                streaks[lang_id] = 0
                continue

            count = 0
            current = start
            while current in active_dates:
                count += 1
                current -= timedelta(days=1)
            streaks[lang_id] = count

        return streaks

    # ── Active languages ──────────────────────────────────────────────────────

    async def get_studied_language_ids(self, user_id: int) -> list[int]:
        """Languages the user has at least one daily-stats row for."""
        result = await self._session.execute(
            select(UserDailyStats.language_id)
            .where(UserDailyStats.user_id == user_id)
            .distinct()
            .order_by(UserDailyStats.language_id.asc())
        )
        return [row[0] for row in result.fetchall()]

    # ── Reviews due today ─────────────────────────────────────────────────────

    async def count_due_now(self, user_id: int) -> int:
        """Total items due for review right now across all sets."""
        from app.models.user_progress import UserProgress

        now = datetime.now(timezone.utc)
        result = await self._session.scalar(
            select(func.count(UserProgress.item_id)).where(
                UserProgress.user_id == user_id,
                UserProgress.next_review <= now,
            )
        )
        return result or 0

    # ── Hardest items ─────────────────────────────────────────────────────────

    async def get_hardest_items(
        self,
        user_id: int,
        language_id: int,
        *,
        limit: int = 20,
        min_reviews: int = 5,
        failure_threshold: float = 0.3,
    ) -> list[dict]:
        """Items with highest failure rate, filtered by min review count."""
        total_expr = func.count(StudyReview.id)
        fail_expr = func.sum(
            case((StudyReview.was_correct == False, 1), else_=0)  # noqa: E712
        )
        rate_expr = cast(fail_expr, Float) / total_expr

        result = await self._session.execute(
            select(
                Item.id.label("item_id"),
                Item.term,
                Item.language_id,
                total_expr.label("total_reviews"),
                rate_expr.label("failure_rate"),
            )
            .join(Item, Item.id == StudyReview.item_id)
            .where(
                StudyReview.user_id == user_id,
                StudyReview.language_id == language_id,
                Item.deleted_at.is_(None),
            )
            .group_by(Item.id, Item.term, Item.language_id)
            .having(
                total_expr >= min_reviews,
                rate_expr >= failure_threshold,
            )
            .order_by(rate_expr.desc())
            .limit(limit)
        )
        return [
            {
                "item_id": row.item_id,
                "term": row.term,
                "language_id": row.language_id,
                "total_reviews": row.total_reviews,
                "failure_rate": round(float(row.failure_rate), 4),
            }
            for row in result.fetchall()
        ]


__all__ = ["StatsRepository"]
