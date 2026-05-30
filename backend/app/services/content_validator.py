# backend/app/services/content_validator.py
"""
Automated content quality checks run before a submission enters the moderation queue.

All functions are pure (no I/O). Raise ContentValidationError on hard failures.
Language detection mismatches are soft — logged by caller, not raised.
"""

import logging

from app.core.exceptions import ContentValidationError

logger = logging.getLogger(__name__)

_TERM_MIN = 1
_TERM_MAX = 200
_CONTEXT_MAX = 500


def check_length(term: str, context: str | None) -> None:
    """Hard-block: term and context must be within allowed character limits."""
    if len(term) < _TERM_MIN or len(term) > _TERM_MAX:
        raise ContentValidationError(
            "term", f"must be between {_TERM_MIN} and {_TERM_MAX} characters"
        )
    if context is not None and len(context) > _CONTEXT_MAX:
        raise ContentValidationError("context", f"must not exceed {_CONTEXT_MAX} characters")


def check_profanity(
    term: str,
    context: str | None,
    term_field: str = "term",
    context_field: str = "context",
) -> None:
    """Hard-block: term or context must not contain profanity (English wordlist only)."""
    try:
        from better_profanity import profanity  # type: ignore[import-untyped]

        if profanity.contains_profanity(term):
            raise ContentValidationError(term_field, "contains inappropriate language")
        if context and profanity.contains_profanity(context):
            raise ContentValidationError(context_field, "contains inappropriate language")
    except ImportError:
        logger.warning("better-profanity not installed — profanity check skipped")


def detect_language_mismatch(term: str, expected_lang_code: str) -> bool:
    """
    Soft check: returns True if detected language likely differs from expected.
    Caller decides whether to log or warn — never raises.
    Unreliable for short terms (single words); treat result as a hint only.
    """
    try:
        from langdetect import detect  # type: ignore[import-untyped]

        detected = detect(term)
        return detected != expected_lang_code
    except Exception:
        return False


def validate_item(
    term: str,
    context: str | None,
    expected_lang_code: str,
) -> bool:
    """
    Run all pre-submission checks for an item.
    Raises ContentValidationError on hard failures.
    Returns True if a language mismatch was detected (soft warning).
    """
    check_length(term, context)
    check_profanity(term, context)
    return detect_language_mismatch(term, expected_lang_code)


def validate_set(title: str, description: str | None) -> None:
    """
    Run pre-submission checks for a set.
    Raises ContentValidationError on hard failures.
    Sets only get length + profanity checks (no language detection).
    """
    if len(title) < 1 or len(title) > _TERM_MAX:
        raise ContentValidationError("title", f"must be between 1 and {_TERM_MAX} characters")
    if description is not None and len(description) > _CONTEXT_MAX:
        raise ContentValidationError("description", f"must not exceed {_CONTEXT_MAX} characters")
    check_profanity(title, description, term_field="title", context_field="description")


__all__ = ["validate_item", "validate_set", "ContentValidationError"]
