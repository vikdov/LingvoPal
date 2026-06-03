# backend/app/routes/moderation.py
"""
User-facing moderation routes.

Routes:
  POST /api/v1/moderation/sets/{set_id}/submit     — submit a set for review
  POST /api/v1/moderation/items/{item_id}/submit   — submit an item for review
  GET  /api/v1/moderation/sets/{set_id}/latest     — latest submission for a set
  GET  /api/v1/moderation/items/{item_id}/latest   — latest submission for an item
  GET  /api/v1/moderation/my                       — list own submissions
  GET  /api/v1/moderation/{moderation_id}          — view a specific submission
"""

from typing import NoReturn

from fastapi import APIRouter, Query, status

from app.core.dependencies import CurrentUser, ModerationServiceDep
from app.core.exceptions import LingvoPalError
from app.core.http_errors import domain_error_to_http
from app.models.enums import ModerationTargetType
from app.schemas.common import PaginatedResponse
from app.schemas.moderation import ModerationSubmissionResponse, SubmitForReviewRequest

router = APIRouter(prefix="/moderation", tags=["moderation"])


# ============================================================================
# ERROR MAPPING
# ============================================================================


def _handle(exc: LingvoPalError) -> NoReturn:
    domain_error_to_http(exc, business_rule_status=status.HTTP_409_CONFLICT)


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post(
    "/sets/{set_id}/submit",
    response_model=ModerationSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a set for public visibility review",
    description=(
        "Moves a DRAFT set into the moderation queue. "
        "If an existing pending submission exists it is replaced. "
        "After rejection a set returns to DRAFT and may be resubmitted."
    ),
)
async def submit_set_for_review(
    set_id: int,
    body: SubmitForReviewRequest,
    user: CurrentUser,
    svc: ModerationServiceDep,
) -> ModerationSubmissionResponse:
    try:
        entry = await svc.submit_set(user.id, set_id, feedback=body.feedback)
        return ModerationSubmissionResponse.model_validate(entry)
    except LingvoPalError as exc:
        _handle(exc)


@router.post(
    "/items/{item_id}/submit",
    response_model=ModerationSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit an item for public visibility review",
)
async def submit_item_for_review(
    item_id: int,
    body: SubmitForReviewRequest,
    user: CurrentUser,
    svc: ModerationServiceDep,
) -> ModerationSubmissionResponse:
    try:
        entry = await svc.submit_item(user.id, item_id, feedback=body.feedback)
        return ModerationSubmissionResponse.model_validate(entry)
    except LingvoPalError as exc:
        _handle(exc)


@router.get(
    "/sets/{set_id}/latest",
    response_model=ModerationSubmissionResponse | None,
    summary="Get latest moderation submission for a set",
)
async def get_latest_set_submission(
    set_id: int,
    user: CurrentUser,
    svc: ModerationServiceDep,
) -> ModerationSubmissionResponse | None:
    entry = await svc.get_latest_for_target(user.id, ModerationTargetType.SET, set_id)
    if not entry:
        return None
    return ModerationSubmissionResponse.model_validate(entry)


@router.get(
    "/items/{item_id}/latest",
    response_model=ModerationSubmissionResponse | None,
    summary="Get latest moderation submission for an item",
)
async def get_latest_item_submission(
    item_id: int,
    user: CurrentUser,
    svc: ModerationServiceDep,
) -> ModerationSubmissionResponse | None:
    entry = await svc.get_latest_for_target(user.id, ModerationTargetType.ITEM, item_id)
    if not entry:
        return None
    return ModerationSubmissionResponse.model_validate(entry)


@router.get(
    "/my",
    response_model=PaginatedResponse[ModerationSubmissionResponse],
    summary="List my moderation submissions",
)
async def list_my_submissions(
    user: CurrentUser,
    svc: ModerationServiceDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[ModerationSubmissionResponse]:
    entries, total = await svc.get_my_submissions(user.id, skip=skip, limit=limit)
    data = [ModerationSubmissionResponse.model_validate(e) for e in entries]
    page = skip // limit + 1 if limit else 1
    return PaginatedResponse(data=data, total=total, page=page, page_size=limit)


@router.get(
    "/{moderation_id}",
    response_model=ModerationSubmissionResponse,
    summary="Get status of a specific submission",
)
async def get_submission_status(
    moderation_id: int,
    user: CurrentUser,
    svc: ModerationServiceDep,
) -> ModerationSubmissionResponse:
    try:
        entry = await svc.get_my_submission(user.id, moderation_id)
        return ModerationSubmissionResponse.model_validate(entry)
    except LingvoPalError as exc:
        _handle(exc)
