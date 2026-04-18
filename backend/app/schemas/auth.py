# backend/app/schemas/auth.py
"""
Authentication schemas.

Request: What client sends to login/signup
Response: What API returns (token + user info)
"""

from enum import Enum
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    AfterValidator,
)

from app.core.security import validate_password_strength
from app.schemas.user import UserPrivateResponse


# ============================================================================
# REUSABLE ANNOTATED TYPES
# ============================================================================


def _password_validator(password: str) -> str:
    """Pydantic AfterValidator: wraps security.py checker, raises on failure."""
    errors = validate_password_strength(password)
    if errors:
        raise ValueError("Password must contain: " + ", ".join(errors))
    return password


# Reusable annotated type — attach once, use everywhere.
# AfterValidator runs *after* min/max length checks from Field constraints.
StrongPassword = Annotated[
    str,
    Field(min_length=8, max_length=128, description="Password (8–128 chars)"),
    AfterValidator(_password_validator),
]

NormalizedEmail = Annotated[
    EmailStr,
    AfterValidator(lambda v: v.lower().strip()),
]


# ============================================================================
# AUTH ERROR CODE ENUM
# ============================================================================


class AuthErrorCode(str, Enum):
    """
    Exhaustive list of auth-domain error codes.
    str-mixin ensures JSON serialization produces the string value directly.
    """

    INVALID_CREDENTIALS = "invalid_credentials"
    EMAIL_ALREADY_EXISTS = "email_already_exists"
    USERNAME_ALREADY_EXISTS = "username_already_exists"
    ACCOUNT_DISABLED = "account_disabled"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_INVALID = "token_invalid"
    PASSWORD_SAME_AS_CURRENT = "password_same_as_current"


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================


class SignupRequest(BaseModel):
    """POST /api/v1/auth/signup"""

    model_config = ConfigDict(
        str_strip_whitespace=True,  # trim accidental leading/trailing spaces
        str_max_length=256,  # hard global ceiling on any string field
    )

    email: NormalizedEmail = Field(..., description="User email address")
    password: StrongPassword
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Display name (alphanumeric, _, - only)",
    )
    native_lang_id: int = Field(..., gt=0, description="User's native language ID")
    interface_lang_id: int | None = Field(
        None, gt=0, description="Interface language ID (defaults to native language)"
    )


class LoginRequest(BaseModel):
    """POST /api/v1/auth/login"""

    model_config = ConfigDict(str_strip_whitespace=True)

    email: NormalizedEmail = Field(..., description="User email")
    # Bounded to prevent DoS; no complexity check (we verify against hash)
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Password (plain text)",
    )


class PasswordChangeRequest(BaseModel):
    """POST /api/v1/auth/change-password"""

    model_config = ConfigDict(str_strip_whitespace=True)

    current_password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Current password",
    )
    new_password: StrongPassword

    @field_validator("new_password", mode="after")
    @classmethod
    def new_must_differ_from_current(cls, v: str, info) -> str:
        """
        Catch the trivial case at schema level.
        Note: this is a best-effort check on raw strings — the service layer
        must re-check against the stored hash for correctness.
        """
        current = info.data.get("current_password")
        if current and v == current:
            raise ValueError("New password must differ from the current password")
        return v


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class TokenResponse(BaseModel):
    """Login / signup success response containing a JWT bearer token."""

    model_config = ConfigDict(frozen=True)  # responses are immutable value objects

    access_token: str = Field(..., description="JWT bearer token")
    token_type: str = Field(
        default="bearer", description="Token type (always 'bearer')"
    )
    expires_in: int = Field(..., gt=0, description="Token lifetime in seconds")
    user: UserPrivateResponse = Field(..., description="Authenticated user data")


class AuthErrorResponse(BaseModel):
    """Auth-domain error response (e.g., invalid credentials, duplicate email)."""

    model_config = ConfigDict(frozen=True)

    error: AuthErrorCode = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable explanation")


__all__ = [
    # Types
    "StrongPassword",
    "NormalizedEmail",
    "AuthErrorCode",
    # Requests
    "SignupRequest",
    "LoginRequest",
    "PasswordChangeRequest",
    # Responses
    "TokenResponse",
    "AuthErrorResponse",
]
