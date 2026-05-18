# backend/app/schemas/user.py
"""
User profile schemas with privacy controls.

- PublicResponse: What other users see
- PrivateResponse: What you see about yourself (also used in auth token response)
- DetailResponse: Private + settings
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import BaseResponseWithDeleted


class UserPublicReference(BaseModel):
    id: int
    username: str
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# INPUT SCHEMAS
# ============================================================================


class UserUpdateRequest(BaseModel):
    """PATCH /api/v1/users/me"""

    username: str | None = Field(
        None,
        min_length=3,
        max_length=50,
        pattern="^[a-zA-Z0-9_-]+$",
    )
    # No email update (requires verification flow)
    # No password update (separate endpoint)


# ============================================================================
# OUTPUT SCHEMAS
# ============================================================================


class UserPublicResponse(BaseResponseWithDeleted):
    """
    Public profile (what other users see).

    Limited data:
    - Only ID, username, created_at
    - No email, no private info
    """

    username: str
    model_config = ConfigDict(from_attributes=True)


class UserPrivateResponse(BaseModel):
    """
    Private profile — returned by both /me and auth token responses.

    No audit timestamps (updated_at / deleted_at are internal).
    """

    id: int
    created_at: datetime
    username: str | None
    email: str
    email_verified: bool
    pending_email: str | None = None
    is_admin: bool
    native_lang_id: int
    active_target_lang_id: int | None
    model_config = ConfigDict(from_attributes=True)


class LanguageRefResponse(BaseModel):
    """Nested response for language references"""

    id: int
    code: str = Field(..., description="ISO 639-1 code (e.g., 'en', 'es')")
    name: str = Field(..., description="Language name (e.g., 'English')")

    model_config = ConfigDict(from_attributes=True)


class UserSettingsEmbedded(BaseModel):
    """Minimal settings embedded inside UserDetailResponse."""

    user_id: int
    native_language: LanguageRefResponse
    interface_language: LanguageRefResponse
    model_config = ConfigDict(from_attributes=True)


class UserDetailResponse(UserPrivateResponse):
    """
    Full user details with relationships.

    Includes: settings
    Not included: audit logs, full relationship expansion
    """

    settings: UserSettingsEmbedded | None = None


__all__ = [
    "UserUpdateRequest",
    "UserPublicResponse",
    "UserPrivateResponse",
    "UserDetailResponse",
    "UserSettingsEmbedded",
    "LanguageRefResponse",
]
