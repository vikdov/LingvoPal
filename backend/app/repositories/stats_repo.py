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
from app.models.study_review import StudyReview
from app.models.user_daily_stats import UserDailyStats
from app.models.user_stats_total import UserStatsTotal


def interval_to_bucket_key(interval: int) -> str:
    """Map an SM-2 interval (days) to a maturity bucket key."""
    if interval <= 1:
        return "new"
    if interval <= 7:
        return "learning"
    if interval <= 21:
        return "young"
    if interval <= 120:
        return "mature"
    return "long_term"


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
                UserDailyStats.stat_date == datetime.now(timezone.utc).date(),
            )
        )

    async def get_today_stats_batch(
        self, user_id: int, language_ids: list[int]
    ) -> dict[int, UserDailyStats | None]:
        """Today's stats for multiple languages in one query."""
        if not language_ids:
            return {}
        today = datetime.now(timezone.utc).date()
        result = await self._session.execute(
            select(UserDailyStats).where(
                UserDailyStats.user_id == user_id,
                UserDailyStats.language_id.in_(language_ids),
                UserDailyStats.stat_date == today,
            )
        )
        rows = {row.language_id: row for row in result.scalars().all()}
        return {lid: rows.get(lid) for lid in language_ids}

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

    # ── Vocabulary maturity ───────────────────────────────────────────────────

    async def get_vocab_maturity(self, user_id: int, language_id: int) -> dict:
        from app.models.item import Item
        from app.models.user_progress import UserProgress

        now = datetime.now(timezone.utc)
        month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        week_ago = now - timedelta(days=7)

        items_result = await self._session.execute(
            select(UserProgress.item_id, Item.term, UserProgress.interval)
            .join(Item, Item.id == UserProgress.item_id)
            .where(
                UserProgress.user_id == user_id,
                Item.language_id == language_id,
                Item.deleted_at.is_(None),
            )
            .order_by(Item.term.asc())
        )
        items_data = items_result.fetchall()
        total = len(items_data)

        bucket_words: dict[str, list[dict]] = {
            "new": [], "learning": [], "young": [], "mature": [], "long_term": []
        }
        for item_id, term, interval in items_data:
            word = {"item_id": item_id, "term": term, "interval": interval}
            bucket_words[interval_to_bucket_key(interval)].append(word)

        def pct(n: int) -> float:
            return round(n / total * 100, 1) if total else 0.0

        recently_mature = await self._session.scalar(
            select(func.count(func.distinct(StudyReview.item_id))).where(
                StudyReview.user_id == user_id,
                StudyReview.language_id == language_id,
                StudyReview.reviewed_at >= week_ago,
                StudyReview.interval_before < 22,
                StudyReview.interval_after >= 22,
                StudyReview.interval_after.isnot(None),
            )
        )

        recently_long_term = await self._session.scalar(
            select(func.count(func.distinct(StudyReview.item_id))).where(
                StudyReview.user_id == user_id,
                StudyReview.language_id == language_id,
                StudyReview.reviewed_at >= week_ago,
                StudyReview.interval_before < 120,
                StudyReview.interval_after >= 120,
                StudyReview.interval_after.isnot(None),
            )
        )

        first_review_subq = (
            select(
                StudyReview.item_id,
                func.min(StudyReview.reviewed_at).label("first_reviewed"),
            )
            .where(
                StudyReview.user_id == user_id,
                StudyReview.language_id == language_id,
            )
            .group_by(StudyReview.item_id)
            .subquery()
        )
        new_this_month = await self._session.scalar(
            select(func.count())
            .select_from(first_review_subq)
            .where(first_review_subq.c.first_reviewed >= month_start)
        )

        def make_bucket(label: str, key: str, range_: str) -> dict:
            words = bucket_words[key]
            return {
                "label": label, "key": key, "range": range_,
                "count": len(words), "percent": pct(len(words)), "words": words,
            }

        return {
            "total_items": total,
            "buckets": [
                make_bucket("New", "new", "0–1d"),
                make_bucket("Learning", "learning", "2–7d"),
                make_bucket("Young", "young", "8–21d"),
                make_bucket("Mature", "mature", "22–120d"),
                make_bucket("Long-term", "long_term", "120d+"),
            ],
            "recently_mature": recently_mature or 0,
            "recently_long_term": recently_long_term or 0,
            "new_this_month": new_this_month or 0,
        }

    # ── Set context stats ─────────────────────────────────────────────────────

    async def get_set_context(self, user_id: int, set_id: int) -> dict:
        from app.models.item import Item
        from app.models.set_item import SetItem
        from app.models.user_progress import UserProgress

        # All items in the set
        set_items_result = await self._session.execute(
            select(SetItem.item_id).where(SetItem.set_id == set_id)
        )
        all_item_ids = [row[0] for row in set_items_result.fetchall()]
        total_items = len(all_item_ids)

        if total_items == 0:
            return {
                "set_id": set_id,
                "total_items": 0,
                "practiced_items": 0,
                "practiced_percent": 0.0,
                "not_started": 0,
                "maturity_buckets": [],
                "hardest_words": [],
            }

        # User progress for items in this set
        progress_result = await self._session.execute(
            select(UserProgress.item_id, UserProgress.interval)
            .where(
                UserProgress.user_id == user_id,
                UserProgress.item_id.in_(all_item_ids),
            )
        )
        progress_map = {row[0]: row[1] for row in progress_result.fetchall()}
        practiced_items = len(progress_map)
        not_started = total_items - practiced_items

        def pct(n: int) -> float:
            return round(n / total_items * 100, 1) if total_items else 0.0

        # Bucket practiced items (percent of TOTAL set, not just practiced)
        bucket_counts = {"new": 0, "learning": 0, "young": 0, "mature": 0, "long_term": 0}
        for interval in progress_map.values():
            bucket_counts[interval_to_bucket_key(interval)] += 1

        maturity_buckets = [
            {"label": "Not started", "key": "not_started", "count": not_started, "percent": pct(not_started)},
            {"label": "New", "key": "new", "count": bucket_counts["new"], "percent": pct(bucket_counts["new"])},
            {"label": "Learning", "key": "learning", "count": bucket_counts["learning"], "percent": pct(bucket_counts["learning"])},
            {"label": "Young", "key": "young", "count": bucket_counts["young"], "percent": pct(bucket_counts["young"])},
            {"label": "Mature", "key": "mature", "count": bucket_counts["mature"], "percent": pct(bucket_counts["mature"])},
            {"label": "Long-term", "key": "long_term", "count": bucket_counts["long_term"], "percent": pct(bucket_counts["long_term"])},
        ]

        # Hardest words in this set (min 3 reviews, ≥ 25% failure rate)
        total_expr = func.count(StudyReview.id)
        fail_expr = func.sum(
            case((StudyReview.was_correct == False, 1), else_=0)  # noqa: E712
        )
        rate_expr = cast(fail_expr, Float) / total_expr

        hardest_result = await self._session.execute(
            select(
                Item.id.label("item_id"),
                Item.term,
                total_expr.label("total_reviews"),
                rate_expr.label("failure_rate"),
            )
            .join(Item, Item.id == StudyReview.item_id)
            .where(
                StudyReview.user_id == user_id,
                StudyReview.set_id == set_id,
                Item.deleted_at.is_(None),
            )
            .group_by(Item.id, Item.term)
            .having(total_expr >= 3, rate_expr >= 0.25)
            .order_by(rate_expr.desc())
            .limit(5)
        )
        hardest_words = [
            {
                "item_id": row.item_id,
                "term": row.term,
                "total_reviews": row.total_reviews,
                "failure_rate": round(float(row.failure_rate), 4),
            }
            for row in hardest_result.fetchall()
        ]

        return {
            "set_id": set_id,
            "total_items": total_items,
            "practiced_items": practiced_items,
            "practiced_percent": pct(practiced_items),
            "not_started": not_started,
            "maturity_buckets": maturity_buckets,
            "hardest_words": hardest_words,
        }

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
