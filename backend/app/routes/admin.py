# backend/app/routes/admin.py
"""
Admin-only routes for content moderation.

All endpoints require AdminUser (verified + ADMIN role).

Routes:
  GET  /api/v1/admin/moderation                          — list with filters
  GET  /api/v1/admin/moderation/{moderation_id}          — full detail
  POST /api/v1/admin/moderation/{moderation_id}/approve  — approve
  POST /api/v1/admin/moderation/{moderation_id}/reject   — reject
"""

from typing import NoReturn

from fastapi import APIRouter, HTTPException, Query, status

from app.core.dependencies import AdminUser, ModerationServiceDep
from app.core.exceptions import (
    BusinessRuleViolationError,
    ConcurrencyError,
    InvalidStateTransitionError,
    LingvoPalError,
    ResourceNotFoundError,
)
from app.models.enums import ModerationStatus, ModerationTargetType
from app.schemas.admin import AdminOverviewStats, AuditLogEntry, PromoteToOfficialRequest
from app.schemas.common import PaginatedResponse
from app.schemas.complaint import ComplaintResponse
from app.schemas.item import ItemResponse
from app.schemas.moderation import (
    AdminModerationResponse,
    ApproveModerationRequest,
    PendingModerationResponse,
    RejectModerationRequest,
)

router = APIRouter(prefix="/admin", tags=["admin"])


# ============================================================================
# ERROR MAPPING
# ============================================================================


def _handle(exc: LingvoPalError) -> NoReturn:
    if isinstance(exc, ResourceNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, ConcurrencyError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This entry was already resolved by another admin.",
        )
    if isinstance(exc, InvalidStateTransitionError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, BusinessRuleViolationError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# ============================================================================
# MODERATION QUEUE
# ============================================================================


@router.get(
    "/moderation",
    response_model=PaginatedResponse[AdminModerationResponse],
    summary="List moderation submissions (enriched)",
    description="Includes quality metrics and complaint count per entry.",
)
async def list_moderation(
    admin: AdminUser,
    svc: ModerationServiceDep,
    target_type: ModerationTargetType | None = Query(None),
    status_filter: ModerationStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[AdminModerationResponse]:
    entries, total = await svc.list_submissions_enriched(
        target_type=target_type,
        status=status_filter,
        skip=skip,
        limit=limit,
    )
    page = skip // limit + 1 if limit else 1
    return PaginatedResponse(data=entries, total=total, page=page, page_size=limit)


@router.get(
    "/moderation/{moderation_id}",
    response_model=PendingModerationResponse,
    summary="Get full moderation entry detail",
)
async def get_moderation_detail(
    moderation_id: int,
    admin: AdminUser,
    svc: ModerationServiceDep,
) -> PendingModerationResponse:
    try:
        entry = await svc.get_submission(moderation_id)
        return PendingModerationResponse.model_validate(entry)
    except LingvoPalError as exc:
        _handle(exc)


@router.post(
    "/moderation/{moderation_id}/approve",
    response_model=PendingModerationResponse,
    summary="Approve a moderation submission",
    description=(
        "Marks the submission as APPROVED and makes the content publicly visible. "
        "Returns 409 if the entry was already resolved (concurrent review guard)."
    ),
)
async def approve_moderation(
    moderation_id: int,
    body: ApproveModerationRequest,
    admin: AdminUser,
    svc: ModerationServiceDep,
) -> PendingModerationResponse:
    try:
        entry = await svc.approve(
            admin.id,
            moderation_id,
            resolution_feedback=body.resolution_feedback,
        )
        return PendingModerationResponse.model_validate(entry)
    except LingvoPalError as exc:
        _handle(exc)


@router.post(
    "/moderation/{moderation_id}/reject",
    response_model=PendingModerationResponse,
    summary="Reject a moderation submission",
    description=(
        "Marks the submission as REJECTED and reverts content to DRAFT. "
        "A rejection reason is required. "
        "The creator may edit and resubmit the content."
    ),
)
async def reject_moderation(
    moderation_id: int,
    body: RejectModerationRequest,
    admin: AdminUser,
    svc: ModerationServiceDep,
) -> PendingModerationResponse:
    try:
        entry = await svc.reject(
            admin.id,
            moderation_id,
            resolution_feedback=body.resolution_feedback,
        )
        return PendingModerationResponse.model_validate(entry)
    except LingvoPalError as exc:
        _handle(exc)


@router.post(
    "/items/{item_id}/promote",
    response_model=ItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Promote an approved item to OFFICIAL",
    description=(
        "Elevates an APPROVED item to the OFFICIAL tier. "
        "Quality thresholds (learner_count, success_rate) are soft gates — "
        "pass override=true to bypass them."
    ),
)
async def promote_item_to_official(
    item_id: int,
    body: PromoteToOfficialRequest,
    admin: AdminUser,
    svc: ModerationServiceDep,
) -> ItemResponse:
    try:
        await svc.promote_to_official(admin.id, item_id, override=body.override)
        item = await svc._items.get_by_id(item_id)
        return ItemResponse.model_validate(item)
    except LingvoPalError as exc:
        _handle(exc)


@router.get(
    "/items/promotion-candidates",
    response_model=list[ItemResponse],
    summary="List APPROVED items meeting OFFICIAL promotion thresholds",
)
async def list_promotion_candidates(
    admin: AdminUser,
    svc: ModerationServiceDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> list[ItemResponse]:
    try:
        items = await svc.list_promotion_candidates(skip=skip, limit=limit)
        return [ItemResponse.model_validate(i) for i in items]
    except LingvoPalError as exc:
        _handle(exc)


@router.get(
    "/overview",
    response_model=AdminOverviewStats,
    summary="Admin overview statistics",
)
async def get_admin_overview(
    admin: AdminUser,
    svc: ModerationServiceDep,
) -> AdminOverviewStats:
    stats = await svc.get_overview_stats()
    return AdminOverviewStats(**stats)


@router.get(
    "/complaints",
    response_model=PaginatedResponse[ComplaintResponse],
    summary="List all complaints",
)
async def list_complaints(
    admin: AdminUser,
    svc: ModerationServiceDep,
    target_type: ModerationTargetType | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[ComplaintResponse]:
    entries, total = await svc.list_complaints_admin(
        target_type=target_type, skip=skip, limit=limit
    )
    data = [ComplaintResponse.model_validate(e) for e in entries]
    page = skip // limit + 1 if limit else 1
    return PaginatedResponse(data=data, total=total, page=page, page_size=limit)


@router.get(
    "/audit-log",
    response_model=PaginatedResponse[AuditLogEntry],
    summary="System audit log",
)
async def list_audit_log(
    admin: AdminUser,
    svc: ModerationServiceDep,
    table_name: str | None = Query(None),
    action: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> PaginatedResponse[AuditLogEntry]:
    entries, total = await svc.list_audit_log(
        table_name=table_name, action=action, skip=skip, limit=limit
    )
    data = [AuditLogEntry.model_validate(e) for e in entries]
    page = skip // limit + 1 if limit else 1
    return PaginatedResponse(data=data, total=total, page=page, page_size=limit)
