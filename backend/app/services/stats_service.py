# backend/app/services/stats_service.py
"""
Stats service — aggregation and query logic for study statistics.

Reads from user_daily_stats and user_stats_total tables which are
populated by ProgressUpdater.finalise_batch() during session finalization.

No writes happen here.
"""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError
from app.models.language import Language
from app.models.user_daily_stats import UserDailyStats
from app.repositories.stats_repo import StatsRepository


class StatsService:
    def __init__(self, session: AsyncSession, user_id: int) -> None:
        self._session = session
        self._user_id = user_id
        self._repo = StatsRepository(session)

    # ── Overview (dashboard) ─────────────────────────────────────────────────

    async def get_overview(self) -> dict:
        """
        Return a dashboard overview for the authenticated user.

        Includes:
          - Languages studied (with per-language streak)
          - Today's aggregate stats across all languages
          - Total items due for review right now
        """
        lang_ids = await self._repo.get_studied_language_ids(self._user_id)

        # Load language names in one query
        if lang_ids:
            lang_result = await self._session.execute(
                select(Language).where(Language.id.in_(lang_ids))
            )
            lang_map = {lang.id: lang for lang in lang_result.scalars()}
        else:
            lang_map = {}

        streaks = await self._repo.get_streak_batch(self._user_id, lang_ids)
        today_stats = await self._repo.get_today_stats_batch(self._user_id, lang_ids)

        # Per-language: today's stats + streak
        languages_overview = []
        for lang_id in lang_ids:
            today = today_stats.get(lang_id)
            streak = streaks.get(lang_id, 0)
            lang = lang_map.get(lang_id)
            languages_overview.append(
                {
                    "language_id": lang_id,
                    "language_code": lang.code if lang else None,
                    "language_name": lang.name if lang else None,
                    "streak_days": streak,
                    "today_correct": today.correct_count if today else 0,
                    "today_incorrect": today.incorrect_count if today else 0,
                    "today_new_words": today.new_words_count if today else 0,
                    "today_minutes": (
                        round(float(today.seconds_spent) / 60, 1) if today else 0.0
                    ),
                }
            )

        due_count = await self._repo.count_due_now(self._user_id)

        return {
            "languages": languages_overview,
            "total_due_now": due_count,
        }

    # ── Daily stats (paginated) ───────────────────────────────────────────────

    async def get_daily_stats(
        self,
        language_id: int,
        *,
        page: int = 1,
        page_size: int = 30,
    ) -> list[dict]:
        """Paginated list of daily stats for one language, newest first."""
        await self._assert_language_exists(language_id)

        offset = (page - 1) * page_size
        rows = await self._repo.get_daily_stats(
            self._user_id, language_id, limit=page_size, offset=offset
        )
        return [_daily_to_dict(r) for r in rows]

    # ── Date-range stats ─────────────────────────────────────────────────────

    async def get_range_stats(
        self,
        language_id: int,
        start_date: date,
        end_date: date,
    ) -> dict:
        """
        Aggregated stats for [start_date, end_date].

        Days with no activity are NOT included in the list (sparse).
        Summary totals cover the whole range.
        """
        if end_date < start_date:
            start_date, end_date = end_date, start_date

        max_range_days = 365
        if (end_date - start_date).days > max_range_days:
            start_date = end_date - timedelta(days=max_range_days)

        await self._assert_language_exists(language_id)

        rows = await self._repo.get_daily_stats_range(
            self._user_id, language_id, start_date, end_date
        )

        daily = [_daily_to_dict(r) for r in rows]
        total_correct = sum(r["correct_count"] for r in daily)
        total_incorrect = sum(r["incorrect_count"] for r in daily)
        total_reviews = total_correct + total_incorrect
        total_seconds = sum(r["seconds_spent"] for r in daily)
        days_active = sum(1 for r in daily if r["total_reviews"] > 0)

        return {
            "language_id": language_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days_active": days_active,
            "total_correct": total_correct,
            "total_incorrect": total_incorrect,
            "total_reviews": total_reviews,
            "accuracy_percent": (
                round(total_correct / total_reviews * 100, 2) if total_reviews else 0.0
            ),
            "total_hours": round(total_seconds / 3600, 2),
            "avg_reviews_per_day": (
                round(total_reviews / days_active, 2) if days_active else 0.0
            ),
            "daily": daily,
        }

    # ── Lifetime totals ──────────────────────────────────────────────────────

    async def get_total_stats(self) -> list[dict]:
        """
        Lifetime aggregates for each language the user has studied.

        Also injects the current streak for each language.
        """
        rows = await self._repo.get_total_stats(self._user_id)

        # Load language names
        lang_ids = [r.language_id for r in rows]
        lang_map: dict[int, Language] = {}
        if lang_ids:
            lang_result = await self._session.execute(
                select(Language).where(Language.id.in_(lang_ids))
            )
            lang_map = {lang.id: lang for lang in lang_result.scalars()}

        streaks = await self._repo.get_streak_batch(self._user_id, lang_ids)

        result = []
        for row in rows:
            streak = streaks.get(row.language_id, 0)
            lang = lang_map.get(row.language_id)
            result.append(
                {
                    "language_id": row.language_id,
                    "language_code": lang.code if lang else None,
                    "language_name": lang.name if lang else None,
                    "total_words_learned": row.total_words,
                    "total_hours": round(float(row.total_seconds) / 3600, 2),
                    "streak_days": streak,
                    "last_recalculated_at": (
                        row.last_recalculated_at.isoformat() if row.last_recalculated_at else None
                    ),
                }
            )

        return result

    # ── Hardest items ─────────────────────────────────────────────────────────

    async def get_hardest_items(
        self,
        language_id: int,
        *,
        limit: int = 20,
    ) -> list[dict]:
        await self._assert_language_exists(language_id)
        return await self._repo.get_hardest_items(
            self._user_id, language_id, limit=limit
        )

    # ── Streak ────────────────────────────────────────────────────────────────

    async def get_streak(self, language_id: int) -> dict:
        await self._assert_language_exists(language_id)
        streak = await self._repo.get_streak(self._user_id, language_id)
        return {"language_id": language_id, "streak_days": streak}

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _assert_language_exists(self, language_id: int) -> None:
        result = await self._session.execute(
            select(Language.id).where(Language.id == language_id)
        )
        if result.scalar_one_or_none() is None:
            raise ResourceNotFoundError("Language", language_id)


# ============================================================================
# Pure serialisation helpers
# ============================================================================


def _daily_to_dict(row: UserDailyStats) -> dict:
    correct = row.correct_count
    incorrect = row.incorrect_count
    total = correct + incorrect
    return {
        "stat_date": row.stat_date.isoformat(),
        "language_id": row.language_id,
        "correct_count": correct,
        "incorrect_count": incorrect,
        "total_reviews": total,
        "new_words_count": row.new_words_count,
        "seconds_spent": float(row.seconds_spent),
        "accuracy_percent": (round(correct / total * 100, 2) if total else 0.0),
    }


__all__ = ["StatsService"]
