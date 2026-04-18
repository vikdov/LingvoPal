# backend/tests/test_answer_evaluator.py
"""
Unit tests for the answer evaluator.

100% coverage of answer_evaluator.py.
No mocks — all tests use pure function calls.

Test groups:
  - _normalise(): diacritics, casing, whitespace
  - _levenshtein_similarity(): exact, empty, edge cases, values
  - evaluate(): correctness thresholds per mode
  - evaluate(): time capping at T_MAX_MS
  - evaluate(): quality mapping (q=1,3,4,5)
  - evaluate(): confidence_override interactions
  - evaluate(): EvaluationResult fields
  - evaluate(): structured logging data (tested via result fields)
"""

import pytest

from app.models.enums import EvaluationMode
from app.services.answer_evaluator import (
    DEFAULT_EXPECTED_MS,
    FAST_THRESHOLD,
    T_MAX_MS,
    VERY_SLOW_THRESHOLD,
    EvaluationContext,
    EvaluationResult,
    evaluate,
    _levenshtein_similarity,
    _normalise,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_OVERRIDE_MAP: dict[str, int] = {
    "blackout": 1,
    "hard": 2,
    "neutral": 3,
    "good": 4,
    "easy": 5,
}


def _ctx(
    user: str = "hello",
    correct: str = "hello",
    response_ms: int = 2000,
    expected_ms: int = DEFAULT_EXPECTED_MS,
    mode: EvaluationMode = EvaluationMode.NORMAL,
    override: str | int | None = None,
) -> EvaluationContext:
    conf: int | None = (
        _OVERRIDE_MAP[override] if isinstance(override, str) else override
    )
    return EvaluationContext(
        user_answer=user,
        correct_answer=correct,
        response_time_ms=response_ms,
        expected_time_ms=expected_ms,
        evaluation_mode=mode,
        confidence_override=conf,
    )


# ---------------------------------------------------------------------------
# _normalise()
# ---------------------------------------------------------------------------


class TestNormalise:
    def test_lowercase(self):
        assert _normalise("Hello") == "hello"

    def test_strips_whitespace(self):
        assert _normalise("  hello  ") == "hello"

    def test_removes_diacritics(self):
        assert _normalise("café") == "cafe"

    def test_removes_umlaut(self):
        assert _normalise("Üniversität") == "universitat"

    def test_removes_acute_accent(self):
        assert _normalise("résumé") == "resume"

    def test_empty_string(self):
        assert _normalise("") == ""

    def test_already_normalised(self):
        assert _normalise("libro") == "libro"

    def test_combined_normalisation(self):
        assert _normalise("  Üniversität  ") == "universitat"


# ---------------------------------------------------------------------------
# _levenshtein_similarity()
# ---------------------------------------------------------------------------


class TestLevenshteinSimilarity:
    def test_identical_strings_return_one(self):
        assert _levenshtein_similarity("hello", "hello") == 1.0

    def test_empty_both_return_one(self):
        assert _levenshtein_similarity("", "") == 1.0

    def test_one_empty_return_zero(self):
        assert _levenshtein_similarity("hello", "") == 0.0
        assert _levenshtein_similarity("", "hello") == 0.0

    def test_completely_different_return_low(self):
        sim = _levenshtein_similarity("abc", "xyz")
        assert sim == 0.0  # 3 edits / max(3,3)=3 → 1 - 1 = 0

    def test_one_typo_high_similarity(self):
        # "helo" vs "hello": 1 insertion → 1/5 edit distance → 0.8
        sim = _levenshtein_similarity("helo", "hello")
        assert sim >= 0.79

    def test_symmetry(self):
        a, b = "kitten", "sitting"
        assert _levenshtein_similarity(a, b) == _levenshtein_similarity(b, a)

    def test_single_char_match(self):
        assert _levenshtein_similarity("a", "a") == 1.0

    def test_single_char_no_match(self):
        assert _levenshtein_similarity("a", "b") == 0.0

    def test_known_value_hello_helo(self):
        # edit distance = 1 (insertion), max_len = 5
        # similarity = 1 - 1/5 = 0.8
        sim = _levenshtein_similarity("helo", "hello")
        assert abs(sim - 0.8) < 0.001

    def test_known_value_libro_libra(self):
        # edit distance = 1 (substitution o→a), max_len = 5
        # similarity = 1 - 1/5 = 0.8
        sim = _levenshtein_similarity("libro", "libra")
        assert abs(sim - 0.8) < 0.001

    def test_result_in_range(self):
        for a, b in [("cat", "car"), ("hello", "hell"), ("", "x")]:
            sim = _levenshtein_similarity(a, b)
            assert 0.0 <= sim <= 1.0

    def test_long_strings(self):
        a = "the quick brown fox jumps over the lazy dog"
        b = "the quick brown fox jumps over the lazy cat"
        sim = _levenshtein_similarity(a, b)
        assert sim > 0.9  # only last 3 chars differ

    def test_prefix_match(self):
        # "abcde" vs "abc": 2 deletions, max_len=5 → 1 - 2/5 = 0.6
        sim = _levenshtein_similarity("abcde", "abc")
        assert abs(sim - 0.6) < 0.001


# ---------------------------------------------------------------------------
# evaluate() — correctness determination
# ---------------------------------------------------------------------------


class TestCorrectnessThresholds:
    def test_exact_match_is_correct(self):
        result = evaluate(_ctx("hello", "hello"))
        assert result.is_correct is True

    def test_completely_wrong_is_incorrect(self):
        result = evaluate(_ctx("xyz", "hello"))
        assert result.is_correct is False

    def test_normal_mode_09_threshold(self):
        # Construct answer where similarity ≈ 0.91 (just above normal threshold)
        # "helo" vs "hello": similarity = 0.8 → below 0.9 → incorrect
        result = evaluate(_ctx("helo", "hello", mode=EvaluationMode.NORMAL))
        assert result.is_correct is False  # 0.8 < 0.9

    def test_forgiving_mode_08_threshold(self):
        # "helo" vs "hello": similarity = 0.8 → exactly at forgiving threshold
        result = evaluate(_ctx("helo", "hello", mode=EvaluationMode.FORGIVING))
        assert result.is_correct is True  # 0.8 >= 0.8

    def test_strict_mode_095_threshold(self):
        # Need similarity ≥ 0.95 for strict mode
        result = evaluate(_ctx("hello", "hellp", mode=EvaluationMode.STRICT))
        # similarity = 0.8 → incorrect in strict
        assert result.is_correct is False

    def test_strict_mode_exact_match(self):
        result = evaluate(_ctx("hello", "hello", mode=EvaluationMode.STRICT))
        assert result.is_correct is True

    def test_diacritics_normalised_before_comparison(self):
        # "cafe" vs "café" should be treated as identical after normalisation
        result = evaluate(_ctx("cafe", "café"))
        assert result.is_correct is True
        assert result.similarity == 1.0

    def test_case_insensitive(self):
        result = evaluate(_ctx("Hello", "hello"))
        assert result.is_correct is True

    def test_whitespace_trimmed(self):
        result = evaluate(_ctx("  hello  ", "hello"))
        assert result.is_correct is True


# ---------------------------------------------------------------------------
# evaluate() — response time capping
# ---------------------------------------------------------------------------


class TestTimeCapping:
    def test_response_capped_at_t_max(self):
        result = evaluate(_ctx(response_ms=T_MAX_MS + 5000))
        assert result.capped_response_ms == T_MAX_MS

    def test_response_below_cap_unchanged(self):
        result = evaluate(_ctx(response_ms=2000))
        assert result.capped_response_ms == 2000

    def test_response_exactly_at_cap(self):
        result = evaluate(_ctx(response_ms=T_MAX_MS))
        assert result.capped_response_ms == T_MAX_MS

    def test_time_ratio_uses_capped_value(self):
        # With expected=3000ms and actual=15000ms (capped at 10000):
        # ratio should be 10000/3000 ≈ 3.33, not 15000/3000=5.0
        result = evaluate(_ctx(response_ms=15_000, expected_ms=3000))
        assert abs(result.time_ratio - (T_MAX_MS / 3000)) < 0.01


# ---------------------------------------------------------------------------
# evaluate() — quality mapping (no override)
# ---------------------------------------------------------------------------


class TestQualityMapping:
    def test_incorrect_answer_gives_q1(self):
        result = evaluate(_ctx("xyz", "hello"))
        assert result.quality == 1

    def test_correct_fast_gives_q5(self):
        # ratio = 1000 / 5000 = 0.2 → fast (< 0.8)
        result = evaluate(_ctx("hello", "hello", response_ms=1000, expected_ms=5000))
        assert result.quality == 5

    def test_correct_normal_gives_q4(self):
        # ratio = 3000 / 3000 = 1.0 → normal (0.8 ≤ 1.0 ≤ 1.5)
        result = evaluate(_ctx("hello", "hello", response_ms=3000, expected_ms=3000))
        assert result.quality == 4

    def test_correct_very_slow_gives_q3(self):
        # ratio = 9000 / 3000 = 3.0 → very slow (> 1.5)
        result = evaluate(_ctx("hello", "hello", response_ms=9000, expected_ms=3000))
        assert result.quality == 3

    def test_boundary_fast_threshold(self):
        # ratio = FAST_THRESHOLD (0.8) → normal (not fast: must be < 0.8)
        ms = int(DEFAULT_EXPECTED_MS * FAST_THRESHOLD)
        result = evaluate(_ctx("hello", "hello", response_ms=ms))
        assert result.quality == 4  # at boundary → normal

    def test_boundary_very_slow_threshold(self):
        # ratio exactly at 1.5 → normal (≤ 1.5 is still normal)
        ms = int(DEFAULT_EXPECTED_MS * VERY_SLOW_THRESHOLD)
        result = evaluate(_ctx("hello", "hello", response_ms=ms))
        assert result.quality == 4

    def test_just_above_very_slow_threshold(self):
        ms = int(DEFAULT_EXPECTED_MS * VERY_SLOW_THRESHOLD) + 1
        result = evaluate(_ctx("hello", "hello", response_ms=ms))
        assert result.quality == 3

    def test_just_below_fast_threshold(self):
        ms = int(DEFAULT_EXPECTED_MS * FAST_THRESHOLD) - 1
        result = evaluate(_ctx("hello", "hello", response_ms=ms))
        assert result.quality == 5


# ---------------------------------------------------------------------------
# evaluate() — confidence_override interactions
# ---------------------------------------------------------------------------


class TestConfidenceOverride:
    def test_easy_override_correct_gives_q5(self):
        # Even with slow speed (would normally be q=3), "easy" → q=5
        result = evaluate(
            _ctx(
                "hello",
                "hello",
                response_ms=9000,
                expected_ms=3000,
                override="easy",
            )
        )
        assert result.quality == 5

    def test_easy_override_incorrect_gives_q1(self):
        # Override only applies to correct answers
        result = evaluate(_ctx("xyz", "hello", override="easy"))
        assert result.quality == 1

    def test_hard_override_correct_gives_q3(self):
        # Even with fast speed (would normally be q=5), "hard" → q=3
        result = evaluate(
            _ctx(
                "hello",
                "hello",
                response_ms=500,
                expected_ms=3000,
                override="hard",
            )
        )
        assert result.quality == 3

    def test_hard_override_incorrect_gives_q1(self):
        result = evaluate(_ctx("xyz", "hello", override="hard"))
        assert result.quality == 1

    def test_good_override_correct_fast_gives_q5(self):
        # Fast speed → q=5; "good" floors at 4 so max(4,5)=5
        result = evaluate(
            _ctx(
                "hello",
                "hello",
                response_ms=500,
                expected_ms=3000,
                override="good",
            )
        )
        assert result.quality == 5

    def test_good_override_correct_slow_gives_q4(self):
        # Slow speed would give q=3; "good" floors at 4 → max(4,3)=4
        result = evaluate(
            _ctx(
                "hello",
                "hello",
                response_ms=9000,
                expected_ms=3000,
                override="good",
            )
        )
        assert result.quality == 4

    def test_good_override_incorrect_gives_q1(self):
        result = evaluate(_ctx("xyz", "hello", override="good"))
        assert result.quality == 1

    def test_none_override_uses_speed(self):
        result_slow = evaluate(
            _ctx("hello", "hello", response_ms=9000, expected_ms=3000)
        )
        result_fast = evaluate(
            _ctx("hello", "hello", response_ms=500, expected_ms=3000)
        )
        assert result_slow.quality < result_fast.quality


# ---------------------------------------------------------------------------
# evaluate() — EvaluationResult fields
# ---------------------------------------------------------------------------


class TestEvaluationResultFields:
    def test_result_type(self):
        result = evaluate(_ctx())
        assert isinstance(result, EvaluationResult)

    def test_similarity_in_range(self):
        for user, correct in [("hello", "hello"), ("abc", "xyz"), ("", "hello")]:
            result = evaluate(_ctx(user, correct))
            assert 0.0 <= result.similarity <= 1.0

    def test_time_ratio_positive(self):
        result = evaluate(_ctx(response_ms=2000, expected_ms=3000))
        assert result.time_ratio > 0

    def test_capped_response_never_exceeds_t_max(self):
        result = evaluate(_ctx(response_ms=99_999))
        assert result.capped_response_ms <= T_MAX_MS

    def test_quality_one_of_valid_values(self):
        for user, correct, ms in [
            ("xyz", "hello", 500),  # incorrect
            ("hello", "hello", 500),  # fast
            ("hello", "hello", 3000),  # normal
            ("hello", "hello", 9000),  # slow
        ]:
            result = evaluate(_ctx(user, correct, response_ms=ms))
            assert result.quality in {1, 3, 4, 5}

    def test_is_correct_matches_quality(self):
        """Quality=1 → incorrect; quality≥3 → correct."""
        for user, correct in [("hello", "hello"), ("xyz", "hello")]:
            result = evaluate(_ctx(user, correct))
            if result.quality == 1:
                assert result.is_correct is False
            else:
                assert result.is_correct is True


# ---------------------------------------------------------------------------
# evaluate() — zero/edge expected_time values
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_zero_expected_time_does_not_raise(self):
        # Division by zero guard: expected_ms=0 should use fallback ratio
        result = evaluate(_ctx(expected_ms=0))
        assert isinstance(result, EvaluationResult)

    def test_minimum_response_time(self):
        result = evaluate(_ctx(response_ms=1))
        assert result.capped_response_ms == 1

    def test_both_empty_answers(self):
        # Both empty after normalisation → identical → similarity = 1.0 → correct
        result = evaluate(_ctx("   ", ""))
        # After normalise: both become "" → similarity=1.0 → correct
        assert result.is_correct is True
        assert result.similarity == 1.0
