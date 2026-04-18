# backend/app/services/moderation_service.py
"""
Moderation service — workflow for submitting and reviewing content.

State machine:
  DRAFT           → submit()   → PENDING_REVIEW  (content status)
  PENDING_REVIEW  → approve()  → APPROVED        (content status)
  PENDING_REVIEW  → reject()   → DRAFT           (content status)
  DRAFT           → submit()   → PENDING_REVIEW  (resubmit after rejection)

PendingModeration entry:
  PENDING  → approve() → APPROVED (resolved_at set)
  PENDING  → reject()  → REJECTED (resolved_at set)
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BusinessRuleViolationError,
    ConcurrencyError,
    InvalidStateTransitionError,
    NotAuthorizedError,
    ResourceNotFoundError,
)
from app.models.enums import ContentStatus, ModerationStatus, ModerationTargetType
from app.models.pending_moderation import PendingModeration
from app.repositories.item_repo import ItemRepository
from app.repositories.moderation_repo import ModerationRepository
from app.repositories.set_repo import SetRepository

_SUBMITTABLE_STATUSES = (ContentStatus.DRAFT,)


def _set_snapshot(s) -> dict:
    return {
        "title": s.title,
        "description": s.description,
        "difficulty": s.difficulty,
        "source_lang_id": s.source_lang_id,
        "target_lang_id": s.target_lang_id,
        "status": s.status.value,
    }


def _item_snapshot(item) -> dict:
    return {
        "term": item.term,
        "language_id": item.language_id,
        "context": item.context,
        "difficulty": item.difficulty,
        "part_of_speech": item.part_of_speech.value if item.part_of_speech else None,
        "lemma": item.lemma,
        "status": item.status.value,
    }


class ModerationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._mod = ModerationRepository(session)
        self._sets = SetRepository(session)
        self._items = ItemRepository(session)

    # ------------------------------------------------------------------
    # USER: Submit for review
    # ------------------------------------------------------------------

    async def submit_set(
        self, user_id: int, set_id: int, feedback: str | None = None
    ) -> PendingModeration:
        """
        Submit a set for moderation.

        Rules:
        - User must own the set.
        - Set must be in DRAFT status (includes post-rejection resubmit).
        - If an active PENDING entry exists for this set, it is replaced.
        """
        s = await self._sets.get_by_id(set_id)
        if not s:
            raise ResourceNotFoundError("Set", set_id)
        if s.creator_id != user_id:
            raise NotAuthorizedError("submit this set for review")
        if s.status not in _SUBMITTABLE_STATUSES:
            raise InvalidStateTransitionError(s.status.value, ContentStatus.PENDING_REVIEW.value)

        # Cancel any existing active entry for this target (upsert semantics)
        existing = await self._mod.get_active_for_target(ModerationTargetType.SET, set_id)
        if existing:
            await self._session.delete(existing)
            await self._session.flush()

        # Advance content status to PENDING_REVIEW
        await self._sets.update(set_id, status=ContentStatus.PENDING_REVIEW)

        entry = await self._mod.create(
            target_type=ModerationTargetType.SET,
            target_id=set_id,
            creator_id=user_id,
            patch_data=_set_snapshot(s),
            feedback=feedback,
        )
        await self._session.commit()
        await self._session.refresh(entry)
        return entry

    async def submit_item(
        self, user_id: int, item_id: int, feedback: str | None = None
    ) -> PendingModeration:
        """
        Submit an item for moderation.

        Rules:
        - User must own the item.
        - Item must be in DRAFT status.
        - If an active PENDING entry exists for this item, it is replaced.
        """
        item = await self._items.get_by_id(item_id)
        if not item:
            raise ResourceNotFoundError("Item", item_id)
        if item.creator_id != user_id:
            raise NotAuthorizedError("submit this item for review")
        if item.status not in _SUBMITTABLE_STATUSES:
            raise InvalidStateTransitionError(item.status.value, ContentStatus.PENDING_REVIEW.value)

        existing = await self._mod.get_active_for_target(ModerationTargetType.ITEM, item_id)
        if existing:
            await self._session.delete(existing)
            await self._session.flush()

        await self._items.update_status(item_id, ContentStatus.PENDING_REVIEW)

        entry = await self._mod.create(
            target_type=ModerationTargetType.ITEM,
            target_id=item_id,
            creator_id=user_id,
            patch_data=_item_snapshot(item),
            feedback=feedback,
        )
        await self._session.commit()
        await self._session.refresh(entry)
        return entry

    # ------------------------------------------------------------------
    # USER: View own submissions
    # ------------------------------------------------------------------

    async def get_my_submissions(
        self, user_id: int, *, skip: int = 0, limit: int = 20
    ) -> tuple[list[PendingModeration], int]:
        entries = list(await self._mod.get_by_creator(user_id, skip=skip, limit=limit))
        total = await self._mod.count_by_creator(user_id)
        return entries, total

    async def get_my_submission(self, user_id: int, moderation_id: int) -> PendingModeration:
        entry = await self._mod.get_by_id(moderation_id)
        if not entry or entry.creator_id != user_id:
            raise ResourceNotFoundError("Moderation entry", moderation_id)
        return entry

    # ------------------------------------------------------------------
    # ADMIN: List and inspect
    # ------------------------------------------------------------------

    async def list_submissions(
        self,
        *,
        target_type: ModerationTargetType | None = None,
        status: ModerationStatus | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[PendingModeration], int]:
        entries = list(
            await self._mod.list_all(
                target_type=target_type, status=status, skip=skip, limit=limit
            )
        )
        total = await self._mod.count_all(target_type=target_type, status=status)
        return entries, total

    async def get_submission(self, moderation_id: int) -> PendingModeration:
        entry = await self._mod.get_by_id(moderation_id)
        if not entry:
            raise ResourceNotFoundError("Moderation entry", moderation_id)
        return entry

    # ------------------------------------------------------------------
    # ADMIN: Approve
    # ------------------------------------------------------------------

    async def approve(
        self,
        admin_id: int,
        moderation_id: int,
        resolution_feedback: str | None = None,
    ) -> PendingModeration:
        """
        Approve a pending moderation entry.

        - Content status → APPROVED (publicly visible).
        - Entry resolved atomically; raises ConcurrencyError if already resolved.
        """
        entry = await self._mod.get_by_id(moderation_id)
        if not entry:
            raise ResourceNotFoundError("Moderation entry", moderation_id)
        if entry.status != ModerationStatus.PENDING:
            raise BusinessRuleViolationError(
                f"Moderation entry {moderation_id} is already {entry.status.value}"
            )

        resolved = await self._mod.resolve(
            moderation_id,
            moderator_id=admin_id,
            status=ModerationStatus.APPROVED,
            resolution_feedback=resolution_feedback,
        )
        if not resolved:
            raise ConcurrencyError("PendingModeration", moderation_id)

        await self._approve_content(entry)
        await self._session.commit()

        await self._session.refresh(entry)
        return entry

    async def _approve_content(self, entry: PendingModeration) -> None:
        if entry.target_type == ModerationTargetType.SET:
            await self._sets.update(entry.target_id, status=ContentStatus.APPROVED)
        elif entry.target_type == ModerationTargetType.ITEM:
            await self._items.update_status(entry.target_id, ContentStatus.APPROVED)

    # ------------------------------------------------------------------
    # ADMIN: Reject
    # ------------------------------------------------------------------

    async def reject(
        self,
        admin_id: int,
        moderation_id: int,
        resolution_feedback: str,
    ) -> PendingModeration:
        """
        Reject a pending moderation entry.

        - Content status → DRAFT (stays private).
        - resolution_feedback is required.
        - Raises ConcurrencyError if another admin resolved concurrently.
        """
        entry = await self._mod.get_by_id(moderation_id)
        if not entry:
            raise ResourceNotFoundError("Moderation entry", moderation_id)
        if entry.status != ModerationStatus.PENDING:
            raise BusinessRuleViolationError(
                f"Moderation entry {moderation_id} is already {entry.status.value}"
            )

        resolved = await self._mod.resolve(
            moderation_id,
            moderator_id=admin_id,
            status=ModerationStatus.REJECTED,
            resolution_feedback=resolution_feedback,
        )
        if not resolved:
            raise ConcurrencyError("PendingModeration", moderation_id)

        await self._revert_content(entry)
        await self._session.commit()

        await self._session.refresh(entry)
        return entry

    async def _revert_content(self, entry: PendingModeration) -> None:
        if entry.target_type == ModerationTargetType.SET:
            await self._sets.update(entry.target_id, status=ContentStatus.DRAFT)
        elif entry.target_type == ModerationTargetType.ITEM:
            await self._items.update_status(entry.target_id, ContentStatus.DRAFT)


__all__ = ["ModerationService"]
