# backend/tests/test_sm2_engine.py
"""
Unit tests for the SM-2 engine.

100% coverage of sm2_engine.py.
No mocks — all tests use pure function calls with injected `now` timestamps.

Test groups:
  - initial_state()
  - update() — success path (q=3,4,5)
  - update() — lapse path (q=0,1,2)
  - update() — repetition count progression
  - update() — ease factor boundaries (MIN_EF, MAX_EF)
  - update() — review_intensity scaling
  - update() — first / second interval heuristics
  - update() — multi-lapse recovery intervals
  - apply_absence_decay_for_days()
  - update() — input validation (bad q, bad intensity)
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.services.sm2_engine import (
    INITIAL_EF,
    INITIAL_INTERVAL_HOURS,
    MAX_EF,
    MIN_EF,
    QUALITY_THRESHOLD,
    SM2State,
    apply_absence_decay_for_days,
    initial_state,
    update,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


def _state(
    interval: int = 0,
    ef: str = "2.5",
    reps: int = 0,
    lapsed: int = 0,
) -> SM2State:
    return SM2State(
        interval_days=interval,
        ease_factor=Decimal(ef),
        repetitions=reps,
        lapsed_attempts=lapsed,
    )


# ---------------------------------------------------------------------------
# initial_state()
# ---------------------------------------------------------------------------


class TestInitialState:
    def test_returns_sm2state(self):
        s = initial_state()
        assert isinstance(s, SM2State)

    def test_zero_interval(self):
        assert initial_state().interval_days == 0

    def test_initial_ef(self):
        assert initial_state().ease_factor == INITIAL_EF

    def test_zero_repetitions(self):
        assert initial_state().repetitions == 0

    def test_zero_lapsed_attempts(self):
        assert initial_state().lapsed_attempts == 0


# ---------------------------------------------------------------------------
# update() — input validation
# ---------------------------------------------------------------------------


class TestUpdateValidation:
    def test_quality_below_zero_raises(self):
        with pytest.raises(ValueError, match="quality score q"):
            update(_state(), -1, now=_NOW)

    def test_quality_above_five_raises(self):
        with pytest.raises(ValueError, match="quality score q"):
            update(_state(), 6, now=_NOW)

    def test_zero_intensity_raises(self):
        with pytest.raises(ValueError, match="review_intensity"):
            update(_state(), 4, review_intensity=0.0, now=_NOW)

    def test_negative_intensity_raises(self):
        with pytest.raises(ValueError, match="review_intensity"):
            update(_state(), 4, review_intensity=-0.5, now=_NOW)

    def test_boundary_q_zero_valid(self):
        result = update(_state(), 0, now=_NOW)
        assert result.was_lapsed is True

    def test_boundary_q_five_valid(self):
        result = update(_state(), 5, now=_NOW)
        assert result.was_lapsed is False

    def test_boundary_q_three_is_success(self):
        result = update(_state(), QUALITY_THRESHOLD, now=_NOW)
        assert result.was_lapsed is False

    def test_boundary_q_two_is_lapse(self):
        result = update(_state(), QUALITY_THRESHOLD - 1, now=_NOW)
        assert result.was_lapsed is True


# ---------------------------------------------------------------------------
# update() — lapse path
# ---------------------------------------------------------------------------


class TestLapsePath:
    def test_lapse_resets_repetitions(self):
        s = _state(reps=5, interval=30)
        result = update(s, 0, now=_NOW)
        assert result.new_state.repetitions == 0

    def test_lapse_resets_interval(self):
        s = _state(interval=30)
        result = update(s, 2, now=_NOW)
        assert result.new_state.interval_days == 0

    def test_lapse_decreases_ef(self):
        s = _state(ef="2.5")
        result = update(s, 0, now=_NOW)
        assert result.new_state.ease_factor < Decimal("2.5")

    def test_lapse_ef_not_below_minimum(self):
        s = _state(ef=str(MIN_EF))
        result = update(s, 0, now=_NOW)
        assert result.new_state.ease_factor == MIN_EF

    def test_was_lapsed_flag_set(self):
        result = update(_state(), 1, now=_NOW)
        assert result.was_lapsed is True

    def test_lapsed_attempts_increments(self):
        s = _state(lapsed=0)
        result = update(s, 0, now=_NOW)
        assert result.new_state.lapsed_attempts == 1

    def test_lapsed_attempts_accumulates(self):
        s = _state(lapsed=2)
        result = update(s, 1, now=_NOW)
        assert result.new_state.lapsed_attempts == 3

    def test_first_lapse_recovery_interval_24h(self):
        """First failure → 24h recovery (1440 min)."""
        s = _state(lapsed=0)
        result = update(s, 0, now=_NOW)
        expected_min = _NOW + timedelta(minutes=1439)
        expected_max = _NOW + timedelta(minutes=1441)
        assert expected_min <= result.next_review_at <= expected_max

    def test_second_lapse_recovery_interval_30min(self):
        s = _state(lapsed=1)
        result = update(s, 0, now=_NOW)
        expected = _NOW + timedelta(minutes=30)
        assert abs((result.next_review_at - expected).total_seconds()) < 5

    def test_third_lapse_recovery_interval_10min(self):
        s = _state(lapsed=2)
        result = update(s, 0, now=_NOW)
        expected = _NOW + timedelta(minutes=10)
        assert abs((result.next_review_at - expected).total_seconds()) < 5

    def test_fourth_and_beyond_lapse_recovery_5min(self):
        for lapsed in (3, 4, 10):
            s = _state(lapsed=lapsed)
            result = update(s, 0, now=_NOW)
            expected = _NOW + timedelta(minutes=5)
            assert abs((result.next_review_at - expected).total_seconds()) < 5


# ---------------------------------------------------------------------------
# update() — success path, first review (n=1)
# ---------------------------------------------------------------------------


class TestSuccessFirstRepetition:
    def test_repetitions_becomes_one(self):
        result = update(_state(reps=0), 4, now=_NOW)
        assert result.new_state.repetitions == 1

    def test_was_lapsed_false(self):
        result = update(_state(reps=0), 4, now=_NOW)
        assert result.was_lapsed is False

    def test_lapsed_attempts_reset(self):
        s = _state(lapsed=3)
        result = update(s, 4, now=_NOW)
        assert result.new_state.lapsed_attempts == 0

    def test_next_review_within_day(self):
        """First review → 6-hour interval (default intensity=1.0)."""
        result = update(_state(reps=0), 4, now=_NOW)
        delta = result.next_review_at - _NOW
        assert timedelta(hours=5) <= delta <= timedelta(hours=7)

    def test_interval_days_is_one(self):
        result = update(_state(reps=0), 5, now=_NOW)
        assert result.new_state.interval_days == 1

    def test_q5_increases_ef(self):
        result = update(_state(reps=0, ef="2.5"), 5, now=_NOW)
        assert result.new_state.ease_factor > Decimal("2.5")

    def test_q3_decreases_ef(self):
        result = update(_state(reps=0, ef="2.5"), 3, now=_NOW)
        assert result.new_state.ease_factor < Decimal("2.5")

    def test_q4_leaves_ef_neutral(self):
        result = update(_state(reps=0, ef="2.5"), 4, now=_NOW)
        # q=4 adjustment = 0.1 - 1*(0.08 + 1*0.02) = 0.1 - 0.10 = 0.0
        assert result.new_state.ease_factor == Decimal("2.5")


# ---------------------------------------------------------------------------
# update() — success path, second review (n=2)
# ---------------------------------------------------------------------------


class TestSuccessSecondRepetition:
    def test_repetitions_becomes_two(self):
        s = _state(reps=1, interval=1)
        result = update(s, 4, now=_NOW)
        assert result.new_state.repetitions == 2

    def test_interval_at_least_four_days(self):
        s = _state(reps=1, interval=1, ef="1.3")
        result = update(s, 4, now=_NOW)
        assert result.new_state.interval_days >= 4

    def test_high_ef_gives_longer_second_interval(self):
        s_low = _state(reps=1, interval=1, ef="1.3")
        s_high = _state(reps=1, interval=1, ef="3.5")
        r_low = update(s_low, 4, now=_NOW)
        r_high = update(s_high, 4, now=_NOW)
        assert r_high.new_state.interval_days > r_low.new_state.interval_days


# ---------------------------------------------------------------------------
# update() — success path, third+ review (n≥3)
# ---------------------------------------------------------------------------


class TestSuccessLaterRepetitions:
    def test_interval_grows_multiplicatively(self):
        s = _state(reps=2, interval=6, ef="2.5")
        result = update(s, 4, now=_NOW)
        # new_days = int(6 * 2.5) = 15
        assert result.new_state.interval_days == 15

    def test_interval_minimum_one_day(self):
        s = _state(reps=2, interval=0, ef="1.3")
        result = update(s, 3, now=_NOW)
        assert result.new_state.interval_days >= 1

    def test_repetitions_increment(self):
        s = _state(reps=5, interval=30)
        result = update(s, 4, now=_NOW)
        assert result.new_state.repetitions == 6


# ---------------------------------------------------------------------------
# update() — ease factor boundaries
# ---------------------------------------------------------------------------


class TestEaseFactorBoundaries:
    def test_ef_never_exceeds_max(self):
        s = _state(ef=str(MAX_EF), reps=3, interval=10)
        result = update(s, 5, now=_NOW)
        assert result.new_state.ease_factor <= MAX_EF

    def test_ef_never_below_min(self):
        s = _state(ef=str(MIN_EF))
        result = update(s, 0, now=_NOW)
        assert result.new_state.ease_factor >= MIN_EF

    def test_repeated_lapses_do_not_go_below_min(self):
        s = _state(ef=str(MIN_EF), lapsed=5)
        for _ in range(10):
            s = update(s, 0, now=_NOW).new_state
        assert s.ease_factor >= MIN_EF


# ---------------------------------------------------------------------------
# update() — review_intensity scaling
# ---------------------------------------------------------------------------


class TestReviewIntensityScaling:
    def test_intensive_gives_shorter_intervals(self):
        # intensity=0.75 (<1.0) → interval * 0.75 → shorter → sooner review
        s = _state(reps=2, interval=6, ef="2.5")
        r_default = update(s, 4, review_intensity=1.0, now=_NOW)
        r_intensive = update(s, 4, review_intensity=0.75, now=_NOW)
        assert r_intensive.new_state.interval_days <= r_default.new_state.interval_days

    def test_light_gives_longer_intervals(self):
        # intensity=1.3 (>1.0) → interval * 1.3 → longer → later review
        s = _state(reps=2, interval=6, ef="2.5")
        r_default = update(s, 4, review_intensity=1.0, now=_NOW)
        r_light = update(s, 4, review_intensity=1.3, now=_NOW)
        assert r_light.new_state.interval_days >= r_default.new_state.interval_days

    def test_first_review_intensity_scales_hours(self):
        # intensity=0.5 (<1.0) → initial_hours * 0.5 → sooner first review
        r_default = update(_state(reps=0), 4, review_intensity=1.0, now=_NOW)
        r_intensive = update(_state(reps=0), 4, review_intensity=0.5, now=_NOW)
        assert r_intensive.next_review_at < r_default.next_review_at


# ---------------------------------------------------------------------------
# update() — next_review_at timestamp
# ---------------------------------------------------------------------------


class TestNextReviewAt:
    def test_next_review_after_now(self):
        result = update(_state(), 4, now=_NOW)
        assert result.next_review_at > _NOW

    def test_lapse_next_review_within_24h(self):
        result = update(_state(lapsed=0), 0, now=_NOW)
        assert result.next_review_at <= _NOW + timedelta(hours=24, minutes=1)

    def test_success_next_review_uses_injected_now(self):
        custom_now = datetime(2030, 6, 1, tzinfo=timezone.utc)
        result = update(_state(reps=2, interval=10, ef="2.5"), 4, now=custom_now)
        assert result.next_review_at > custom_now

    def test_next_review_is_timezone_aware(self):
        result = update(_state(), 4, now=_NOW)
        assert result.next_review_at.tzinfo is not None


# ---------------------------------------------------------------------------
# apply_absence_decay_for_days()
# ---------------------------------------------------------------------------


class TestAbsenceDecay:
    def test_no_decay_within_60_days(self):
        ef = Decimal("2.5")
        assert apply_absence_decay_for_days(ef, 60) == ef

    def test_no_decay_at_zero_days(self):
        ef = Decimal("2.5")
        assert apply_absence_decay_for_days(ef, 0) == ef

    def test_mild_decay_between_61_and_90_days(self):
        ef = Decimal("2.5")
        decayed = apply_absence_decay_for_days(ef, 75)
        assert decayed < ef
        assert decayed > ef * Decimal("0.96")  # 0.98 rate

    def test_moderate_decay_between_91_and_180_days(self):
        ef = Decimal("2.5")
        decayed = apply_absence_decay_for_days(ef, 120)
        assert decayed < ef
        assert decayed > ef * Decimal("0.93")  # 0.95 rate

    def test_severe_decay_beyond_180_days(self):
        ef = Decimal("2.5")
        decayed = apply_absence_decay_for_days(ef, 181)
        assert decayed < ef

    def test_decay_floored_at_min_ef(self):
        decayed = apply_absence_decay_for_days(MIN_EF, 365)
        assert decayed == MIN_EF

    def test_high_ef_decays_to_legal_value(self):
        ef = Decimal("4.0")
        decayed = apply_absence_decay_for_days(ef, 200)
        assert MIN_EF <= decayed < ef


# ---------------------------------------------------------------------------
# Regression: full session simulation
# ---------------------------------------------------------------------------


class TestFullSessionSimulation:
    def test_new_card_study_sequence(self):
        """Simulate a card going through a full successful learning sequence."""
        s = initial_state()

        # Review 1: q=4 (correct, normal speed)
        r1 = update(s, 4, now=_NOW)
        assert r1.new_state.repetitions == 1
        assert r1.was_lapsed is False

        # Review 2: q=5 (correct, fast)
        r2 = update(r1.new_state, 5, now=_NOW + timedelta(hours=7))
        assert r2.new_state.repetitions == 2
        assert r2.new_state.ease_factor > r1.new_state.ease_factor

        # Review 3: q=4 (correct, normal)
        r3 = update(r2.new_state, 4, now=_NOW + timedelta(days=7))
        assert r3.new_state.repetitions == 3
        assert r3.new_state.interval_days > r2.new_state.interval_days

    def test_lapse_then_recovery(self):
        """Simulate a card lapsing and then recovering."""
        s = _state(reps=5, interval=30, ef="2.8")

        # Lapse
        lapsed = update(s, 1, now=_NOW)
        assert lapsed.was_lapsed is True
        assert lapsed.new_state.repetitions == 0

        # First successful recovery
        recovered = update(lapsed.new_state, 4, now=_NOW + timedelta(minutes=30))
        assert recovered.was_lapsed is False
        assert recovered.new_state.repetitions == 1

    def test_repeated_perfect_scores_increase_ef(self):
        s = _state(reps=3, interval=15, ef="2.5")
        for _ in range(5):
            s = update(s, 5, now=_NOW).new_state
        assert s.ease_factor > Decimal("2.5")

    def test_repeated_slow_scores_decrease_ef(self):
        s = _state(reps=3, interval=15, ef="2.5")
        for _ in range(5):
            s = update(s, 3, now=_NOW).new_state
        assert s.ease_factor < Decimal("2.5")
