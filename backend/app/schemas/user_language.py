# backend/app/schemas/user_language.py
"""Schemas for user language management."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import LanguageRefResponse


class UserLanguageResponse(BaseModel):
    """One language a user is learning."""

    model_config = ConfigDict(from_attributes=True)

    language: LanguageRefResponse
    is_active: bool
    created_at: datetime


class UserLanguagesResponse(BaseModel):
    """All languages the user is learning, plus active language."""

    languages: list[UserLanguageResponse]
    active_language: LanguageRefResponse | None


class AddUserLanguageRequest(BaseModel):
    """Add a new learning language for the current user."""

    language_id: int = Field(..., gt=0)
    set_active: bool = Field(
        default=True,
        description="Immediately set as the active learning language",
    )


__all__ = [
    "UserLanguageResponse",
    "UserLanguagesResponse",
    "AddUserLanguageRequest",
]
