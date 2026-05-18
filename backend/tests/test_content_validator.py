# backend/tests/test_content_validator.py
"""Tests for automated pre-submission content validation."""

import pytest

from app.core.exceptions import ContentValidationError
from app.services.content_validator import (
    check_length,
    check_profanity,
    validate_item,
    validate_set,
)

# ============================================================================
# check_length
# ============================================================================


def test_length_valid_term():
    check_length("hello", None)  # no raise


def test_length_valid_term_and_context():
    check_length("hello", "Use it in a sentence.")  # no raise


def test_length_empty_term_raises():
    with pytest.raises(ContentValidationError) as exc_info:
        check_length("", None)
    assert exc_info.value.field == "term"


def test_length_term_too_long_raises():
    with pytest.raises(ContentValidationError) as exc_info:
        check_length("x" * 201, None)
    assert exc_info.value.field == "term"


def test_length_context_too_long_raises():
    with pytest.raises(ContentValidationError) as exc_info:
        check_length("hello", "x" * 501)
    assert exc_info.value.field == "context"


def test_length_context_none_skipped():
    check_length("hello", None)  # None context always valid


def test_length_context_exactly_at_limit():
    check_length("hello", "x" * 500)  # no raise


def test_length_term_exactly_at_limit():
    check_length("x" * 200, None)  # no raise


# ============================================================================
# check_profanity
# ============================================================================


def test_profanity_clean_content():
    check_profanity("apple", "The apple is red.")  # no raise


def test_profanity_dirty_term_raises():
    with pytest.raises(ContentValidationError) as exc_info:
        check_profanity("shit", None)
    assert exc_info.value.field == "term"


def test_profanity_dirty_context_raises():
    with pytest.raises(ContentValidationError) as exc_info:
        check_profanity("apple", "This is a shit example.")
    assert exc_info.value.field == "context"


def test_profanity_none_context_skipped():
    check_profanity("apple", None)  # no raise


# ============================================================================
# validate_item
# ============================================================================


def test_validate_item_english_correct_lang():
    mismatch = validate_item("apple", "The apple is red.", "en")
    assert isinstance(mismatch, bool)


def test_validate_item_blocks_empty_term():
    with pytest.raises(ContentValidationError) as exc_info:
        validate_item("", None, "en")
    assert exc_info.value.field == "term"


def test_validate_item_blocks_profane_term():
    with pytest.raises(ContentValidationError) as exc_info:
        validate_item("shit", None, "en")
    assert exc_info.value.field == "term"


def test_validate_item_returns_bool():
    result = validate_item("dog", None, "en")
    assert result is True or result is False


# ============================================================================
# validate_set
# ============================================================================


def test_validate_set_valid():
    validate_set("My Vocabulary Set", "Learn basic words.")  # no raise


def test_validate_set_empty_title_raises():
    with pytest.raises(ContentValidationError) as exc_info:
        validate_set("", None)
    assert exc_info.value.field == "title"


def test_validate_set_title_too_long_raises():
    with pytest.raises(ContentValidationError) as exc_info:
        validate_set("x" * 201, None)
    assert exc_info.value.field == "title"


def test_validate_set_description_too_long_raises():
    with pytest.raises(ContentValidationError) as exc_info:
        validate_set("My Set", "x" * 501)
    assert exc_info.value.field == "description"


def test_validate_set_profane_title_raises():
    with pytest.raises(ContentValidationError) as exc_info:
        validate_set("shit words", None)
    assert exc_info.value.field == "title"
