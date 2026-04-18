# backend/app/routes/stats.py
"""
Study statistics routes.

All data is read-only: stats are written during session finalisation
by ProgressUpdater.finalise_batch().
"""

from datetime import date

from fastapi import APIRouter, HTTPException, Query, status

from app.core.dependencies import StatsServiceDep
from app.core.exceptions import ResourceNotFoundError

router = APIRouter(prefix="/stats", tags=["stats"])


# ============================================================================
# Endpoints
# ============================================================================


@router.get(
    "/overview",
    summary="Dashboard overview — streaks, today's stats, items due",
)
async def get_overview(svc: StatsServiceDep) -> dict:
    """
    Return a quick summary suitable for a home-screen dashboard:
      - Per-language streak + today's activity
      - Total items due for review right now (all languages combined)
    """
    return await svc.get_overview()


@router.get(
    "/totals",
    summary="Lifetime totals per language",
)
async def get_totals(svc: StatsServiceDep) -> list[dict]:
    """
    Aggregate lifetime stats for each language the user has studied.
    Each entry includes total words, total hours, and current streak.
    """
    return await svc.get_total_stats()


@router.get(
    "/streak",
    summary="Current streak for a language",
)
async def get_streak(
    svc: StatsServiceDep,
    language_id: int = Query(..., gt=0),
) -> dict:
    """Consecutive days studied for the given language (0 if broken)."""
    try:
        return await svc.get_streak(language_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/daily",
    summary="Paginated daily stats for a language",
)
async def get_daily_stats(
    svc: StatsServiceDep,
    language_id: int = Query(..., gt=0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=30, ge=1, le=365),
) -> list[dict]:
    """
    Daily stats for a language, newest first.
    Each entry has correct/incorrect counts, accuracy, seconds spent.
    """
    try:
        return await svc.get_daily_stats(language_id, page=page, page_size=page_size)
    except ResourceNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/hardest-items",
    summary="Items with highest failure rate (leech candidates)",
)
async def get_hardest_items(
    svc: StatsServiceDep,
    language_id: int = Query(..., gt=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[dict]:
    """
    Returns up to `limit` items with the highest failure rate for the given
    language (minimum 5 reviews, ≥ 30% failure rate).
    """
    try:
        return await svc.get_hardest_items(language_id, limit=limit)
    except ResourceNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/range",
    summary="Aggregated stats over a date range",
)
async def get_range_stats(
    svc: StatsServiceDep,
    language_id: int = Query(..., gt=0),
    start_date: date = Query(...),
    end_date: date = Query(...),
) -> dict:
    """
    Aggregated + daily breakdown for [start_date, end_date] (max 365 days).

    Response includes daily list plus roll-up totals (accuracy, hours, etc.).
    """
    try:
        return await svc.get_range_stats(language_id, start_date, end_date)
    except ResourceNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
