# backend/app/services/sm2_engine.py
"""
SM-2 Engine — pure algorithm, zero side effects.

This module contains ONLY the scheduling mathematics.
It knows nothing about databases, HTTP, users, or answer evaluation.
Every function is a pure transformation: (state, q) → next_state.

SM-2 algorithm overview:
  - q ≥ 3  → successful recall  → interval grows via ease factor
  - q < 3  → failure (lapse)    → interval drops proportionally, EF unchanged
  - n=1 success: 1-day interval (review next day)
  - n=1 lapse:   1-hour interval (never recalled — show again this session)
  - n=2: short interval based on EF (4–10 days)
  - n>2: interval = prev_interval × EF

Deviations from original SM-2 (intentional):
  - Lapse interval: proportional drop (interval × 0.33) instead of reset to 1 day.
    Mature cards (interval > 3 days) set repetitions=1 to skip 6-hour re-learning.
  - EF unchanged on lapse (original SM-2 behaviour — we do NOT penalise EF).
  - First interval: 1 day (matches original SM-2; overnight gap aids consolidation).
  - Second interval: EF-based heuristic (4/6/10 days) instead of flat 6 days.
  - q=3 (slow-correct): EF treated as neutral (same as q=4). Instead, the computed
    interval for that cycle is scaled by SLOW_ANSWER_INTERVAL_FACTOR (0.75). This
    separates "item difficulty" (long-term EF) from "momentary retrieval latency"
    (one-time interval nudge). Effortful-but-correct recall strengthens memory and
    should not permanently degrade scheduling.

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

# Lapse: interval shrinks to this fraction of the previous interval
LAPSE_INTERVAL_FACTOR: Final[Decimal] = Decimal("0.33")

# Minimum recovery interval after any lapse (days)
MIN_LAPSE_DAYS: Final[int] = 1

# Re-show interval for a card never successfully recalled
NEW_CARD_LAPSE_HOURS: Final[int] = 1

# Cards with interval_days above this are considered mature
_MATURE_CARD_DAYS: Final[int] = 3

# q=3 (slow-correct): this factor shortens the interval for that cycle only.
# EF is left neutral — latency shouldn't degrade long-term ease.
SLOW_ANSWER_INTERVAL_FACTOR: Final[Decimal] = Decimal("0.75")

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
    """Total lifetime lapse count for this item (never resets)."""


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
    """Card failed. EF unchanged (original SM-2). Interval drops proportionally."""
    new_lapsed = state.lapsed_attempts + 1

    if state.repetitions == 0:
        # Never successfully recalled — show again in 1 hour
        return SM2Result(
            new_state=SM2State(
                interval_days=0,
                ease_factor=ef,
                repetitions=0,
                lapsed_attempts=new_lapsed,
            ),
            next_review_at=now + timedelta(hours=NEW_CARD_LAPSE_HOURS),
            was_lapsed=True,
        )

    mature = state.interval_days > _MATURE_CARD_DAYS
    if mature:
        recovery_days = max(MIN_LAPSE_DAYS, round(state.interval_days * float(LAPSE_INTERVAL_FACTOR)))
        new_repetitions = 1
    else:
        recovery_days = MIN_LAPSE_DAYS
        new_repetitions = 0

    return SM2Result(
        new_state=SM2State(
            interval_days=recovery_days,
            ease_factor=ef,
            repetitions=new_repetitions,
            lapsed_attempts=new_lapsed,
        ),
        next_review_at=now + timedelta(days=recovery_days),
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
    """Card recalled successfully. Update EF, compute next interval.

    q=3 (slow-correct): EF updated as if q=4 (neutral). Interval scaled by
    SLOW_ANSWER_INTERVAL_FACTOR for this cycle only — see module docstring.
    """
    new_repetitions = state.repetitions + 1

    # q=3: EF neutral (don't penalise long-term ease for slow-but-correct recall)
    ef_q = q if q > QUALITY_THRESHOLD else QUALITY_THRESHOLD + 1
    new_ef = _update_ef(ef, ef_q)

    slow = q == QUALITY_THRESHOLD

    if new_repetitions == 1:
        raw_first = 1 * (float(SLOW_ANSWER_INTERVAL_FACTOR) if slow else 1.0)
        first_days = max(1, round(raw_first * review_intensity))
        return SM2Result(
            new_state=SM2State(
                interval_days=first_days,
                ease_factor=new_ef,
                repetitions=new_repetitions,
                lapsed_attempts=state.lapsed_attempts,
            ),
            next_review_at=now + timedelta(days=first_days),
            was_lapsed=False,
        )

    if new_repetitions == 2:
        raw_days = _second_interval(new_ef)
    else:
        raw_days = int(state.interval_days * float(new_ef))

    slow_scale = float(SLOW_ANSWER_INTERVAL_FACTOR) if slow else 1.0
    final_days = max(1, round(raw_days * slow_scale * review_intensity))

    return SM2Result(
        new_state=SM2State(
            interval_days=final_days,
            ease_factor=new_ef,
            repetitions=new_repetitions,
            lapsed_attempts=state.lapsed_attempts,
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
    "LAPSE_INTERVAL_FACTOR",
    "MIN_LAPSE_DAYS",
    "NEW_CARD_LAPSE_HOURS",
    "SLOW_ANSWER_INTERVAL_FACTOR",
]
