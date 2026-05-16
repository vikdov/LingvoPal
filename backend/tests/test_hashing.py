# backend/tests/test_hashing.py
"""
Unit tests for item content fingerprinting.

No DB, no mocks — pure function calls only.

Test groups:
  - compute_item_content_hash(): deterministic output, sensitivity to each
    input dimension, normalization (case, whitespace, unicode), homograph
    deduplication, None context handling
"""

import pytest

from app.services.hashing import compute_item_content_hash


class TestComputeItemContentHash:
    def test_returns_hex_string(self) -> None:
        result = compute_item_content_hash(1, "bank", "Money in the bank.")
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex digest

    def test_deterministic(self) -> None:
        a = compute_item_content_hash(1, "bank", "Money in the bank.")
        b = compute_item_content_hash(1, "bank", "Money in the bank.")
        assert a == b

    def test_different_language_id_produces_different_hash(self) -> None:
        a = compute_item_content_hash(1, "bank", "Money in the bank.")
        b = compute_item_content_hash(2, "bank", "Money in the bank.")
        assert a != b

    def test_different_term_produces_different_hash(self) -> None:
        a = compute_item_content_hash(1, "bank", "Money in the bank.")
        b = compute_item_content_hash(1, "river", "Money in the bank.")
        assert a != b

    def test_different_context_produces_different_hash(self) -> None:
        a = compute_item_content_hash(1, "bank", "Money in the bank.")
        b = compute_item_content_hash(1, "bank", "The river bank was muddy.")
        assert a != b

    def test_homograph_different_context_deduplicates_correctly(self) -> None:
        # "bank" (financial) and "bank" (river) must hash differently
        financial = compute_item_content_hash(1, "bank", "He deposited money at the bank.")
        river = compute_item_content_hash(1, "bank", "They sat on the river bank.")
        assert financial != river

    def test_case_insensitive_term(self) -> None:
        lower = compute_item_content_hash(1, "apple", "I ate an apple.")
        upper = compute_item_content_hash(1, "Apple", "I ate an apple.")
        assert lower == upper

    def test_case_insensitive_context(self) -> None:
        a = compute_item_content_hash(1, "run", "She runs every day.")
        b = compute_item_content_hash(1, "run", "She Runs Every Day.")
        assert a == b

    def test_whitespace_normalized_in_term(self) -> None:
        a = compute_item_content_hash(1, "hello world", "Say hello world.")
        b = compute_item_content_hash(1, "hello  world", "Say hello world.")
        assert a == b

    def test_none_context_handled(self) -> None:
        result = compute_item_content_hash(1, "bank", None)
        assert isinstance(result, str)
        assert len(result) == 64

    def test_none_context_same_as_empty_string_context(self) -> None:
        none_ctx = compute_item_content_hash(1, "bank", None)
        empty_ctx = compute_item_content_hash(1, "bank", "")
        assert none_ctx == empty_ctx
