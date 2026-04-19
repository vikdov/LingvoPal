# backend/app/core/security.py
"""
Pure cryptographic utilities — no business logic, no DB, no user concepts.

Responsibilities:
  - Password hashing / verification (via passlib/bcrypt)
  - JWT encode / decode (via PyJWT)
  - Password strength validation (reusable rule set)

Hard rule: nothing here ever asks "does this user exist?"
"""

from typing import Any

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext

from app.core.config import get_settings

# ============================================================================
# PASSWORD HASHING
# ============================================================================

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain-text password. Never store the plain-text version."""
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Constant-time comparison via passlib.
    Safe to call with a dummy hash when no user is found (timing-attack mitigation).
    """
    return _pwd_context.verify(plain_password, hashed_password)


# ============================================================================
# JWT  —  encode/decode only, no payload decisions
# ============================================================================


class TokenExpiredError(Exception):
    """JWT has a valid signature but the exp claim is in the past."""


class TokenInvalidError(Exception):
    """JWT is malformed, has an invalid signature, or is missing required claims."""


def encode_token(payload: dict[str, Any]) -> str:
    """
    Encode a JWT from an arbitrary payload dict.

    Caller (auth_service) is responsible for building the payload structure.
    Raises ValueError if 'exp' claim is missing — non-expiring tokens are not allowed.
    """
    if "exp" not in payload:
        raise ValueError("JWT payload must include 'exp' claim")
    settings = get_settings()
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and verify a JWT.

    Raises:
        TokenExpiredError: signature is valid but the token has expired
        TokenInvalidError: malformed token, bad signature, or missing claims
    """
    settings = get_settings()
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except ExpiredSignatureError as exc:
        raise TokenExpiredError from exc
    except InvalidTokenError as exc:
        raise TokenInvalidError from exc


# ============================================================================
# PASSWORD STRENGTH VALIDATION
# ============================================================================


def validate_password_strength(password: str) -> list[str]:
    """
    Returns a list of unmet requirement strings.
    Empty list → password is valid.

    Used by:
      - schemas/auth.py  (Pydantic AfterValidator)
      - Directly in services if needed
    """
    errors: list[str] = []
    if len(password.encode()) > 72:
        errors.append("at most 72 bytes")
    if len(password) < 8:
        errors.append("at least 8 characters")
    if not any(c.isupper() for c in password):
        errors.append("at least one uppercase letter")
    if not any(c.islower() for c in password):
        errors.append("at least one lowercase letter")
    if not any(c.isdigit() for c in password):
        errors.append("at least one digit")
    if not any(c in "!@#$%^&*+-" for c in password):
        errors.append("at least one special character (!@#$%^&*+-)")
    return errors


__all__ = [
    "hash_password",
    "verify_password",
    "encode_token",
    "decode_token",
    "TokenExpiredError",
    "TokenInvalidError",
    "validate_password_strength",
]
