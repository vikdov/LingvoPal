# backend/app/routes/sets.py
"""
Set routes — HTTP layer only.

Rules:
  - Call service, map domain exceptions to HTTP responses
  - Zero business logic here
"""

from typing import NoReturn

from fastapi import APIRouter, HTTPException, Query, status

from app.core.dependencies import CurrentUser, SetServiceDep
from app.core.exceptions import (
    DuplicateResourceError,
    LingvoPalError,
    NotAuthorizedError,
    ResourceNotFoundError,
)
from app.schemas.common import PaginatedResponse
from app.schemas.set import (
    SetCreateRequest,
    SetLibraryEntryResponse,
    SetResponse,
    SetUpdateRequest,
)

router = APIRouter(prefix="/sets", tags=["sets"])


# ============================================================================
# ERROR MAPPING
# ============================================================================


def _handle(exc: LingvoPalError) -> NoReturn:
    if isinstance(exc, ResourceNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, NotAuthorizedError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, DuplicateResourceError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


def _build_set_response(s, item_count: int) -> SetResponse:
    return SetResponse.model_validate(s).model_copy(update={"item_count": item_count})


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
    "/my",
    response_model=PaginatedResponse[SetResponse],
    summary="List my own sets",
)
async def get_my_sets(
    user: CurrentUser,
    service: SetServiceDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[SetResponse]:
    results, total = await service.get_my_sets(user.id, skip=skip, limit=limit)
    data = [_build_set_response(s, count) for s, count in results]
    page = skip // limit + 1 if limit else 1
    return PaginatedResponse(data=data, total=total, page=page, page_size=limit)


@router.get(
    "/public",
    response_model=PaginatedResponse[SetResponse],
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
) -> PaginatedResponse[SetResponse]:
    results, total = await service.search_public_sets(
        query=query,
        source_lang_id=source_lang_id,
        target_lang_id=target_lang_id,
        difficulty=difficulty,
        skip=skip,
        limit=limit,
    )
    data = [_build_set_response(s, count) for s, count in results]
    page = skip // limit + 1 if limit else 1
    return PaginatedResponse(data=data, total=total, page=page, page_size=limit)


@router.get(
    "/library",
    response_model=list[SetLibraryEntryResponse],
    summary="Get my saved library",
)
async def get_library(
    user: CurrentUser,
    service: SetServiceDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> list[SetLibraryEntryResponse]:
    entries = await service.get_user_library(user.id, skip=skip, limit=limit)
    # item_count is 0 by default in the nested SetResponse; acceptable for library list view
    return [SetLibraryEntryResponse.model_validate(e) for e in entries]


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
        s, count = await service.get_set(user.id, set_id)
        return _build_set_response(s, count)
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


@router.post(
    "/{set_id}/save",
    status_code=status.HTTP_201_CREATED,
    summary="Save a set to your library",
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
    "/{set_id}/save",
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
