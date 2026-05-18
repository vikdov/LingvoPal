# backend/tests/test_stats.py
"""
Unit tests for pure stats helpers.

No mocks, no DB — only pure functions.

Test groups:
  - interval_to_bucket_key(): boundary values for all 5 buckets
  - _compute_learning_balance(): all decision branches
    - total < 10 guard (None)
    - new_pct > 35 → heavy
    - active_load > 55 → heavy
    - retention < 15 with total > 30 → slow
    - healthy deck → None
  - _daily_to_dict(): field mapping, accuracy_percent, zero-review guard
"""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.repositories.stats_repo import interval_to_bucket_key
from app.services.stats_service import _compute_learning_balance, _daily_to_dict

# ── interval_to_bucket_key ────────────────────────────────────────────────────


class TestIntervalToBucketKey:
    @pytest.mark.parametrize("interval,expected", [
        (0,   "new"),
        (1,   "new"),
        (2,   "learning"),
        (7,   "learning"),
        (8,   "young"),
        (21,  "young"),
        (22,  "mature"),
        (120, "mature"),
        (121, "long_term"),
        (365, "long_term"),
        (999, "long_term"),
    ])
    def test_boundaries(self, interval: int, expected: str) -> None:
        assert interval_to_bucket_key(interval) == expected

    def test_new_lower_bound(self) -> None:
        assert interval_to_bucket_key(0) == "new"

    def test_learning_lower_bound(self) -> None:
        assert interval_to_bucket_key(2) == "learning"

    def test_young_lower_bound(self) -> None:
        assert interval_to_bucket_key(8) == "young"

    def test_mature_lower_bound(self) -> None:
        assert interval_to_bucket_key(22) == "mature"

    def test_long_term_lower_bound(self) -> None:
        assert interval_to_bucket_key(121) == "long_term"


# ── _compute_learning_balance ─────────────────────────────────────────────────


def _make_buckets(
    new: float = 0.0,
    learning: float = 0.0,
    young: float = 0.0,
    mature: float = 0.0,
    long_term: float = 0.0,
) -> list[dict]:
    """Build a bucket list matching the shape returned by get_vocab_maturity."""
    return [
        {"key": "new",       "percent": new},
        {"key": "learning",  "percent": learning},
        {"key": "young",     "percent": young},
        {"key": "mature",    "percent": mature},
        {"key": "long_term", "percent": long_term},
    ]


class TestComputeLearningBalance:
    def test_too_few_words_returns_none(self) -> None:
        # Guard: total < 10 always returns None regardless of percentages
        buckets = _make_buckets(new=100.0)
        assert _compute_learning_balance(buckets, total=9) is None

    def test_exactly_ten_words_not_guarded(self) -> None:
        # total == 10 passes the guard; heavy new should trigger warning
        buckets = _make_buckets(new=40.0, learning=10.0, young=50.0)
        result = _compute_learning_balance(buckets, total=10)
        assert result is not None
        assert result["status"] == "heavy"

    def test_new_pct_above_35_triggers_heavy(self) -> None:
        buckets = _make_buckets(new=36.0, learning=10.0, young=54.0)
        result = _compute_learning_balance(buckets, total=50)
        assert result is not None
        assert result["status"] == "heavy"
        assert "new cards" in result["message"].lower()

    def test_new_pct_exactly_35_no_trigger(self) -> None:
        # 35.0 is NOT > 35 — no trigger from new_pct branch
        buckets = _make_buckets(new=35.0, learning=15.0, young=50.0)
        result = _compute_learning_balance(buckets, total=50)
        # active_load = 50 ≤ 55, retention = 0 but total=50>30 → slow
        assert result is not None
        assert result["status"] == "slow"

    def test_active_load_above_55_triggers_heavy(self) -> None:
        # new=30, learning=26 → active_load=56 > 55
        buckets = _make_buckets(new=30.0, learning=26.0, young=44.0)
        result = _compute_learning_balance(buckets, total=50)
        assert result is not None
        assert result["status"] == "heavy"
        assert "load" in result["message"].lower()

    def test_active_load_exactly_55_no_trigger(self) -> None:
        # new=30, learning=25 → active_load=55, not > 55
        buckets = _make_buckets(new=30.0, learning=25.0, young=30.0, mature=15.0)
        result = _compute_learning_balance(buckets, total=50)
        # retention=15 is not < 15, so no slow trigger either
        assert result is None

    def test_slow_maturation_triggers_when_total_above_30(self) -> None:
        # retention (mature+long_term) = 10 < 15, total = 31 > 30
        buckets = _make_buckets(new=20.0, learning=20.0, young=50.0, mature=5.0, long_term=5.0)
        result = _compute_learning_balance(buckets, total=31)
        assert result is not None
        assert result["status"] == "slow"
        assert "matur" in result["message"].lower()

    def test_slow_maturation_not_triggered_when_total_le_30(self) -> None:
        # same percentages but total ≤ 30 — guard suppresses it
        buckets = _make_buckets(new=20.0, learning=20.0, young=50.0, mature=5.0, long_term=5.0)
        assert _compute_learning_balance(buckets, total=30) is None

    def test_healthy_deck_returns_none(self) -> None:
        # Balanced deck: low new, decent retention
        buckets = _make_buckets(new=10.0, learning=15.0, young=25.0, mature=30.0, long_term=20.0)
        assert _compute_learning_balance(buckets, total=100) is None

    def test_new_pct_branch_takes_priority_over_active_load(self) -> None:
        # new=40 > 35, active_load=70 > 55 — new branch fires first, message differs
        buckets = _make_buckets(new=40.0, learning=30.0, young=30.0)
        result = _compute_learning_balance(buckets, total=50)
        assert result is not None
        assert result["status"] == "heavy"
        assert "new cards" in result["message"].lower()

    def test_result_has_status_and_message_keys(self) -> None:
        buckets = _make_buckets(new=50.0, learning=50.0)
        result = _compute_learning_balance(buckets, total=20)
        assert result is not None
        assert "status" in result
        assert "message" in result
        assert isinstance(result["message"], str)
        assert len(result["message"]) > 0


# ── _daily_to_dict ────────────────────────────────────────────────────────────


def _row(
    stat_date=date(2026, 1, 15),
    language_id: int = 1,
    correct: int = 8,
    incorrect: int = 2,
    new_words: int = 3,
    seconds: float = 120.0,
) -> SimpleNamespace:
    return SimpleNamespace(
        stat_date=stat_date,
        language_id=language_id,
        correct_count=correct,
        incorrect_count=incorrect,
        new_words_count=new_words,
        seconds_spent=Decimal(str(seconds)),
    )


class TestDailyToDict:
    def test_returns_iso_date_string(self) -> None:
        result = _daily_to_dict(_row(stat_date=date(2026, 3, 7)))
        assert result["stat_date"] == "2026-03-07"

    def test_correct_and_incorrect_counts(self) -> None:
        result = _daily_to_dict(_row(correct=10, incorrect=5))
        assert result["correct_count"] == 10
        assert result["incorrect_count"] == 5

    def test_total_reviews_is_sum(self) -> None:
        result = _daily_to_dict(_row(correct=7, incorrect=3))
        assert result["total_reviews"] == 10

    def test_accuracy_percent_rounds_to_two_decimals(self) -> None:
        result = _daily_to_dict(_row(correct=1, incorrect=2))
        # 1/3 * 100 ≈ 33.33
        assert result["accuracy_percent"] == round(1 / 3 * 100, 2)

    def test_accuracy_zero_when_no_reviews(self) -> None:
        result = _daily_to_dict(_row(correct=0, incorrect=0))
        assert result["accuracy_percent"] == 0.0

    def test_accuracy_100_when_all_correct(self) -> None:
        result = _daily_to_dict(_row(correct=5, incorrect=0))
        assert result["accuracy_percent"] == 100.0

    def test_seconds_spent_is_float(self) -> None:
        result = _daily_to_dict(_row(seconds=90.5))
        assert result["seconds_spent"] == 90.5
        assert isinstance(result["seconds_spent"], float)

    def test_language_id_passed_through(self) -> None:
        result = _daily_to_dict(_row(language_id=7))
        assert result["language_id"] == 7

    def test_new_words_count_passed_through(self) -> None:
        result = _daily_to_dict(_row(new_words=12))
        assert result["new_words_count"] == 12
