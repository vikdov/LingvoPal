# backend/app/core/security.py
"""
Pure cryptographic utilities — no business logic, no DB, no user concepts.

Responsibilities:
  - Password hashing / verification (via passlib/bcrypt)
  - JWT encode / decode (via python-jose)
  - Password strength validation (reusable rule set)

Hard rule: nothing here ever asks "does this user exist?"
"""

from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

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


def encode_token(payload: dict[str, Any]) -> str:
    """
    Encode a JWT from an arbitrary payload dict.

    Caller (auth_service) is responsible for building the payload structure.
    This function only handles signing.
    """
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any] | None:
    """
    Decode and verify a JWT.
    Returns the payload dict or None if the token is invalid / expired.
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


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
        errors.append("at most 72 characters")
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
    "validate_password_strength",
]
