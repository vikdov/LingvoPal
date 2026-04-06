# backend/app/schemas/auth.py
"""
Authentication schemas.

Request: What client sends to login/signup
Response: What API returns (token + user info)
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from app.schemas.user import UserPrivateResponse


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================
def _validate_password_strength(password: str) -> str:
    """Helper: Validate password meets minimum requirements"""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not any(c.isupper() for c in password):
        raise ValueError("Password must contain uppercase")
    if not any(c.isdigit() for c in password):
        raise ValueError("Password must contain digit")
    if not any(c in "!@#$%^&*" for c in password):
        raise ValueError("Password must contain special character")
    return password


class SignupRequest(BaseModel):
    """POST /api/v1/auth/signup"""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (8-128 chars)",
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern="^[a-zA-Z0-9_-]+$",
        description="Display name (alphanumeric, _, - only)",
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        return _validate_password_strength(v)


class LoginRequest(BaseModel):
    """POST /api/v1/auth/login"""

    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="Password (plain text)")


class PasswordChangeRequest(BaseModel):
    """POST /api/v1/auth/change-password"""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password",
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v):
        return _validate_password_strength(v)


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class TokenResponse(BaseModel):
    """Login/signup response with JWT token"""

    access_token: str = Field(..., description="JWT bearer token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")
    user: "UserPrivateResponse" = Field(..., description="Authenticated user")


class AuthErrorResponse(BaseModel):
    """Auth-specific error (invalid credentials)"""

    error: str = Field(..., description="Error code (e.g., 'invalid_credentials')")
    message: str = Field(..., description="Human-readable message")


__all__ = [
    "SignupRequest",
    "LoginRequest",
    "PasswordChangeRequest",
    "TokenResponse",
    "AuthErrorResponse",
]
