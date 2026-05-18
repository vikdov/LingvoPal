# backend/app/core/http_errors.py
"""
Shared domain-exception → HTTP-exception mapping.

Each route module can call `domain_error_to_http()` instead of maintaining
its own copy of the same isinstance chain.  Routes that need different
status codes for specific exceptions can pass keyword overrides.
"""

from typing import NoReturn

from fastapi import HTTPException, status

from app.core.exceptions import (
    BusinessRuleViolationError,
    ConcurrencyError,
    ContentValidationError,
    DuplicateResourceError,
    InvalidStateTransitionError,
    LingvoPalError,
    NoDueItemsError,
    NotAuthorizedError,
    ResourceNotFoundError,
)


def domain_error_to_http(
    exc: LingvoPalError,
    *,
    business_rule_status: int = status.HTTP_422_UNPROCESSABLE_ENTITY,
) -> NoReturn:
    """
    Translate a domain exception into an HTTPException and raise it.

    Args:
        exc: The domain exception to translate.
        business_rule_status: Override the default 422 for BusinessRuleViolationError.
            Use HTTP_409_CONFLICT for routes where a violated rule means "conflict"
            rather than "unprocessable entity" (e.g. moderation state transitions).
    """
    if isinstance(exc, ResourceNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, NotAuthorizedError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, ConcurrencyError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, (InvalidStateTransitionError, DuplicateResourceError)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, ContentValidationError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"field": exc.field, "reason": exc.reason},
        )
    if isinstance(exc, NoDueItemsError):
        raise HTTPException(
            status_code=business_rule_status,
            detail={
                "error": "no_due_items",
                "message": str(exc),
                "next_review_at": exc.next_review_at.isoformat() if exc.next_review_at else None,
            },
        )
    if isinstance(exc, BusinessRuleViolationError):
        raise HTTPException(status_code=business_rule_status, detail=str(exc))
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


__all__ = ["domain_error_to_http"]
