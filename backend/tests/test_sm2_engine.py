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
    LAPSE_INTERVAL_FACTOR,
    MAX_EF,
    MIN_EF,
    MIN_LAPSE_DAYS,
    QUALITY_THRESHOLD,
    SLOW_ANSWER_INTERVAL_FACTOR,
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
    def test_lapse_preserves_ef(self):
        """Original SM-2: EF never changes on lapse."""
        s = _state(ef="2.5")
        result = update(s, 0, now=_NOW)
        assert result.new_state.ease_factor == Decimal("2.5")

    def test_lapse_preserves_ef_at_minimum(self):
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

    # Young card (interval <= 3 days)
    def test_new_card_lapse_gives_one_hour(self):
        """Never recalled card → 1-hour re-show, not 1 day."""
        s = _state(reps=0, interval=0)
        result = update(s, 0, now=_NOW)
        assert result.next_review_at == _NOW + timedelta(hours=1)
        assert result.new_state.interval_days == 0
        assert result.new_state.repetitions == 0

    def test_young_card_lapse_gives_min_lapse_days(self):
        s = _state(reps=1, interval=0)
        result = update(s, 0, now=_NOW)
        assert result.new_state.interval_days == MIN_LAPSE_DAYS

    def test_young_card_lapse_resets_repetitions(self):
        s = _state(reps=1, interval=1)
        result = update(s, 0, now=_NOW)
        assert result.new_state.repetitions == 0

    def test_young_card_lapse_schedules_min_lapse_days(self):
        s = _state(reps=1, interval=0)
        result = update(s, 0, now=_NOW)
        expected = _NOW + timedelta(days=MIN_LAPSE_DAYS)
        assert abs((result.next_review_at - expected).total_seconds()) < 5

    # Mature card (interval > 3 days)
    def test_mature_card_lapse_proportional_interval(self):
        """30-day card → round(30 × 0.33) = 10 days."""
        s = _state(reps=3, interval=30)
        result = update(s, 0, now=_NOW)
        expected_days = max(MIN_LAPSE_DAYS, round(30 * float(LAPSE_INTERVAL_FACTOR)))
        assert result.new_state.interval_days == expected_days

    def test_mature_card_lapse_sets_repetitions_one(self):
        """Mature card skips re-learning phase."""
        s = _state(reps=5, interval=30)
        result = update(s, 0, now=_NOW)
        assert result.new_state.repetitions == 1

    def test_mature_card_lapse_schedules_proportional(self):
        s = _state(reps=3, interval=365)
        result = update(s, 0, now=_NOW)
        expected_days = max(MIN_LAPSE_DAYS, round(365 * float(LAPSE_INTERVAL_FACTOR)))
        expected_dt = _NOW + timedelta(days=expected_days)
        assert abs((result.next_review_at - expected_dt).total_seconds()) < 5

    def test_proportional_lapse_minimum_one_day(self):
        """Very short mature card interval cannot go below MIN_LAPSE_DAYS."""
        s = _state(reps=3, interval=4)  # 4 * 0.33 = 1.32 → rounds to 1
        result = update(s, 0, now=_NOW)
        assert result.new_state.interval_days >= MIN_LAPSE_DAYS


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

    def test_lapsed_attempts_preserved_on_success(self):
        """lapsed_attempts is a lifetime counter — success does not reset it."""
        s = _state(lapsed=3)
        result = update(s, 4, now=_NOW)
        assert result.new_state.lapsed_attempts == 3

    def test_next_review_is_one_day(self):
        """First review → 1-day interval (default intensity=1.0)."""
        result = update(_state(reps=0), 4, now=_NOW)
        delta = result.next_review_at - _NOW
        assert delta == timedelta(days=1)

    def test_interval_days_is_one(self):
        result = update(_state(reps=0), 5, now=_NOW)
        assert result.new_state.interval_days == 1

    def test_q5_increases_ef(self):
        result = update(_state(reps=0, ef="2.5"), 5, now=_NOW)
        assert result.new_state.ease_factor > Decimal("2.5")

    def test_q3_ef_neutral(self):
        """q=3 (slow-correct): EF unchanged — latency != difficulty."""
        result = update(_state(reps=0, ef="2.5"), 3, now=_NOW)
        assert result.new_state.ease_factor == Decimal("2.5")

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

    def test_repeated_lapses_ef_unchanged(self):
        """EF never changes on lapse — stays at initial value regardless of failure count."""
        s = _state(ef="2.5", lapsed=5)
        for _ in range(10):
            s = update(s, 0, now=_NOW).new_state
        assert s.ease_factor == Decimal("2.5")


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

    def test_first_review_intensity_clamped_to_one_day(self):
        # First interval is always 1 day minimum regardless of intensity
        r_default = update(_state(reps=0), 4, review_intensity=1.0, now=_NOW)
        r_intensive = update(_state(reps=0), 4, review_intensity=0.5, now=_NOW)
        assert r_intensive.next_review_at == r_default.next_review_at
        assert r_intensive.new_state.interval_days == 1


# ---------------------------------------------------------------------------
# update() — next_review_at timestamp
# ---------------------------------------------------------------------------


class TestNextReviewAt:
    def test_next_review_after_now(self):
        result = update(_state(), 4, now=_NOW)
        assert result.next_review_at > _NOW

    def test_young_lapse_next_review_within_24h(self):
        """Young card (interval=0) lapse → MIN_LAPSE_DAYS = 1 day."""
        result = update(_state(lapsed=0, interval=0), 0, now=_NOW)
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
        """Mature card lapses: rep=1, proportional interval; next success → rep=2."""
        s = _state(reps=5, interval=30, ef="2.8")

        # Lapse — mature card (interval=30 > 3)
        lapsed = update(s, 1, now=_NOW)
        assert lapsed.was_lapsed is True
        assert lapsed.new_state.repetitions == 1  # skips 6h re-learning
        assert lapsed.new_state.ease_factor == Decimal("2.8")  # EF unchanged

        # First successful recovery
        recovered = update(lapsed.new_state, 4, now=_NOW + timedelta(days=10))
        assert recovered.was_lapsed is False
        assert recovered.new_state.repetitions == 2

    def test_repeated_perfect_scores_increase_ef(self):
        s = _state(reps=3, interval=15, ef="2.5")
        for _ in range(5):
            s = update(s, 5, now=_NOW).new_state
        assert s.ease_factor > Decimal("2.5")

    def test_repeated_slow_scores_preserve_ef(self):
        """Repeated q=3: EF stays stable. Only interval is shortened each cycle."""
        s = _state(reps=3, interval=15, ef="2.5")
        for _ in range(5):
            s = update(s, 3, now=_NOW).new_state
        assert s.ease_factor == Decimal("2.5")

    def test_q3_shorter_interval_than_q4(self):
        """q=3 interval scaled by SLOW_ANSWER_INTERVAL_FACTOR vs q=4 at same state."""
        s = _state(reps=3, interval=20, ef="2.5")
        r3 = update(s, 3, now=_NOW)
        r4 = update(s, 4, now=_NOW)
        assert r3.new_state.interval_days < r4.new_state.interval_days

    def test_q3_interval_uses_slow_factor(self):
        """q=3 interval ≈ q=4 interval × SLOW_ANSWER_INTERVAL_FACTOR."""
        s = _state(reps=3, interval=20, ef="2.5")
        r3 = update(s, 3, now=_NOW)
        r4 = update(s, 4, now=_NOW)
        expected = max(1, round(r4.new_state.interval_days * float(SLOW_ANSWER_INTERVAL_FACTOR)))
        assert r3.new_state.interval_days == expected
