# backend/app/services/moderation_service.py
"""
Moderation service — workflow for submitting and reviewing content.

State machine:
  DRAFT      → submit()   → COMMUNITY  (content status, publicly visible immediately)
  COMMUNITY  → approve()  → APPROVED   (content status)
  COMMUNITY  → reject()   → DRAFT      (content status)
  DRAFT      → submit()   → COMMUNITY  (resubmit after rejection)

PendingModeration entry:
  PENDING  → approve() → APPROVED (resolved_at set)
  PENDING  → reject()  → REJECTED (resolved_at set)
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BusinessRuleViolationError,
    ConcurrencyError,
    ContentValidationError,  # noqa: F401 — re-exported for route imports
    InvalidStateTransitionError,
    NotAuthorizedError,
    ResourceNotFoundError,
)
from app.models.enums import ContentStatus, ModerationStatus, ModerationTargetType
from app.models.pending_moderation import PendingModeration
from app.repositories.audit_repo import AuditRepository
from app.repositories.complaint_repo import ComplaintRepository
from app.repositories.item_repo import ItemRepository
from app.repositories.moderation_repo import ModerationRepository
from app.repositories.set_repo import SetRepository
from app.services import content_validator

logger = logging.getLogger(__name__)

_SUBMITTABLE_STATUSES = (ContentStatus.DRAFT,)


def _assert_status(current: ContentStatus, expected: ContentStatus) -> None:
    if current != expected:
        raise InvalidStateTransitionError(current.value, expected.value)


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
        self._audit = AuditRepository(session)
        self._complaints = ComplaintRepository(session)

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
            raise InvalidStateTransitionError(s.status.value, ContentStatus.COMMUNITY.value)

        content_validator.validate_set(s.title, s.description)

        # Cancel any existing active entry for this target (upsert semantics)
        existing = await self._mod.get_active_for_target(ModerationTargetType.SET, set_id)
        if existing:
            await self._session.delete(existing)
            await self._session.flush()

        await self._sets.update(set_id, status=ContentStatus.COMMUNITY)

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
            raise InvalidStateTransitionError(item.status.value, ContentStatus.COMMUNITY.value)

        lang_code = await self._items.get_language_code(item.language_id)
        lang_mismatch = content_validator.validate_item(item.term, item.context, lang_code or "")
        if lang_mismatch:
            logger.warning(
                "Language mismatch on submission: item=%d expected_lang=%s",
                item_id, lang_code,
            )

        existing = await self._mod.get_active_for_target(ModerationTargetType.ITEM, item_id)
        if existing:
            await self._session.delete(existing)
            await self._session.flush()

        await self._items.update_status(item_id, ContentStatus.COMMUNITY)

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

    async def get_latest_for_target(
        self,
        user_id: int,
        target_type: ModerationTargetType,
        target_id: int,
    ) -> PendingModeration | None:
        return await self._mod.get_latest_for_creator_and_target(user_id, target_type, target_id)

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

        await self._approve_content(entry, admin_id)
        await self._session.commit()

        await self._session.refresh(entry)
        return entry

    async def _approve_content(self, entry: PendingModeration, moderator_id: int) -> None:
        if entry.target_type == ModerationTargetType.SET:
            s = await self._sets.get_by_id(entry.target_id)
            if s:
                _assert_status(s.status, ContentStatus.COMMUNITY)
            await self._sets.update(entry.target_id, status=ContentStatus.APPROVED)
            await self._audit.log(
                "sets", entry.target_id, "UPDATE", user_id=moderator_id,
                old_values={"status": ContentStatus.COMMUNITY.value},
                new_values={"status": ContentStatus.APPROVED.value},
            )
        elif entry.target_type == ModerationTargetType.ITEM:
            item = await self._items.get_by_id(entry.target_id)
            if item:
                _assert_status(item.status, ContentStatus.COMMUNITY)
            await self._items.update_status(entry.target_id, ContentStatus.APPROVED)
            await self._audit.log(
                "items", entry.target_id, "UPDATE", user_id=moderator_id,
                old_values={"status": ContentStatus.COMMUNITY.value},
                new_values={"status": ContentStatus.APPROVED.value},
            )

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

        await self._revert_content(entry, admin_id)
        await self._session.commit()

        await self._session.refresh(entry)
        return entry

    # ------------------------------------------------------------------
    # ADMIN: Promote to OFFICIAL
    # ------------------------------------------------------------------

    async def promote_to_official(
        self,
        admin_id: int,
        item_id: int,
        override: bool = False,
    ) -> None:
        """
        Promote an APPROVED item to OFFICIAL.

        Quality thresholds from config are soft gates: if override=True,
        admin can bypass them. Always raises InvalidStateTransitionError
        if item is not APPROVED.
        """
        from app.core.config import get_settings
        from app.repositories.quality_repo import QualityRepository
        from app.models.item_quality_metrics import ItemQualityMetrics
        from sqlalchemy import select

        item = await self._items.get_by_id(item_id)
        if not item:
            raise ResourceNotFoundError("Item", item_id)
        _assert_status(item.status, ContentStatus.APPROVED)

        if not override:
            settings = get_settings()
            result = await self._session.execute(
                select(ItemQualityMetrics).where(
                    ItemQualityMetrics.item_id == item_id
                )
            )
            metrics = result.scalar_one_or_none()
            if metrics:
                below_threshold = (
                    metrics.learner_count < settings.OFFICIAL_MIN_LEARNERS
                    or metrics.global_success_rate < settings.OFFICIAL_MIN_SUCCESS_RATE
                )
                if below_threshold:
                    raise BusinessRuleViolationError(
                        f"Item does not meet OFFICIAL thresholds "
                        f"(learners={metrics.learner_count}, "
                        f"success_rate={metrics.global_success_rate:.2f}). "
                        f"Pass override=true to promote anyway."
                    )

        await self._items.update_status(item_id, ContentStatus.OFFICIAL)
        await self._audit.log(
            "items", item_id, "UPDATE", user_id=admin_id,
            old_values={"status": ContentStatus.APPROVED.value},
            new_values={"status": ContentStatus.OFFICIAL.value},
        )
        await self._session.commit()

    # ------------------------------------------------------------------
    # ADMIN: Promotion candidates
    # ------------------------------------------------------------------

    async def list_promotion_candidates(
        self, skip: int = 0, limit: int = 20
    ) -> list:
        """Return APPROVED items whose quality metrics meet OFFICIAL thresholds."""
        from app.core.config import get_settings
        from app.repositories.quality_repo import QualityRepository
        from app.models.item_quality_metrics import ItemQualityMetrics
        from app.models.item import Item
        from sqlalchemy import select

        settings = get_settings()
        result = await self._session.execute(
            select(Item)
            .join(ItemQualityMetrics, ItemQualityMetrics.item_id == Item.id)
            .where(
                Item.status == ContentStatus.APPROVED,
                Item.deleted_at.is_(None),
                ItemQualityMetrics.learner_count >= settings.OFFICIAL_MIN_LEARNERS,
                ItemQualityMetrics.global_success_rate >= settings.OFFICIAL_MIN_SUCCESS_RATE,
            )
            .order_by(
                ItemQualityMetrics.global_success_rate.desc(),
                ItemQualityMetrics.learner_count.desc(),
            )
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # ADMIN: Overview stats
    # ------------------------------------------------------------------

    async def get_overview_stats(self) -> dict:
        from sqlalchemy import select, func as sql_func
        from app.models.item import Item

        community_count = (await self._session.execute(
            select(sql_func.count()).where(
                Item.status == ContentStatus.COMMUNITY,
                Item.deleted_at.is_(None),
            )
        )).scalar_one()

        pending_queue_count = await self._mod.count_all(status=ModerationStatus.PENDING)
        total_complaints = await self._complaints.count_all()

        return {
            "community_count": community_count,
            "pending_queue_count": pending_queue_count,
            "total_complaints": total_complaints,
        }

    # ------------------------------------------------------------------
    # ADMIN: Enriched moderation queue
    # ------------------------------------------------------------------

    async def list_submissions_enriched(
        self,
        *,
        target_type: ModerationTargetType | None = None,
        status: ModerationStatus | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list, int]:
        from sqlalchemy import select
        from app.models.item_quality_metrics import ItemQualityMetrics
        from app.schemas.moderation import (
            AdminModerationResponse,
            PendingModerationResponse,
            QualityMetricsSummary,
        )

        entries = list(await self._mod.list_all(
            target_type=target_type, status=status, skip=skip, limit=limit
        ))
        total = await self._mod.count_all(target_type=target_type, status=status)

        if not entries:
            return [], total

        item_ids = [e.target_id for e in entries if e.target_type == ModerationTargetType.ITEM]
        set_ids = [e.target_id for e in entries if e.target_type == ModerationTargetType.SET]

        item_counts = await self._complaints.count_for_targets_batch(ModerationTargetType.ITEM, item_ids)
        set_counts = await self._complaints.count_for_targets_batch(ModerationTargetType.SET, set_ids)

        quality_map: dict[int, ItemQualityMetrics] = {}
        if item_ids:
            result = await self._session.execute(
                select(ItemQualityMetrics).where(ItemQualityMetrics.item_id.in_(item_ids))
            )
            for m in result.scalars():
                quality_map[m.item_id] = m

        enriched = []
        for e in entries:
            base = PendingModerationResponse.model_validate(e).model_dump()
            if e.target_type == ModerationTargetType.ITEM:
                complaint_count = item_counts.get(e.target_id, 0)
                qm = quality_map.get(e.target_id)
                quality_metrics = QualityMetricsSummary(
                    learner_count=qm.learner_count,
                    sample_size=qm.sample_size,
                    global_success_rate=qm.global_success_rate,
                    avg_interval=qm.avg_interval,
                ) if qm else None
            else:
                complaint_count = set_counts.get(e.target_id, 0)
                quality_metrics = None

            enriched.append(AdminModerationResponse(
                **base,
                quality_metrics=quality_metrics,
                complaint_count=complaint_count,
            ))

        return enriched, total

    # ------------------------------------------------------------------
    # ADMIN: Complaint listing
    # ------------------------------------------------------------------

    async def list_complaints_admin(
        self,
        *,
        target_type: ModerationTargetType | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list, int]:
        entries = list(await self._complaints.list_all(
            target_type=target_type, skip=skip, limit=limit
        ))
        total = await self._complaints.count_all(target_type=target_type)
        return entries, total

    # ------------------------------------------------------------------
    # ADMIN: Force-delete content
    # ------------------------------------------------------------------

    async def admin_delete_item(self, admin_id: int, item_id: int, reason: str) -> None:
        """
        Permanently soft-deletes an item regardless of owner.
        Resolves any pending moderation entry for the item.
        """
        item = await self._items.get_by_id(item_id)
        if not item:
            raise ResourceNotFoundError("Item", item_id)
        pending = await self._mod.get_active_for_target(ModerationTargetType.ITEM, item_id)
        if pending:
            await self._mod.resolve(
                pending.id,
                moderator_id=admin_id,
                status=ModerationStatus.REJECTED,
                resolution_feedback=f"Content removed by admin: {reason}",
            )
        await self._items.soft_delete(item_id)
        await self._audit.log(
            "items", item_id, "DELETE", user_id=admin_id,
            old_values={"status": item.status.value, "reason": reason},
        )
        await self._session.commit()

    async def admin_delete_set(self, admin_id: int, set_id: int, reason: str) -> None:
        """
        Permanently soft-deletes a set regardless of owner.
        Resolves any pending moderation entry for the set.
        """
        s = await self._sets.get_by_id(set_id)
        if not s:
            raise ResourceNotFoundError("Set", set_id)
        pending = await self._mod.get_active_for_target(ModerationTargetType.SET, set_id)
        if pending:
            await self._mod.resolve(
                pending.id,
                moderator_id=admin_id,
                status=ModerationStatus.REJECTED,
                resolution_feedback=f"Content removed by admin: {reason}",
            )
        await self._sets.soft_delete(set_id)
        await self._audit.log(
            "sets", set_id, "DELETE", user_id=admin_id,
            old_values={"status": s.status.value, "reason": reason},
        )
        await self._session.commit()

    async def dismiss_complaint(self, admin_id: int, complaint_id: int) -> None:
        complaint = await self._complaints.get_by_id(complaint_id)
        if not complaint:
            raise ResourceNotFoundError("Complaint", complaint_id)
        deleted = await self._complaints.delete_by_id(complaint_id)
        if not deleted:
            raise ResourceNotFoundError("Complaint", complaint_id)
        await self._audit.log(
            "content_complaints", complaint_id, "DELETE", user_id=admin_id,
            old_values={"target_type": complaint.target_type.value, "target_id": complaint.target_id},
        )
        await self._session.commit()

    # ------------------------------------------------------------------
    # ADMIN: Audit log
    # ------------------------------------------------------------------

    async def list_audit_log(
        self,
        *,
        table_name: str | None = None,
        action: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list, int]:
        entries = list(await self._audit.list_all(
            table_name=table_name, action=action, skip=skip, limit=limit
        ))
        total = await self._audit.count_all(table_name=table_name, action=action)
        return entries, total

    async def _revert_content(self, entry: PendingModeration, moderator_id: int) -> None:
        if entry.target_type == ModerationTargetType.SET:
            s = await self._sets.get_by_id(entry.target_id)
            if s:
                _assert_status(s.status, ContentStatus.COMMUNITY)
            await self._sets.update(entry.target_id, status=ContentStatus.DRAFT)
            await self._audit.log(
                "sets", entry.target_id, "UPDATE", user_id=moderator_id,
                old_values={"status": ContentStatus.COMMUNITY.value},
                new_values={"status": ContentStatus.DRAFT.value},
            )
        elif entry.target_type == ModerationTargetType.ITEM:
            item = await self._items.get_by_id(entry.target_id)
            if item:
                _assert_status(item.status, ContentStatus.COMMUNITY)
            await self._items.update_status(entry.target_id, ContentStatus.DRAFT)
            await self._audit.log(
                "items", entry.target_id, "UPDATE", user_id=moderator_id,
                old_values={"status": ContentStatus.COMMUNITY.value},
                new_values={"status": ContentStatus.DRAFT.value},
            )


__all__ = ["ModerationService"]
