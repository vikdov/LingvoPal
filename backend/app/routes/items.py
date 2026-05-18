# backend/app/routes/items.py
"""Item routes — HTTP layer only. No business logic."""

from typing import NoReturn

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile, status

from app.core.dependencies import (
    ComplaintServiceDep,
    CurrentUser,
    ItemServiceDep,
    ItemSuggestionServiceDep,
    StorageDep,
)
from app.core.exceptions import LingvoPalError
from app.core.http_errors import domain_error_to_http
from app.core.limiter import limiter
from app.models.enums import PartOfSpeech
from app.schemas.common import PaginatedResponse
from app.schemas.complaint import ComplaintRequest, ComplaintResponse
from app.schemas.item import (
    AddExistingItemRequest,
    GenerateAudioRequest,
    GenerateAudioResponse,
    ImageSuggestion,
    ItemCreateRequest,
    ItemDetailResponse,
    ItemMetadataSuggestion,
    ItemSummaryResponse,
    ItemUpdateRequest,
    SearchImagesRequest,
    SetItemResponse,
    SuggestItemMetadataRequest,
    SynonymTermsRequest,
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
    domain_error_to_http(exc, business_rule_status=status.HTTP_409_CONFLICT)


# ============================================================================
# STATIC ROUTES (before /{item_id} catch-all)
# ============================================================================
# ⚠️ IMPORTANT: These routes must come BEFORE /{item_id} parameterized routes
# to avoid FastAPI matching "/suggestions" as item_id="suggestions"


@items_router.post(
    "/suggestions",
    response_model=ItemMetadataSuggestion,
    summary="Auto-fill item metadata, audio, and images",
    description=(
        "Generate complete item metadata in parallel:\n\n"
        "- **Linguistic enrichment** (AI): lemma, POS, CEFR, translations, synonyms\n"
        "- **Audio** (TTS): natural pronunciation\n"
        "- **Images**: visual reference suggestions\n\n"
        "All run in parallel. Partial failures don't block the response.\n"
        "User can accept, reject, or modify any suggestion before saving."
    ),
)
@limiter.limit("20/minute")
async def suggest_item_metadata(
    request: Request,
    body: SuggestItemMetadataRequest,
    user: CurrentUser,
    service: ItemSuggestionServiceDep,
) -> ItemMetadataSuggestion:
    """Generate complete suggestions for a vocabulary item."""
    try:
        suggestion = await service.suggest_complete(
            term=body.term,
            source_language=body.source_language,
            source_language_code=body.source_language_code,
            target_language=body.target_language,
            context=body.context,
        )
        return ItemMetadataSuggestion(**suggestion)
    except LingvoPalError as exc:
        _handle(exc)


@items_router.post(
    "/search_images",
    response_model=list[ImageSuggestion],
    summary="Fetch additional image suggestions for a query",
)
@limiter.limit("20/minute")
async def search_images(
    request: Request,
    body: SearchImagesRequest,
    user: CurrentUser,
    service: ItemSuggestionServiceDep,
) -> list[ImageSuggestion]:
    return await service.search_images(query=body.query, count=body.count)


@items_router.post(
    "/generate_audio",
    response_model=GenerateAudioResponse,
    summary="Generate TTS audio for a term and optional context sentence",
)
@limiter.limit("30/minute")
async def generate_item_audio(
    request: Request,
    body: GenerateAudioRequest,
    user: CurrentUser,
    service: ItemSuggestionServiceDep,
) -> GenerateAudioResponse:
    result = await service.generate_audio(
        term=body.term,
        language_code=body.language_code,
        context=body.context,
    )
    return GenerateAudioResponse(**result)


@items_router.get(
    "/mine",
    response_model=PaginatedResponse[ItemDetailResponse],
    summary="List items created by the current user",
)
async def get_my_items(
    user: CurrentUser,
    service: ItemServiceDep,
    query: str | None = Query(None, max_length=200),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[ItemDetailResponse]:
    items, total = await service.get_my_items(user.id, query=query, skip=skip, limit=limit)
    return PaginatedResponse(
        data=[ItemDetailResponse.model_validate(i) for i in items],
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
    )


@items_router.get(
    "/public",
    response_model=PaginatedResponse[ItemSummaryResponse],
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
) -> PaginatedResponse[ItemSummaryResponse]:
    items, total = await service.search_public_items(
        query=query,
        language_id=language_id,
        part_of_speech=part_of_speech,
        difficulty=difficulty,
        skip=skip,
        limit=limit,
    )
    return PaginatedResponse(
        data=[ItemSummaryResponse.model_validate(i) for i in items],
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
    )


@items_router.get(
    "/synonym-suggestions",
    response_model=list[str],
    summary="Autocomplete synonym term suggestions",
)
async def get_synonym_suggestions(
    service: ItemServiceDep,
    language_id: int = Query(..., gt=0),
    q: str = Query(..., min_length=1),
) -> list[str]:
    return await service.search_synonym_suggestions(language_id, q)


# ============================================================================
# ITEM CRUD — /{item_id} parameterized routes (after static routes)
# ============================================================================


@items_router.get(
    "/{item_id}",
    response_model=ItemDetailResponse,
    summary="Get a public item's full detail",
)
async def get_item(
    item_id: int,
    user: CurrentUser,
    service: ItemServiceDep,
) -> ItemDetailResponse:
    try:
        item = await service.get_public_item(user.id, item_id)
        return ItemDetailResponse.model_validate(item)
    except LingvoPalError as exc:
        _handle(exc)


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
    summary="Submit item for moderation review (DRAFT → COMMUNITY)",
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
    "/{item_id}/audio",
    response_model=ItemDetailResponse,
    summary="Upload audio pronunciation for an item",
)
async def upload_item_audio(
    item_id: int,
    user: CurrentUser,
    service: ItemServiceDep,
    storage: StorageDep,
    file: UploadFile = File(...),
) -> ItemDetailResponse:
    try:
        item = await service.upload_item_audio(user.id, item_id, file, storage)
        return ItemDetailResponse.model_validate(item)
    except LingvoPalError as exc:
        _handle(exc)


@items_router.post(
    "/{item_id}/context_audio",
    response_model=ItemDetailResponse,
    summary="Upload context audio for an item",
)
async def upload_item_context_audio(
    item_id: int,
    user: CurrentUser,
    service: ItemServiceDep,
    storage: StorageDep,
    file: UploadFile = File(...),
) -> ItemDetailResponse:
    try:
        item = await service.upload_item_context_audio(user.id, item_id, file, storage)
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
    user: CurrentUser,
    service: ItemServiceDep,
    storage: StorageDep,
    file: UploadFile = File(...),
) -> ItemDetailResponse:
    try:
        item = await service.upload_item_image(user.id, item_id, file, storage)
        return ItemDetailResponse.model_validate(item)
    except LingvoPalError as exc:
        _handle(exc)


@items_router.get(
    "/{item_id}/synonyms",
    response_model=list[str],
    summary="List synonym terms of an item",
)
async def get_item_synonyms(
    item_id: int,
    user: CurrentUser,
    service: ItemServiceDep,
) -> list[str]:
    try:
        return await service.get_synonyms(user.id, item_id)
    except LingvoPalError as exc:
        _handle(exc)


@items_router.put(
    "/{item_id}/synonyms",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Replace all synonym terms for an item",
)
async def set_item_synonyms(
    item_id: int,
    body: SynonymTermsRequest,
    user: CurrentUser,
    service: ItemServiceDep,
) -> None:
    try:
        await service.set_synonyms(user.id, item_id, body.terms)
    except LingvoPalError as exc:
        _handle(exc)


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


@items_router.post(
    "/{item_id}/report",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Report a community item",
    description=(
        "File a complaint against a COMMUNITY item. "
        "One report per user per item. "
        "Requires at least one completed study session. "
        "Rate-limited to MAX_COMPLAINTS_PER_DAY per day."
    ),
)
async def report_item(
    item_id: int,
    body: ComplaintRequest,
    user: CurrentUser,
    svc: ComplaintServiceDep,
) -> ComplaintResponse:
    try:
        complaint = await svc.file_item_complaint(
            user.id, item_id, body.reason, body.details
        )
        return ComplaintResponse.model_validate(complaint)
    except LingvoPalError as exc:
        _handle(exc)


# ============================================================================
# ITEMS WITHIN A SET  (/sets/{set_id}/items/*)
# ============================================================================


@set_items_router.get(
    "",
    response_model=PaginatedResponse[SetItemResponse],
    summary="List items in a set (with translations)",
)
async def get_set_items(
    set_id: int,
    user: CurrentUser,
    service: ItemServiceDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[SetItemResponse]:
    try:
        set_items, total = await service.get_set_items(
            user.id, set_id, skip=skip, limit=limit
        )
        return PaginatedResponse[SetItemResponse](
            data=[SetItemResponse.model_validate(si) for si in set_items],
            total=total,
            page=(skip // limit) + 1,
            page_size=limit,
        )
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
