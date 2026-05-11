# backend/app/services/complaint_service.py
"""
Community complaint service.

Anti-gaming guards:
  1. One complaint per (user, target) — UniqueConstraint in DB.
  2. Rate limit: MAX_COMPLAINTS_PER_DAY per user per calendar day.
  3. Activity gate: reporter must have ≥1 completed study session.

Escalation:
  When complaint count on a COMMUNITY item/set reaches COMPLAINT_ESCALATION_THRESHOLD,
  content is auto-reverted to DRAFT and a new PendingModeration entry is created.
"""

from datetime import date, timezone, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import (
    BusinessRuleViolationError,
    NotAuthorizedError,
    ResourceNotFoundError,
)
from app.models.content_complaint import ContentComplaint
from app.models.enums import (
    ComplaintReason,
    ContentStatus,
    ModerationStatus,
    ModerationTargetType,
    SessionStatus,
)
from app.models.study_session import StudySession
from app.repositories.complaint_repo import ComplaintRepository
from app.repositories.item_repo import ItemRepository
from app.repositories.moderation_repo import ModerationRepository
from app.repositories.set_repo import SetRepository

from sqlalchemy import func, select


class ComplaintService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._complaints = ComplaintRepository(session)
        self._items = ItemRepository(session)
        self._sets = SetRepository(session)
        self._mod = ModerationRepository(session)

    async def _has_completed_session(self, user_id: int) -> bool:
        result = await self._session.execute(
            select(func.count()).where(
                StudySession.user_id == user_id,
                StudySession.status == SessionStatus.COMPLETED,
            )
        )
        return result.scalar_one() > 0

    async def file_item_complaint(
        self,
        reporter_id: int,
        item_id: int,
        reason: ComplaintReason,
        details: str | None = None,
    ) -> ContentComplaint:
        settings = get_settings()

        item = await self._items.get_by_id(item_id)
        if not item:
            raise ResourceNotFoundError("Item", item_id)

        # Activity gate
        if not await self._has_completed_session(reporter_id):
            raise NotAuthorizedError("file complaints without completing a study session first")

        # Rate limit
        today = datetime.now(timezone.utc).date()
        daily_count = await self._complaints.count_by_reporter_today(reporter_id, today)
        if daily_count >= settings.MAX_COMPLAINTS_PER_DAY:
            raise BusinessRuleViolationError(
                f"Daily complaint limit of {settings.MAX_COMPLAINTS_PER_DAY} reached"
            )

        # Dedup
        existing = await self._complaints.get_existing(
            reporter_id, ModerationTargetType.ITEM, item_id
        )
        if existing:
            raise BusinessRuleViolationError("You have already reported this item")

        complaint = await self._complaints.create(
            reporter_id=reporter_id,
            target_type=ModerationTargetType.ITEM,
            target_id=item_id,
            reason=reason,
            details=details,
        )

        await self._maybe_escalate_item(item_id, item, settings.COMPLAINT_ESCALATION_THRESHOLD)
        await self._session.commit()
        return complaint

    async def file_set_complaint(
        self,
        reporter_id: int,
        set_id: int,
        reason: ComplaintReason,
        details: str | None = None,
    ) -> ContentComplaint:
        settings = get_settings()

        s = await self._sets.get_by_id(set_id)
        if not s:
            raise ResourceNotFoundError("Set", set_id)

        if not await self._has_completed_session(reporter_id):
            raise NotAuthorizedError("file complaints without completing a study session first")

        today = datetime.now(timezone.utc).date()
        daily_count = await self._complaints.count_by_reporter_today(reporter_id, today)
        if daily_count >= settings.MAX_COMPLAINTS_PER_DAY:
            raise BusinessRuleViolationError(
                f"Daily complaint limit of {settings.MAX_COMPLAINTS_PER_DAY} reached"
            )

        existing = await self._complaints.get_existing(
            reporter_id, ModerationTargetType.SET, set_id
        )
        if existing:
            raise BusinessRuleViolationError("You have already reported this set")

        complaint = await self._complaints.create(
            reporter_id=reporter_id,
            target_type=ModerationTargetType.SET,
            target_id=set_id,
            reason=reason,
            details=details,
        )

        await self._maybe_escalate_set(set_id, s, settings.COMPLAINT_ESCALATION_THRESHOLD)
        await self._session.commit()
        return complaint

    async def _maybe_escalate_item(self, item_id: int, item, threshold: int) -> None:
        count = await self._complaints.count_for_target(ModerationTargetType.ITEM, item_id)
        if count < threshold or item.status != ContentStatus.COMMUNITY:
            return
        await self._items.update_status(item_id, ContentStatus.DRAFT)
        await self._ensure_pending_moderation(ModerationTargetType.ITEM, item_id, item.creator_id)

    async def _maybe_escalate_set(self, set_id: int, s, threshold: int) -> None:
        count = await self._complaints.count_for_target(ModerationTargetType.SET, set_id)
        if count < threshold or s.status != ContentStatus.COMMUNITY:
            return
        await self._sets.update(set_id, status=ContentStatus.DRAFT)
        await self._ensure_pending_moderation(ModerationTargetType.SET, set_id, s.creator_id)

    async def _ensure_pending_moderation(
        self, target_type: ModerationTargetType, target_id: int, creator_id: int | None
    ) -> None:
        existing = await self._mod.get_active_for_target(target_type, target_id)
        if existing:
            return
        if creator_id is None:
            return
        await self._mod.create(
            target_type=target_type,
            target_id=target_id,
            creator_id=creator_id,
            patch_data={"escalated_by": "complaints"},
            feedback="Auto-escalated: complaint threshold reached",
        )


__all__ = ["ComplaintService"]
