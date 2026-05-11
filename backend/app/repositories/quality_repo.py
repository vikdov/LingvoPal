# backend/app/repositories/quality_repo.py
"""ItemQualityMetrics repository — upsert aggregated learning outcome data per item."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_UPSERT_SQL = text("""
INSERT INTO item_quality_metrics (
    item_id,
    learner_count,
    sample_size,
    avg_ease_factor,
    global_success_rate,
    avg_interval,
    updated_at
)
SELECT
    up.item_id,
    COUNT(DISTINCT up.user_id)                                          AS learner_count,
    COUNT(sr.id)                                                        AS sample_size,
    COALESCE(AVG(up.ease_factor), 2.5)                                  AS avg_ease_factor,
    CASE
        WHEN COUNT(sr.id) = 0 THEN 0.0
        ELSE SUM(CASE WHEN sr.was_correct THEN 1 ELSE 0 END)::float
             / COUNT(sr.id)
    END                                                                 AS global_success_rate,
    COALESCE(AVG(up.interval), 0.0)                                     AS avg_interval,
    now()
FROM user_progress up
LEFT JOIN study_reviews sr ON sr.item_id = up.item_id
WHERE up.item_id = :item_id
GROUP BY up.item_id
ON CONFLICT (item_id) DO UPDATE SET
    learner_count        = EXCLUDED.learner_count,
    sample_size          = EXCLUDED.sample_size,
    avg_ease_factor      = EXCLUDED.avg_ease_factor,
    global_success_rate  = EXCLUDED.global_success_rate,
    avg_interval         = EXCLUDED.avg_interval,
    updated_at           = EXCLUDED.updated_at
""")


class QualityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_item_quality(self, item_ids: list[int]) -> None:
        """Recompute and upsert quality metrics for the given items."""
        for item_id in item_ids:
            await self._session.execute(_UPSERT_SQL, {"item_id": item_id})


__all__ = ["QualityRepository"]
