"""
Import routes — Anki .apkg deck import.

Two-phase flow:
  POST /import/anki/preview  → parse file, cache cards in Redis, return summary
  POST /import/anki/confirm  → load from cache, create set + items + translations
"""

from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

import redis.asyncio as aioredis

from app.core.dependencies import (
    CurrentUser,
    WriteDBSession,
    get_redis_client,
    get_storage_service,
)
from app.core.exceptions import BusinessRuleViolationError, LingvoPalError, ResourceNotFoundError
from app.schemas.anki_import import AnkiConfirmRequest, AnkiImportResponse, AnkiPreviewResponse
from app.services.anki_import_service import AnkiImportService
from app.services.anki_parser import parse_apkg
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
