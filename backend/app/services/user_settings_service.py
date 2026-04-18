# backend/app/services/user_settings_service.py
"""
UserSettings service — all business logic for user preferences.

Responsibilities:
  - Single source of truth for default settings (get_default_settings)
  - Auto-creation of settings row when missing (get_or_create)
  - Safe PATCH merge: only update provided fields, validate full post-merge state
  - Reset preferences to defaults while preserving language identity settings
  - Language existence validation (native_lang_id / interface_lang_id)
  - Cross-field invariant enforcement

Architecture rules:
  - NEVER import schemas here
  - Repository is the only DB access layer
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, SettingsValidationError
from app.models.enums import EvaluationMode, LearningIntensity, RetentionPriority
from app.models.language import Language
from app.models.user import UserSettings
from app.repositories.user_settings_repo import UserSettingsRepository

logger = logging.getLogger(__name__)


# ============================================================================
# Defaults  — single source of truth
# ============================================================================


def get_default_settings() -> dict:
    """
    Canonical default values for all preference fields.

    Language IDs are NOT included here — they are identity data supplied at
    registration time.  Callers must merge them in separately.
    """
    return {
        # Learning behaviour
        "learning_intensity": LearningIntensity.BALANCED,
        "evaluation_mode": EvaluationMode.NORMAL,
        "show_hints_on_fails": True,
        # Scheduling
        "daily_study_goal": 20,
        "reminder_time": None,
        "streak_reminders_enabled": True,
        # UI preferences
        "show_translations": True,
        "show_images": True,
        "show_synonyms": True,
        "show_part_of_speech": True,
        "auto_play_audio": False,
        # Advanced settings
        "new_items_per_day_limit": 20,
        "new_items_per_session": 10,
        "retention_priority": RetentionPriority.BALANCED,
        "max_review_load_per_day": None,
    }


# ============================================================================
# Validation  (pure — easy to unit-test independently)
# ============================================================================


def _validate_patch(patch: dict) -> None:
    """
    Enforce domain invariants on the *patch* dict before applying it.

    Pydantic handles type/range coercion; this layer guards higher-level
    business rules (cross-field constraints) that Pydantic cannot express.

    Raises SettingsValidationError on the first violation.
    """
    goal = patch.get("daily_study_goal")
    per_session = patch.get("new_items_per_session")
    per_day_limit = patch.get("new_items_per_day_limit")
    max_review = patch.get("max_review_load_per_day")

    # Positivity guards (belt-and-suspenders; schema already enforces these)
    if goal is not None and goal < 1:
        raise SettingsValidationError("daily_study_goal", "must be ≥ 1")
    if per_session is not None and per_session < 1:
        raise SettingsValidationError("new_items_per_session", "must be ≥ 1")
    if per_day_limit is not None and per_day_limit < 1:
        raise SettingsValidationError("new_items_per_day_limit", "must be ≥ 1")
    if max_review is not None and max_review < 1:
        raise SettingsValidationError("max_review_load_per_day", "must be ≥ 1 or null")


def _validate_cross_field(merged: dict) -> None:
    """
    Validate the *complete merged* settings state after applying a patch.

    Called after merging patch onto current values so the full picture is
    available for relational constraints.
    """
    per_session = merged.get("new_items_per_session")
    per_day_limit = merged.get("new_items_per_day_limit")

    if (
        per_session is not None
        and per_day_limit is not None
        and per_session > per_day_limit
    ):
        raise SettingsValidationError(
            "new_items_per_session",
            f"cannot exceed new_items_per_day_limit ({per_day_limit})",
        )

    goal = merged.get("daily_study_goal")
    max_review = merged.get("max_review_load_per_day")
    if goal is not None and max_review is not None and goal > max_review:
        raise SettingsValidationError(
            "daily_study_goal",
            f"cannot exceed max_review_load_per_day ({max_review}). "
            "Increase the review load cap or lower the daily goal.",
        )


# ============================================================================
# Service
# ============================================================================


class UserSettingsService:
    """
    Stateless per-request service.
    Instantiated with a session; repository is constructed internally.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = UserSettingsRepository(session)

    # ── Language helper ────────────────────────────────────────────────────

    async def _assert_language_exists(self, lang_id: int, field: str) -> None:
        """Raise SettingsValidationError if language_id does not exist."""
        result = await self._session.execute(
            select(Language.id).where(Language.id == lang_id)
        )
        if result.scalar_one_or_none() is None:
            raise SettingsValidationError(field, f"language {lang_id} does not exist")

    async def _get_any_language_id(self) -> int:
        """
        Return the ID of any available language.

        Used only as a last-resort fallback when get_or_create is called
        for a user whose settings row is somehow missing (should be rare).
        Raises ResourceNotFoundError if no languages are seeded.
        """
        result = await self._session.execute(
            select(Language.id).order_by(Language.id.asc()).limit(1)
        )
        lang_id = result.scalar_one_or_none()
        if lang_id is None:
            raise ResourceNotFoundError("Language", "any — languages table is empty")
        return lang_id

    # ── Creation ──────────────────────────────────────────────────────────────

    async def create_for_user(
        self,
        user_id: int,
        native_lang_id: int,
        interface_lang_id: int,
    ) -> UserSettings:
        """
        Create a settings row for a newly registered user.

        Called by AuthService during signup (within the same transaction).
        Does NOT commit — caller owns the transaction boundary.
        """
        data = {
            "native_lang_id": native_lang_id,
            "interface_lang_id": interface_lang_id,
            **get_default_settings(),
        }
        return await self._repo.create(user_id=user_id, data=data)

    # ── Reads ──────────────────────────────────────────────────────────────

    async def get_or_create(self, user_id: int) -> UserSettings:
        """
        Return existing settings, or create with defaults if somehow missing.

        The settings row should always exist after signup. This guard handles
        edge cases (e.g. backfills, corrupted registration transactions).
        Commits if a new row was inserted.
        """
        settings = await self._repo.get_by_user_id(user_id, load_languages=True)
        if settings is not None:
            return settings

        # Row missing — create with defaults and a fallback language
        logger.warning(
            "settings_row_missing_creating_defaults",
            extra={"user_id": user_id},
        )
        fallback_lang_id = await self._get_any_language_id()
        data = {
            "native_lang_id": fallback_lang_id,
            "interface_lang_id": fallback_lang_id,
            **get_default_settings(),
        }
        await self._repo.create(user_id=user_id, data=data)
        await self._session.commit()
        return await self._repo.get_by_user_id(user_id, load_languages=True)  # type: ignore[return-value]

    # ── Updates ────────────────────────────────────────────────────────────

    async def update_settings(
        self,
        user_id: int,
        patch_data: dict,
    ) -> UserSettings:
        """
        Apply a partial update to the user's settings.

        Steps:
          1. Validate language IDs if provided (existence check in DB).
          2. Validate the patch dict in isolation (range/type guards).
          3. Fetch current settings.
          4. Merge patch onto current values.
          5. Validate the merged state (cross-field constraints).
          6. Persist only the changed fields.
          7. Commit and return the refreshed row.

        Raises:
          SettingsValidationError — on any invariant violation.
          ResourceNotFoundError  — if language IDs don't exist.
        """
        if not patch_data:
            return await self.get_or_create(user_id)

        # 1. Language existence checks (before touching the DB row)
        if "native_lang_id" in patch_data:
            await self._assert_language_exists(patch_data["native_lang_id"], "native_lang_id")
        if "interface_lang_id" in patch_data:
            await self._assert_language_exists(patch_data["interface_lang_id"], "interface_lang_id")

        # 2. Patch-level validation
        _validate_patch(patch_data)

        # 3. Fetch current settings (create if missing — defensive)
        current = await self._repo.get_by_user_id(user_id, load_languages=False)
        if current is None:
            fallback_lang_id = (
                patch_data.get("native_lang_id") or await self._get_any_language_id()
            )
            interface_lang_id = patch_data.get("interface_lang_id", fallback_lang_id)
            await self.create_for_user(
                user_id=user_id,
                native_lang_id=fallback_lang_id,
                interface_lang_id=interface_lang_id,
            )
            await self._session.commit()
            current = await self._repo.get_by_user_id(user_id, load_languages=False)

        # 4. Build merged view for cross-field validation (read-only, no mutation)
        current_dict = {
            col.key: getattr(current, col.key)
            for col in current.__table__.columns
            if col.key not in ("user_id", "created_at", "updated_at")
        }
        merged = {**current_dict, **patch_data}

        # 5. Cross-field validation on merged state
        _validate_cross_field(merged)

        # 6. Persist and commit
        updated = await self._repo.update(user_id, patch_data, load_languages=True)
        await self._session.commit()
        return updated  # type: ignore[return-value]

    async def reset_settings(self, user_id: int) -> UserSettings:
        """
        Reset all preference fields to defaults.

        Language settings (native_lang_id / interface_lang_id) are preserved
        — they are identity data, not changeable preferences.
        Commits the transaction.
        """
        updated = await self._repo.update(
            user_id, get_default_settings(), load_languages=True
        )
        await self._session.commit()
        return updated  # type: ignore[return-value]


__all__ = ["UserSettingsService", "get_default_settings"]
