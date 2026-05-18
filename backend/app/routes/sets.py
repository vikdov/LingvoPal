# backend/app/routes/sets.py
"""
Set routes — HTTP layer only.

Rules:
  - Call service, map domain exceptions to HTTP responses
  - Zero business logic here
"""

from typing import NoReturn

from fastapi import APIRouter, HTTPException, Query, status

from app.core.dependencies import ComplaintServiceDep, CurrentUser, SetServiceDep
from app.core.exceptions import LingvoPalError
from app.core.http_errors import domain_error_to_http
from app.schemas.common import PaginatedResponse
from app.schemas.complaint import ComplaintRequest, ComplaintResponse
from app.schemas.set import (
    CreatedSetSummaryResponse,
    SetCreateRequest,
    SetLibraryEntryResponse,
    SetLibraryPinRequest,
    SetLibraryStatusResponse,
    SetResponse,
    SetSummaryResponse,
    SetUpdateRequest,
)

router = APIRouter(prefix="/sets", tags=["sets"])


# ============================================================================
# ERROR MAPPING
# ============================================================================


def _handle(exc: LingvoPalError) -> NoReturn:
    domain_error_to_http(exc)


def _build_set_response(s, item_count: int, creator_username: str | None = None) -> SetResponse:
    return SetResponse.model_validate(s).model_copy(update={"item_count": item_count, "creator_username": creator_username})


def _build_set_summary(s, item_count: int, creator_username: str | None = None) -> SetSummaryResponse:
    return SetSummaryResponse.model_validate(s).model_copy(update={"item_count": item_count, "creator_username": creator_username})


def _build_created_set_summary(s, item_count: int, is_pinned: bool) -> CreatedSetSummaryResponse:
    return CreatedSetSummaryResponse.model_validate(s).model_copy(
        update={"item_count": item_count, "is_pinned": is_pinned}
    )


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post(
    "",
    response_model=SetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new set",
)
async def create_set(
    body: SetCreateRequest,
    user: CurrentUser,
    service: SetServiceDep,
) -> SetResponse:
    try:
        s, count = await service.create_set(user.id, body)
        return _build_set_response(s, count)
    except LingvoPalError as exc:
        _handle(exc)


@router.get(
    "/created",
    response_model=PaginatedResponse[CreatedSetSummaryResponse],
    summary="List sets I created",
)
async def get_created_sets(
    user: CurrentUser,
    service: SetServiceDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
) -> PaginatedResponse[CreatedSetSummaryResponse]:
    results, total = await service.get_my_sets(user.id, skip=skip, limit=limit)
    data = [_build_created_set_summary(s, count, is_pinned) for s, count, is_pinned in results]
    page = skip // limit + 1 if limit else 1
    return PaginatedResponse(data=data, total=total, page=page, page_size=limit)


@router.get(
    "/public",
    response_model=PaginatedResponse[SetSummaryResponse],
    summary="Search public sets",
)
async def search_public_sets(
    user: CurrentUser,
    service: SetServiceDep,
    query: str | None = Query(None, max_length=200, description="Title search"),
    source_lang_id: int | None = Query(None, gt=0),
    target_lang_id: int | None = Query(None, gt=0),
    difficulty: int | None = Query(None, ge=1, le=7),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[SetSummaryResponse]:
    results, total = await service.search_public_sets(
        query=query,
        source_lang_id=source_lang_id,
        target_lang_id=target_lang_id,
        difficulty=difficulty,
        skip=skip,
        limit=limit,
    )
    data = [_build_set_summary(s, count, username) for s, count, username in results]
    page = skip // limit + 1 if limit else 1
    return PaginatedResponse(data=data, total=total, page=page, page_size=limit)


@router.get(
    "/library",
    response_model=PaginatedResponse[SetLibraryEntryResponse],
    summary="Get my saved library",
)
async def get_library(
    user: CurrentUser,
    service: SetServiceDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
) -> PaginatedResponse[SetLibraryEntryResponse]:
    entries, total = await service.get_user_library(user.id, skip=skip, limit=limit)
    data = [
        SetLibraryEntryResponse(
            set_id=e.set_id,
            added_at=e.added_at,
            last_opened_at=e.last_opened_at,
            is_pinned=e.is_pinned,
            set=SetSummaryResponse.model_validate(e.set).model_copy(update={"item_count": count}),
            due_count=due_count,
        )
        for e, count, due_count in entries
    ]
    page = skip // limit + 1 if limit else 1
    return PaginatedResponse(data=data, total=total, page=page, page_size=limit)


@router.get(
    "/{set_id}",
    response_model=SetResponse,
    summary="Get a set by ID",
)
async def get_set(
    set_id: int,
    user: CurrentUser,
    service: SetServiceDep,
) -> SetResponse:
    try:
        s, count, creator_username = await service.get_set(user.id, set_id)
        return _build_set_response(s, count, creator_username)
    except LingvoPalError as exc:
        _handle(exc)


@router.patch(
    "/{set_id}",
    response_model=SetResponse,
    summary="Update a set you own",
)
async def update_set(
    set_id: int,
    body: SetUpdateRequest,
    user: CurrentUser,
    service: SetServiceDep,
) -> SetResponse:
    try:
        s, count = await service.update_set(user.id, set_id, body)
        return _build_set_response(s, count)
    except LingvoPalError as exc:
        _handle(exc)


@router.delete(
    "/{set_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a set you own",
)
async def delete_set(
    set_id: int,
    user: CurrentUser,
    service: SetServiceDep,
) -> None:
    try:
        await service.delete_set(user.id, set_id)
    except LingvoPalError as exc:
        _handle(exc)


@router.get(
    "/{set_id}/library",
    response_model=SetLibraryStatusResponse,
    summary="Check if a set is in the user's library",
)
async def get_library_status(
    set_id: int,
    user: CurrentUser,
    service: SetServiceDep,
) -> SetLibraryStatusResponse:
    in_library = await service.is_in_library(user.id, set_id)
    return SetLibraryStatusResponse(in_library=in_library)


@router.post(
    "/{set_id}/library",
    status_code=status.HTTP_201_CREATED,
    summary="Add a set to your library",
    responses={
        409: {"description": "Set already in library"},
    },
)
async def save_set_to_library(
    set_id: int,
    user: CurrentUser,
    service: SetServiceDep,
) -> dict:
    try:
        await service.save_set_to_library(user.id, set_id)
        return {"message": "Set saved to library"}
    except LingvoPalError as exc:
        _handle(exc)


@router.delete(
    "/{set_id}/library",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a set from your library",
)
async def remove_from_library(
    set_id: int,
    user: CurrentUser,
    service: SetServiceDep,
) -> None:
    try:
        await service.remove_set_from_library(user.id, set_id)
    except LingvoPalError as exc:
        _handle(exc)


@router.post(
    "/{set_id}/touch",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Record that the user opened a set (updates last_opened_at)",
)
async def touch_set(
    set_id: int,
    user: CurrentUser,
    service: SetServiceDep,
) -> None:
    await service.touch_set(user.id, set_id)


@router.patch(
    "/{set_id}/library",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update library entry (e.g. pin/unpin a set)",
)
async def update_library_entry(
    set_id: int,
    body: SetLibraryPinRequest,
    user: CurrentUser,
    service: SetServiceDep,
) -> None:
    try:
        await service.toggle_pin(user.id, set_id, body.is_pinned)
    except LingvoPalError as exc:
        _handle(exc)


@router.post(
    "/{set_id}/fork",
    response_model=SetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Fork a set into your own private copy",
    description=(
        "Creates a private copy of the set owned by you. "
        "Items are shared references — not duplicated. "
        "The fork starts as private (DRAFT) and can be made public later."
    ),
)
async def fork_set(
    set_id: int,
    user: CurrentUser,
    service: SetServiceDep,
) -> SetResponse:
    try:
        s, count = await service.fork_set(user.id, set_id)
        return _build_set_response(s, count)
    except LingvoPalError as exc:
        _handle(exc)


@router.post(
    "/{set_id}/report",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Report a community set",
    description=(
        "File a complaint against a COMMUNITY set. "
        "One report per user per set. "
        "Requires at least one completed study session."
    ),
)
async def report_set(
    set_id: int,
    body: ComplaintRequest,
    user: CurrentUser,
    svc: ComplaintServiceDep,
) -> ComplaintResponse:
    try:
        complaint = await svc.file_set_complaint(user.id, set_id, body.reason, body.details)
        return ComplaintResponse.model_validate(complaint)
    except LingvoPalError as exc:
        _handle(exc)
