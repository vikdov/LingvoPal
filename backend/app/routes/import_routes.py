"""
Import routes — Anki .apkg and .lpset import.

Anki two-phase flow:
  POST /import/anki/preview  → parse file, cache cards in Redis, return summary
  POST /import/anki/confirm  → load from cache, create set + items + translations

LPSet single-phase flow:
  POST /import/lpset  → parse bundle, create set + items + translations, add to library
"""

from typing import Annotated, NoReturn

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.core.dependencies import (
    CurrentUser,
    WriteDBSession,
    get_redis_client,
    get_storage_service,
)
from app.core.exceptions import BusinessRuleViolationError, LingvoPalError, ResourceNotFoundError
from app.models.enums import ContentStatus
from app.repositories.set_repo import SetRepository
from app.schemas.anki_import import AnkiConfirmRequest, AnkiImportResponse, AnkiPreviewResponse
from app.services.anki_import_service import AnkiImportService
from app.services.anki_parser import parse_apkg
from app.services.lpset_import_service import LpsetImportError, LpsetImportService
from app.services.storage import StorageService

router = APIRouter(prefix="/import", tags=["import"])

_MAX_APKG_BYTES = 100 * 1024 * 1024  # 100 MB


def _get_anki_import_service(
    db: WriteDBSession,
    redis: Annotated[aioredis.Redis, Depends(get_redis_client)],
    storage: Annotated[StorageService, Depends(get_storage_service)],
) -> AnkiImportService:
    return AnkiImportService(session=db, redis=redis, storage=storage)


AnkiImportServiceDep = Annotated[AnkiImportService, Depends(_get_anki_import_service)]


def _handle(exc: LingvoPalError) -> NoReturn:
    if isinstance(exc, ResourceNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, BusinessRuleViolationError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/anki/preview",
    response_model=AnkiPreviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze an Anki .apkg file and return a summary",
)
async def preview_anki_import(
    file: UploadFile,
    user: CurrentUser,
    service: AnkiImportServiceDep,
) -> AnkiPreviewResponse:
    filename = file.filename or ""
    if not filename.lower().endswith(".apkg"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File must be an Anki package (.apkg)",
        )

    file_bytes = await file.read(_MAX_APKG_BYTES + 1)
    if len(file_bytes) > _MAX_APKG_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds 100 MB limit",
        )

    if not file_bytes[:4].startswith(b"PK\x03\x04"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File is not a valid ZIP archive",
        )

    try:
        result = parse_apkg(file_bytes)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return await service.store_and_build_preview(file_bytes, result)


@router.post(
    "/anki/confirm",
    response_model=AnkiImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a set from a previously analyzed .apkg",
)
async def confirm_anki_import(
    body: AnkiConfirmRequest,
    user: CurrentUser,
    service: AnkiImportServiceDep,
) -> AnkiImportResponse:
    try:
        return await service.confirm_import(user.id, body)
    except LingvoPalError as exc:
        _handle(exc)


_MAX_LPSET_BYTES = 100 * 1024 * 1024  # 100 MB


@router.post(
    "/lpset",
    status_code=status.HTTP_201_CREATED,
    summary="Import a .lpset bundle as a personal draft set",
)
async def import_lpset(
    file: UploadFile,
    user: CurrentUser,
    db: WriteDBSession,
) -> dict:
    filename = file.filename or ""
    if not filename.lower().endswith(".lpset"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File must be a LingvoPal set bundle (.lpset)",
        )

    file_bytes = await file.read(_MAX_LPSET_BYTES + 1)
    if len(file_bytes) > _MAX_LPSET_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds 100 MB limit",
        )

    svc = LpsetImportService(db)
    try:
        result = await svc.import_lpset(file_bytes, user_id=user.id, status=ContentStatus.DRAFT)
    except LpsetImportError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    await SetRepository(db).save_to_library(user.id, result["set_id"])
    await db.commit()
    return result
