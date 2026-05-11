# backend/app/repositories/complaint_repo.py
"""ContentComplaint repository — raw DB access only. No business logic."""

from collections.abc import Sequence
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_complaint import ContentComplaint
from app.models.enums import ComplaintReason, ModerationTargetType


class ComplaintRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_existing(
        self, reporter_id: int, target_type: ModerationTargetType, target_id: int
    ) -> ContentComplaint | None:
        result = await self._session.execute(
            select(ContentComplaint).where(
                ContentComplaint.reporter_id == reporter_id,
                ContentComplaint.target_type == target_type,
                ContentComplaint.target_id == target_id,
            )
        )
        return result.scalar_one_or_none()

    async def count_by_reporter_today(self, reporter_id: int, today: date) -> int:
        result = await self._session.execute(
            select(func.count()).where(
                ContentComplaint.reporter_id == reporter_id,
                func.date(ContentComplaint.created_at) == today,
            )
        )
        return result.scalar_one()

    async def count_for_target(
        self, target_type: ModerationTargetType, target_id: int
    ) -> int:
        result = await self._session.execute(
            select(func.count()).where(
                ContentComplaint.target_type == target_type,
                ContentComplaint.target_id == target_id,
            )
        )
        return result.scalar_one()

    async def create(
        self,
        reporter_id: int,
        target_type: ModerationTargetType,
        target_id: int,
        reason: ComplaintReason,
        details: str | None,
    ) -> ContentComplaint:
        complaint = ContentComplaint(
            reporter_id=reporter_id,
            target_type=target_type,
            target_id=target_id,
            reason=reason,
            details=details,
        )
        self._session.add(complaint)
        await self._session.flush()
        return complaint

    async def list_all(
        self,
        *,
        target_type: ModerationTargetType | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Sequence[ContentComplaint]:
        stmt = select(ContentComplaint).order_by(ContentComplaint.created_at.desc())
        if target_type is not None:
            stmt = stmt.where(ContentComplaint.target_type == target_type)
        result = await self._session.execute(stmt.offset(skip).limit(limit))
        return result.scalars().all()

    async def count_all(self, *, target_type: ModerationTargetType | None = None) -> int:
        stmt = select(func.count()).select_from(ContentComplaint)
        if target_type is not None:
            stmt = stmt.where(ContentComplaint.target_type == target_type)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def count_for_targets_batch(
        self, target_type: ModerationTargetType, target_ids: list[int]
    ) -> dict[int, int]:
        """Return {target_id: complaint_count} for all given ids."""
        if not target_ids:
            return {}
        result = await self._session.execute(
            select(ContentComplaint.target_id, func.count().label("cnt"))
            .where(
                ContentComplaint.target_type == target_type,
                ContentComplaint.target_id.in_(target_ids),
            )
            .group_by(ContentComplaint.target_id)
        )
        counts = {row.target_id: row.cnt for row in result}
        return {tid: counts.get(tid, 0) for tid in target_ids}


__all__ = ["ComplaintRepository"]
