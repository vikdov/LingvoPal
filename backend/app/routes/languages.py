# backend/app/routes/languages.py
"""
Language reference routes.

Read-only — languages are seeded data, not user-created.
Used primarily by the frontend to populate language dropdowns
in registration and settings forms.
"""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.dependencies import DBSession
from app.models.language import Language
from app.schemas.language import LanguageResponse as LanguageRefResponse

router = APIRouter(prefix="/languages", tags=["languages"])


@router.get(
    "",
    response_model=list[LanguageRefResponse],
    summary="List all available languages",
)
async def list_languages(db: DBSession) -> list[LanguageRefResponse]:
    """Return every language supported by the platform, ordered by name."""
    result = await db.execute(select(Language).order_by(Language.name.asc()))
    languages = result.scalars().all()
    return [LanguageRefResponse.model_validate(lang) for lang in languages]


@router.get(
    "/{language_id}",
    response_model=LanguageRefResponse,
    summary="Get a single language by ID",
)
async def get_language(language_id: int, db: DBSession) -> LanguageRefResponse:
    lang = await db.get(Language, language_id)
    if lang is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Language {language_id} not found")
    return LanguageRefResponse.model_validate(lang)
