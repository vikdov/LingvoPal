# backend/app/routes/items.py
"""Item routes — HTTP layer only. No business logic."""

from typing import NoReturn

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile, status

from app.core.dependencies import CurrentUser, ItemServiceDep
from app.core.exceptions import (
    DuplicateResourceError,
    LingvoPalError,
    NotAuthorizedError,
    ResourceNotFoundError,
)
from app.models.enums import PartOfSpeech
from app.schemas.common import PaginatedResponse
from app.schemas.item import (
    AddExistingItemRequest,
    ItemCreateRequest,
    ItemDetailResponse,
    ItemResponse,
    ItemUpdateRequest,
    SetItemResponse,
    TranslationCreateRequest,
    TranslationResponse,
    TranslationUpdateRequest,
)

items_router = APIRouter(prefix="/items", tags=["items"])
set_items_router = APIRouter(prefix="/sets/{set_id}/items", tags=["items"])


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


# ============================================================================
# DISCOVERY  (/items/public)
# ============================================================================


@items_router.get(
    "/public",
    response_model=PaginatedResponse[ItemResponse],
    summary="Search public items",
)
async def search_public_items(
    user: CurrentUser,
    service: ItemServiceDep,
    query: str | None = Query(None, max_length=200),
    language_id: int | None = Query(None, gt=0),
    part_of_speech: PartOfSpeech | None = None,
    difficulty: int | None = Query(None, ge=1, le=7),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[ItemResponse]:
    items, total = await service.search_public_items(
        query=query,
        language_id=language_id,
        part_of_speech=part_of_speech,
        difficulty=difficulty,
        skip=skip,
        limit=limit,
    )
    page = skip // limit + 1 if limit else 1
    return PaginatedResponse(
        data=[ItemResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=limit,
    )


# ============================================================================
# ITEM CRUD  (/items/{item_id})
# ============================================================================


@items_router.patch(
    "/{item_id}",
    response_model=ItemDetailResponse,
    summary="Update an item you own",
)
async def update_item(
    item_id: int,
    body: ItemUpdateRequest,
    user: CurrentUser,
    service: ItemServiceDep,
) -> ItemDetailResponse:
    try:
        item = await service.update_item(user.id, item_id, body)
        return ItemDetailResponse.model_validate(item)
    except LingvoPalError as exc:
        _handle(exc)


@items_router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an item you own",
)
async def delete_item(
    item_id: int,
    user: CurrentUser,
    service: ItemServiceDep,
) -> None:
    try:
        await service.delete_item(user.id, item_id)
    except LingvoPalError as exc:
        _handle(exc)


@items_router.post(
    "/{item_id}/submit",
    response_model=ItemDetailResponse,
    summary="Submit item for moderation review (DRAFT → PENDING_REVIEW)",
)
async def submit_item(
    item_id: int,
    user: CurrentUser,
    service: ItemServiceDep,
) -> ItemDetailResponse:
    try:
        item = await service.submit_item(user.id, item_id)
        return ItemDetailResponse.model_validate(item)
    except LingvoPalError as exc:
        _handle(exc)


@items_router.post(
    "/{item_id}/image",
    response_model=ItemDetailResponse,
    summary="Upload an image for an item",
)
async def upload_item_image(
    item_id: int,
    request: Request,
    user: CurrentUser,
    service: ItemServiceDep,
    file: UploadFile = File(...),
) -> ItemDetailResponse:
    try:
        base_url = str(request.base_url)
        item = await service.upload_item_image(user.id, item_id, file, base_url)
        return ItemDetailResponse.model_validate(item)
    except LingvoPalError as exc:
        _handle(exc)


# ============================================================================
# TRANSLATIONS  (/items/{item_id}/translations)
# ============================================================================


@items_router.post(
    "/{item_id}/translations",
    response_model=TranslationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a translation to an item",
)
async def create_translation(
    item_id: int,
    body: TranslationCreateRequest,
    user: CurrentUser,
    service: ItemServiceDep,
) -> TranslationResponse:
    try:
        t = await service.add_translation(user.id, item_id, body)
        return TranslationResponse.model_validate(t)
    except LingvoPalError as exc:
        _handle(exc)


@items_router.patch(
    "/{item_id}/translations/{translation_id}",
    response_model=TranslationResponse,
    summary="Update a translation",
)
async def update_translation(
    item_id: int,
    translation_id: int,
    body: TranslationUpdateRequest,
    user: CurrentUser,
    service: ItemServiceDep,
) -> TranslationResponse:
    try:
        t = await service.update_translation(user.id, item_id, translation_id, body)
        return TranslationResponse.model_validate(t)
    except LingvoPalError as exc:
        _handle(exc)


@items_router.delete(
    "/{item_id}/translations/{translation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a translation",
)
async def delete_translation(
    item_id: int,
    translation_id: int,
    user: CurrentUser,
    service: ItemServiceDep,
) -> None:
    try:
        await service.delete_translation(user.id, item_id, translation_id)
    except LingvoPalError as exc:
        _handle(exc)


@items_router.post(
    "/{item_id}/translations/{translation_id}/submit",
    response_model=TranslationResponse,
    summary="Submit translation for review",
)
async def submit_translation(
    item_id: int,
    translation_id: int,
    user: CurrentUser,
    service: ItemServiceDep,
) -> TranslationResponse:
    try:
        t = await service.submit_translation(user.id, item_id, translation_id)
        return TranslationResponse.model_validate(t)
    except LingvoPalError as exc:
        _handle(exc)


# ============================================================================
# ITEMS WITHIN A SET  (/sets/{set_id}/items/*)
# ============================================================================


@set_items_router.get(
    "",
    response_model=list[SetItemResponse],
    summary="List items in a set (with translations)",
)
async def get_set_items(
    set_id: int,
    user: CurrentUser,
    service: ItemServiceDep,
) -> list[SetItemResponse]:
    try:
        set_items = await service.get_set_items(user.id, set_id)
        return [SetItemResponse.model_validate(si) for si in set_items]
    except LingvoPalError as exc:
        _handle(exc)


@set_items_router.post(
    "",
    response_model=ItemDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new item and add it to a set",
)
async def create_item_in_set(
    set_id: int,
    body: ItemCreateRequest,
    user: CurrentUser,
    service: ItemServiceDep,
) -> ItemDetailResponse:
    try:
        item, _ = await service.create_item(user.id, set_id, body)
        return ItemDetailResponse.model_validate(item)
    except LingvoPalError as exc:
        _handle(exc)


@set_items_router.post(
    "/{item_id}",
    response_model=SetItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an existing item to a set",
)
async def add_existing_item_to_set(
    set_id: int,
    item_id: int,
    user: CurrentUser,
    service: ItemServiceDep,
    body: AddExistingItemRequest | None = None,
) -> SetItemResponse:
    sort_order = body.sort_order if body else 0
    try:
        set_item = await service.add_item_to_set(user.id, set_id, item_id, sort_order)
        return SetItemResponse.model_validate(set_item)
    except LingvoPalError as exc:
        _handle(exc)


@set_items_router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove an item from a set",
)
async def remove_item_from_set(
    set_id: int,
    item_id: int,
    user: CurrentUser,
    service: ItemServiceDep,
) -> None:
    try:
        await service.remove_item_from_set(user.id, set_id, item_id)
    except LingvoPalError as exc:
        _handle(exc)


@set_items_router.post(
    "/{item_id}/fork",
    response_model=ItemDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Fork a public item into your set",
)
async def fork_item_into_set(
    set_id: int,
    item_id: int,
    user: CurrentUser,
    service: ItemServiceDep,
) -> ItemDetailResponse:
    try:
        item, _ = await service.fork_item_into_set(user.id, set_id, item_id)
        return ItemDetailResponse.model_validate(item)
    except LingvoPalError as exc:
        _handle(exc)
