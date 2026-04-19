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
    LingvoPalError,
    ResourceNotFoundError,
)
from app.models.enums import ModerationStatus, ModerationTargetType
from app.schemas.common import PaginatedResponse
from app.schemas.moderation import (
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
    if isinstance(exc, BusinessRuleViolationError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# ============================================================================
# MODERATION QUEUE
# ============================================================================


@router.get(
    "/moderation",
    response_model=PaginatedResponse[PendingModerationResponse],
    summary="List moderation submissions",
    description="Filter by target_type and/or status. Defaults to showing all entries.",
)
async def list_moderation(
    admin: AdminUser,
    svc: ModerationServiceDep,
    target_type: ModerationTargetType | None = Query(None),
    status_filter: ModerationStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[PendingModerationResponse]:
    entries, total = await svc.list_submissions(
        target_type=target_type,
        status=status_filter,
        skip=skip,
        limit=limit,
    )
    data = [PendingModerationResponse.model_validate(e) for e in entries]
    page = skip // limit + 1 if limit else 1
    return PaginatedResponse(data=data, total=total, page=page, page_size=limit)


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
