# backend/app/schemas/user.py
"""
User profile schemas with privacy controls.

- PublicResponse: What other users see
- PrivateResponse: What you see about yourself
- DetailResponse: Private + settings
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

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

    username: Optional[str] = Field(
        None,
        min_length=3,
        max_length=50,
        pattern="^[a-zA-Z0-9_-]+$",
    )
    # No email update (requires verification flow)
    # No password update (separate endpoint)


class UserSettingsUpdateRequest(BaseModel):
    """PATCH /api/v1/users/me/settings"""

    native_language_id: Optional[int] = Field(None, gt=0)
    interface_language_id: Optional[int] = Field(None, gt=0)


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


class UserPrivateResponse(BaseResponseWithDeleted):
    """
    Private profile (what you see about yourself).

    Full data:
    - Email, verification status, admin flag
    - But no passwords, no internal audit fields
    """

    username: str
    email: str
    email_verified: bool
    is_admin: bool
    model_config = ConfigDict(from_attributes=True)


class LanguageRefResponse(BaseModel):
    """Nested response for language references"""

    id: int
    code: str = Field(..., description="ISO 639-1 code (e.g., 'en', 'es')")
    name: str = Field(..., description="Language name (e.g., 'English')")

    model_config = ConfigDict(from_attributes=True)


class UserSettingsResponse(BaseModel):
    """User's preferences and configuration"""

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

    settings: Optional[UserSettingsResponse] = None


__all__ = [
    "UserUpdateRequest",
    "UserSettingsUpdateRequest",
    "UserPublicResponse",
    "UserPrivateResponse",
    "UserDetailResponse",
    "UserSettingsResponse",
    "LanguageRefResponse",
]
