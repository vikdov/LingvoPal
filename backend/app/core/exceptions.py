# backend/app/core/exceptions.py
"""
Domain exceptions for LingvoPal.

Hierarchy:
  LingvoPalError
  ├── AuthError               ← authentication / authorisation domain
  │   ├── InvalidCredentialsError
  │   ├── EmailAlreadyExistsError
  │   ├── UsernameAlreadyExistsError
  │   ├── SamePasswordError
  │   └── AccountDisabledError
  ├── ResourceNotFoundError
  ├── NotAuthorizedError
  │   └── NotAuthorizedToStudyError
  └── BusinessRuleViolationError
      ├── ConcurrencyError
      ├── InvalidStateTransitionError
      └── DuplicateResourceError

Services raise these. Routers catch and translate to HTTP responses.
"""

from enum import Enum


# ============================================================================
# AUTH ERROR CODES
# ============================================================================


class AuthErrorCode(str, Enum):
    INVALID_CREDENTIALS = "invalid_credentials"
    EMAIL_ALREADY_EXISTS = "email_already_exists"
    USERNAME_ALREADY_EXISTS = "username_already_exists"
    ACCOUNT_DISABLED = "account_disabled"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_INVALID = "token_invalid"
    PASSWORD_SAME_AS_CURRENT = "password_same_as_current"


# ============================================================================
# BASE
# ============================================================================


class LingvoPalError(Exception):
    """Base exception for all domain errors."""

    status_code = 500  # Default to Server Error


# ============================================================================
# AUTH DOMAIN
# ============================================================================


class AuthError(LingvoPalError):
    """Base for authentication / authorisation errors."""

    def __init__(self, code: AuthErrorCode, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class InvalidCredentialsError(AuthError):
    def __init__(self) -> None:
        super().__init__(
            AuthErrorCode.INVALID_CREDENTIALS,
            "Invalid email or password.",
        )


class EmailAlreadyExistsError(AuthError):
    def __init__(self) -> None:
        super().__init__(
            AuthErrorCode.EMAIL_ALREADY_EXISTS,
            "An account with this email already exists.",
        )


class UsernameAlreadyExistsError(AuthError):
    def __init__(self) -> None:
        super().__init__(
            AuthErrorCode.USERNAME_ALREADY_EXISTS,
            "This username is already taken.",
        )


class SamePasswordError(AuthError):
    def __init__(self) -> None:
        super().__init__(
            AuthErrorCode.PASSWORD_SAME_AS_CURRENT,
            "New password must differ from the current password.",
        )


class AccountDisabledError(AuthError):
    def __init__(self) -> None:
        super().__init__(
            AuthErrorCode.ACCOUNT_DISABLED,
            "This account has been disabled.",
        )


# ============================================================================
# RESOURCE / AUTHORISATION
# ============================================================================


class ResourceNotFoundError(LingvoPalError):
    def __init__(self, resource: str, resource_id: int | str) -> None:
        self.resource = resource
        self.resource_id = resource_id
        super().__init__(f"{resource} '{resource_id}' not found")


class NotAuthorizedError(LingvoPalError):
    def __init__(self, action: str, reason: str = "") -> None:
        self.action = action
        super().__init__(f"Not authorized to {action}. {reason}".strip())


class NotAuthorizedToStudyError(NotAuthorizedError):
    def __init__(self, set_id: int, user_id: int) -> None:
        super().__init__(f"study set {set_id}", f"(user {user_id})")
        self.set_id = set_id
        self.user_id = user_id


# ============================================================================
# BUSINESS RULES
# ============================================================================


class BusinessRuleViolationError(LingvoPalError):
    def __init__(self, rule: str) -> None:
        self.rule = rule
        super().__init__(f"Business rule violated: {rule}")


class ConcurrencyError(BusinessRuleViolationError):
    def __init__(self, model: str, record_id: int) -> None:
        self.model = model
        self.record_id = record_id
        super().__init__(f"concurrent modification of {model} {record_id}")


class InvalidStateTransitionError(BusinessRuleViolationError):
    def __init__(self, current_status: str, requested_status: str) -> None:
        super().__init__(
            f"Cannot transition from '{current_status}' to '{requested_status}'"
        )
        self.current_status = current_status
        self.requested_status = requested_status


class DuplicateResourceError(BusinessRuleViolationError):
    def __init__(self, resource: str, field: str, value: str) -> None:
        super().__init__(f"{resource} with {field}='{value}' already exists")
        self.resource = resource
        self.field = field
        self.value = value


class SettingsValidationError(BusinessRuleViolationError):
    """Raised when a settings update violates a domain invariant."""

    def __init__(self, field: str, reason: str) -> None:
        super().__init__(f"Invalid value for '{field}': {reason}")
        self.field = field
        self.reason = reason


__all__ = [
    # Base
    "LingvoPalError",
    # Auth codes
    "AuthErrorCode",
    # Auth
    "AuthError",
    "InvalidCredentialsError",
    "EmailAlreadyExistsError",
    "UsernameAlreadyExistsError",
    "SamePasswordError",
    "AccountDisabledError",
    # Resource / authorisation
    "ResourceNotFoundError",
    "NotAuthorizedError",
    "NotAuthorizedToStudyError",
    # Business rules
    "BusinessRuleViolationError",
    "ConcurrencyError",
    "InvalidStateTransitionError",
    "DuplicateResourceError",
    "SettingsValidationError",
]
