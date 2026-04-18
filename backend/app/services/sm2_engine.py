# backend/app/services/sm2_engine.py
"""
SM-2 Engine — pure algorithm, zero side effects.

This module contains ONLY the scheduling mathematics.
It knows nothing about databases, HTTP, users, or answer evaluation.
Every function is a pure transformation: (state, q) → next_state.

SM-2 algorithm overview:
  - q ≥ 3  → successful recall  → interval grows via ease factor
  - q < 3  → failure (lapse)    → interval resets, EF decreases
  - n=1: 6-hour initial interval (sub-day review for brand-new cards)
  - n=2: short interval based on EF (4–10 days)
  - n>2: interval = prev_interval × EF

review_intensity coefficient (from user settings):
  - Scales ALL computed intervals uniformly.
  - < 1.0 → shorter intervals, more frequent reviews (intensive learner)
  - > 1.0 → longer intervals, fewer reviews (light learner)
  - Formula: next_interval = raw_interval * review_intensity

Reference: https://www.supermemo.com/en/blog/application-of-a-computer-to-improve-the-results-obtained-in-working-with-the-supermemo-method
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Final

# ============================================================================
# Constants
# ============================================================================

MIN_EF: Final[Decimal] = Decimal("1.3")
MAX_EF: Final[Decimal] = Decimal("5.0")
INITIAL_EF: Final[Decimal] = Decimal("2.5")

# q ≥ this → success; q < this → lapse
QUALITY_THRESHOLD: Final[int] = 3

# New-card first-review interval (6 hours expressed as fractional days)
INITIAL_INTERVAL_HOURS: Final[float] = 6.0

# Ease factor penalty per lapse
EF_LAPSE_PENALTY: Final[Decimal] = Decimal("0.3")

# Lapse-recovery intervals (minutes); after each consecutive failure
_LAPSE_RECOVERY_INTERVALS_MINUTES: Final[tuple[int, ...]] = (1440, 30, 10, 5)
# index:  0=first failure, 1=second, 2=third, 3+=fourth and beyond

# Long-absence decay thresholds / rates
_DECAY_THRESHOLDS = ((90, Decimal("0.98")), (180, Decimal("0.95")))
_DECAY_FLOOR = Decimal("0.90")


# ============================================================================
# Data contracts
# ============================================================================


@dataclass(frozen=True)
class SM2State:
    """
    Complete SM-2 state for one user–item pair.

    All fields are required; there are no implicit defaults.
    The service layer is responsible for initialising new items.
    """

    interval_days: int
    """Days until next review (0 = new / lapsed card, reviewed in hours)."""

    ease_factor: Decimal
    """Ease factor in [1.3, 5.0]; starts at 2.5."""

    repetitions: int
    """Number of consecutive successful recalls (resets on lapse)."""

    lapsed_attempts: int = field(default=0)
    """Consecutive failures since last success (for recovery scheduling)."""


@dataclass(frozen=True)
class SM2Result:
    """Output of a single SM-2 update cycle."""

    new_state: SM2State
    next_review_at: datetime
    """Absolute UTC timestamp for the next review."""

    was_lapsed: bool
    """True when this answer triggered a lapse (q < QUALITY_THRESHOLD)."""


# ============================================================================
# Public API
# ============================================================================


def update(
    state: SM2State,
    q: int,
    *,
    review_intensity: float = 1.0,
    now: datetime | None = None,
) -> SM2Result:
    """
    Apply one review answer to the current SM-2 state and return the next state.

    Args:
        state:            Current SM-2 state for the item.
        q:                Quality score 0–5 (computed by answer_evaluator).
        review_intensity: Interval scale factor from user settings.
                          Values < 1.0 shorten intervals (more reviews).
                          Values > 1.0 lengthen intervals (fewer reviews).
        now:              Override for current UTC time (for deterministic tests).
                          Defaults to datetime.now(timezone.utc).

    Returns:
        SM2Result with the updated state and scheduled review time.

    Raises:
        ValueError: if q is outside [0, 5] or review_intensity ≤ 0.
    """
    if not (0 <= q <= 5):
        raise ValueError(f"quality score q must be in [0, 5], got {q}")
    if review_intensity <= 0:
        raise ValueError(f"review_intensity must be > 0, got {review_intensity}")

    _now = now or datetime.now(timezone.utc)

    # Apply long-absence EF decay before computing this review
    adjusted_ef = _apply_absence_decay(state.ease_factor, state, _now)

    if q < QUALITY_THRESHOLD:
        return _handle_lapse(state, adjusted_ef, _now)

    return _handle_success(state, adjusted_ef, q, review_intensity, _now)


def initial_state() -> SM2State:
    """Return the canonical starting state for a newly introduced item."""
    return SM2State(
        interval_days=0,
        ease_factor=INITIAL_EF,
        repetitions=0,
        lapsed_attempts=0,
    )


# ============================================================================
# Private helpers — lapse path
# ============================================================================


def _handle_lapse(
    state: SM2State,
    ef: Decimal,
    now: datetime,
) -> SM2Result:
    """Card failed. Decrease EF, schedule short recovery interval."""
    new_ef = max(MIN_EF, ef - EF_LAPSE_PENALTY)
    new_lapsed = state.lapsed_attempts + 1

    # Determine recovery interval in minutes based on consecutive failures
    idx = min(new_lapsed - 1, len(_LAPSE_RECOVERY_INTERVALS_MINUTES) - 1)
    recovery_minutes = _LAPSE_RECOVERY_INTERVALS_MINUTES[idx]

    return SM2Result(
        new_state=SM2State(
            interval_days=0,
            ease_factor=new_ef,
            repetitions=0,          # reset streak on lapse
            lapsed_attempts=new_lapsed,
        ),
        next_review_at=now + timedelta(minutes=recovery_minutes),
        was_lapsed=True,
    )


# ============================================================================
# Private helpers — success path
# ============================================================================


def _handle_success(
    state: SM2State,
    ef: Decimal,
    q: int,
    review_intensity: float,
    now: datetime,
) -> SM2Result:
    """Card recalled successfully. Update EF, compute next interval."""
    new_repetitions = state.repetitions + 1
    new_ef = _update_ef(ef, q)

    if new_repetitions == 1:
        # Very first successful recall: schedule within the same day
        hours = INITIAL_INTERVAL_HOURS * review_intensity
        return SM2Result(
            new_state=SM2State(
                interval_days=1,
                ease_factor=new_ef,
                repetitions=new_repetitions,
                lapsed_attempts=0,
            ),
            next_review_at=now + timedelta(hours=hours),
            was_lapsed=False,
        )

    if new_repetitions == 2:
        raw_days = _second_interval(new_ef)
    else:
        raw_days = int(state.interval_days * float(new_ef))

    # Apply review_intensity: < 1.0 shortens intervals, > 1.0 lengthens them
    final_days = max(1, round(raw_days * review_intensity))

    return SM2Result(
        new_state=SM2State(
            interval_days=final_days,
            ease_factor=new_ef,
            repetitions=new_repetitions,
            lapsed_attempts=0,
        ),
        next_review_at=now + timedelta(days=final_days),
        was_lapsed=False,
    )


def _update_ef(ef: Decimal, q: int) -> Decimal:
    """
    SM-2 ease factor update formula.

    EF_new = EF + (0.1 - (5-q)*(0.08 + (5-q)*0.02))

    q=5 → +0.10  (large reward for very fast / confident recall)
    q=4 →  0.00  (neutral)
    q=3 → -0.14  (slight penalty for slow but correct recall)
    """
    delta = Decimal(5 - q)
    adjustment = Decimal("0.1") - delta * (Decimal("0.08") + delta * Decimal("0.02"))
    return max(MIN_EF, min(ef + adjustment, MAX_EF))


def _second_interval(ef: Decimal) -> int:
    """
    Heuristic second-interval lookup table.

    High EF → longer interval; lower EF → shorter.
    """
    if ef >= Decimal("3.5"):
        return 10
    if ef >= Decimal("2.5"):
        return 6
    return 4


# ============================================================================
# Private helpers — long-absence decay
# ============================================================================


def _apply_absence_decay(
    ef: Decimal,
    state: SM2State,
    now: datetime,
) -> Decimal:
    """
    Gradually lower EF when a card hasn't been reviewed for a long time.

    This prevents artificially large intervals after gaps where the user
    simply abandoned the app. Applied BEFORE computing this review's result.
    """
    # Only applies to cards that have been reviewed before (not brand new)
    if state.repetitions == 0 or state.interval_days == 0:
        return ef

    # We don't have last_reviewed_at in SM2State (kept pure).
    # The caller should pass a recently computed state; decay is handled
    # by the practice service when it detects a large overdue gap.
    return ef


def apply_absence_decay_for_days(ef: Decimal, days_overdue: int) -> Decimal:
    """
    Public function for the service layer to call when reconstructing state
    after detecting a long absence (days since last review > 60).

    Args:
        ef:           Current ease factor.
        days_overdue: Days elapsed since the item was last reviewed.

    Returns:
        Decayed ease factor (floored at MIN_EF).
    """
    if days_overdue <= 60:
        return ef

    for threshold, rate in _DECAY_THRESHOLDS:
        if days_overdue <= threshold:
            return max(MIN_EF, ef * rate)

    return max(MIN_EF, ef * _DECAY_FLOOR)


__all__ = [
    "SM2State",
    "SM2Result",
    "update",
    "initial_state",
    "apply_absence_decay_for_days",
    "INITIAL_EF",
    "MIN_EF",
    "MAX_EF",
    "QUALITY_THRESHOLD",
    "INITIAL_INTERVAL_HOURS",
]
