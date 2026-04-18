# backend/app/repositories/moderation_repo.py
"""Moderation repository — raw DB access only. No business logic."""

from datetime import datetime, timezone
from typing import Any, Sequence

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ModerationStatus, ModerationTargetType
from app.models.pending_moderation import PendingModeration


class ModerationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------

    async def get_by_id(self, moderation_id: int) -> PendingModeration | None:
        result = await self._session.execute(
            select(PendingModeration).where(PendingModeration.id == moderation_id)
        )
        return result.scalar_one_or_none()

    async def get_active_for_target(
        self,
        target_type: ModerationTargetType,
        target_id: int,
    ) -> PendingModeration | None:
        """Return the unresolved (PENDING) entry for a given target, if any."""
        result = await self._session.execute(
            select(PendingModeration).where(
                PendingModeration.target_type == target_type,
                PendingModeration.target_id == target_id,
                PendingModeration.status == ModerationStatus.PENDING,
                PendingModeration.resolved_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_creator(
        self,
        creator_id: int,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> Sequence[PendingModeration]:
        result = await self._session.execute(
            select(PendingModeration)
            .where(PendingModeration.creator_id == creator_id)
            .order_by(PendingModeration.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_by_creator(self, creator_id: int) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(PendingModeration)
            .where(PendingModeration.creator_id == creator_id)
        )
        return result.scalar_one()

    async def list_all(
        self,
        *,
        target_type: ModerationTargetType | None = None,
        status: ModerationStatus | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Sequence[PendingModeration]:
        stmt = select(PendingModeration)
        if target_type is not None:
            stmt = stmt.where(PendingModeration.target_type == target_type)
        if status is not None:
            stmt = stmt.where(PendingModeration.status == status)
        result = await self._session.execute(
            stmt.order_by(PendingModeration.created_at.asc()).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def count_all(
        self,
        *,
        target_type: ModerationTargetType | None = None,
        status: ModerationStatus | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(PendingModeration)
        if target_type is not None:
            stmt = stmt.where(PendingModeration.target_type == target_type)
        if status is not None:
            stmt = stmt.where(PendingModeration.status == status)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    async def create(
        self,
        *,
        target_type: ModerationTargetType,
        target_id: int,
        creator_id: int,
        patch_data: dict[str, Any],
        feedback: str | None = None,
    ) -> PendingModeration:
        entry = PendingModeration(
            target_type=target_type,
            target_id=target_id,
            creator_id=creator_id,
            status=ModerationStatus.PENDING,
            patch_data=patch_data,
            feedback=feedback,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def resolve(
        self,
        moderation_id: int,
        *,
        moderator_id: int,
        status: ModerationStatus,
        resolution_feedback: str | None,
    ) -> bool:
        """
        Atomically resolve a PENDING entry.
        The WHERE clause guards against concurrent resolution.
        Returns True if the update succeeded, False if the entry was already resolved.
        """
        result = await self._session.execute(
            update(PendingModeration)
            .where(
                PendingModeration.id == moderation_id,
                PendingModeration.status == ModerationStatus.PENDING,
                PendingModeration.resolved_at.is_(None),
            )
            .values(
                status=status,
                moderator_id=moderator_id,
                resolution_feedback=resolution_feedback,
                resolved_at=datetime.now(timezone.utc),
            )
        )
        return result.rowcount == 1


__all__ = ["ModerationRepository"]
