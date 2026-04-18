# backend/app/schemas/user_settings.py
"""
UserSettings schemas — Pydantic request / response models only.

No business logic, no default values, no service imports.
"""

from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EvaluationMode, LearningIntensity, RetentionPriority
from app.schemas.user import LanguageRefResponse


# ============================================================================
# RESPONSE
# ============================================================================


class UserSettingsResponse(BaseModel):
    """Full settings for the authenticated user (GET /settings/me)."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int

    # Language settings
    native_language: LanguageRefResponse
    interface_language: LanguageRefResponse

    # Learning behaviour
    learning_intensity: LearningIntensity
    evaluation_mode: EvaluationMode
    show_hints_on_fails: bool

    # Scheduling
    daily_study_goal: int
    reminder_time: time | None
    streak_reminders_enabled: bool

    # UI preferences
    show_translations: bool
    show_images: bool
    show_synonyms: bool
    show_part_of_speech: bool
    auto_play_audio: bool

    # Advanced settings
    new_items_per_day_limit: int
    new_items_per_session: int
    retention_priority: RetentionPriority
    max_review_load_per_day: int | None

    # Timestamps
    created_at: datetime
    updated_at: datetime | None


# ============================================================================
# REQUEST — PATCH
# ============================================================================


class UserSettingsPatchRequest(BaseModel):
    """
    Partial update payload for PATCH /settings/me.

    All fields are optional; only explicitly supplied fields will be written.
    The service uses model_dump(exclude_unset=True) to derive the changeset.
    """

    # Language settings
    native_lang_id: int | None = Field(None, gt=0)
    interface_lang_id: int | None = Field(None, gt=0)

    # Learning behaviour
    learning_intensity: LearningIntensity | None = None
    evaluation_mode: EvaluationMode | None = None
    show_hints_on_fails: bool | None = None

    # Scheduling
    daily_study_goal: int | None = Field(None, ge=1, le=9999)
    reminder_time: time | None = None
    streak_reminders_enabled: bool | None = None

    # UI preferences
    show_translations: bool | None = None
    show_images: bool | None = None
    show_synonyms: bool | None = None
    show_part_of_speech: bool | None = None
    auto_play_audio: bool | None = None

    # Advanced settings
    new_items_per_day_limit: int | None = Field(None, ge=1, le=500)
    new_items_per_session: int | None = Field(None, ge=1, le=100)
    retention_priority: RetentionPriority | None = None
    max_review_load_per_day: int | None = Field(None, ge=1, le=9999)


__all__ = [
    "UserSettingsResponse",
    "UserSettingsPatchRequest",
]
