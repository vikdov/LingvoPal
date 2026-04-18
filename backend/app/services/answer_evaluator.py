# backend/app/services/answer_evaluator.py
"""
Answer Evaluator — correctness detection and quality (q) scoring.

Responsibilities:
  - Normalise both answers (lowercase, trim, strip diacritics)
  - Compute Levenshtein similarity (pure DP, no external dependency)
  - Determine correctness based on evaluation_mode threshold
  - Cap response time at T_MAX to filter "focus loss" distortion
  - Map (correctness, speed_ratio, confidence_override) → q ∈ {1,3,4,5}

Does NOT touch the database or Redis.
Does NOT perform SM-2 scheduling.
Fully unit-testable with no mocks.

Quality mapping (spec-compliant):
  Incorrect                           → q = 1
  Correct + ratio > VERY_SLOW_THRESHOLD → q = 3
  Correct + NORMAL range              → q = 4
  Correct + ratio < FAST_THRESHOLD    → q = 5
  Correct + override = 1 (blackout)   → q = 1  (user felt completely lost)
  Correct + override = 2 (hard)       → q = 3
  Correct + override = 3 (neutral)    → speed-based quality
  Correct + override = 4 (good)       → max(4, speed_quality)
  Correct + override = 5 (easy)       → q = 5
"""

import logging
import unicodedata
from dataclasses import dataclass
from typing import Final

from app.models.enums import EvaluationMode

logger = logging.getLogger(__name__)

# ============================================================================
# Constants
# ============================================================================

# Correctness thresholds per evaluation mode (Levenshtein similarity ratio)
SIMILARITY_THRESHOLDS: Final[dict[EvaluationMode, float]] = {
    EvaluationMode.STRICT: 0.95,
    EvaluationMode.NORMAL: 0.90,
    EvaluationMode.FORGIVING: 0.80,
}

# Response time cap: anything above this is treated as exactly T_MAX
# (prevents tab-switching / long pauses from inflating "slow" signal)
T_MAX_MS: Final[int] = 10_000  # 10 seconds

# Default expected response time when no history is available
DEFAULT_EXPECTED_MS: Final[int] = 3_000  # 3 seconds

# Speed ratio thresholds for quality mapping
FAST_THRESHOLD: Final[float] = 0.80   # ratio < this → q=5 (fast)
VERY_SLOW_THRESHOLD: Final[float] = 1.50   # ratio > this → q=3 (slow)

ConfidenceOverride = int | None  # 1=blackout, 2=hard, 3=neutral, 4=good, 5=easy


# ============================================================================
# Data contracts
# ============================================================================


@dataclass(frozen=True)
class EvaluationContext:
    """
    Everything the evaluator needs for a single answer judgment.

    The caller (practice_service) is responsible for resolving expected_time_ms
    via the hierarchy: user-item avg → user-category avg → global avg → default.
    """

    user_answer: str
    correct_answer: str
    response_time_ms: int
    """Raw time-to-answer in milliseconds (will be capped internally)."""

    expected_time_ms: int = DEFAULT_EXPECTED_MS
    """Pre-computed expected time for this item and user (see above)."""

    evaluation_mode: EvaluationMode = EvaluationMode.NORMAL
    confidence_override: ConfidenceOverride = None


@dataclass(frozen=True)
class EvaluationResult:
    """Output of a single answer evaluation."""

    is_correct: bool
    similarity: float
    """Normalised Levenshtein similarity in [0.0, 1.0]."""

    quality: int
    """SM-2 quality score in {1, 3, 4, 5} (fed directly into sm2_engine.update)."""

    time_ratio: float
    """capped_response_ms / expected_time_ms."""

    capped_response_ms: int
    """min(response_time_ms, T_MAX_MS) — the value used for ratio computation."""


# ============================================================================
# Public API
# ============================================================================


def evaluate(ctx: EvaluationContext) -> EvaluationResult:
    """
    Evaluate one answer and return a quality score for the SM-2 engine.

    All logging for future model tuning is emitted here (similarity, time_delta, q).
    """
    norm_user = _normalise(ctx.user_answer)
    norm_correct = _normalise(ctx.correct_answer)

    similarity = _levenshtein_similarity(norm_user, norm_correct)
    threshold = SIMILARITY_THRESHOLDS[ctx.evaluation_mode]
    is_correct = similarity >= threshold

    capped_ms = min(ctx.response_time_ms, T_MAX_MS)
    time_ratio = capped_ms / ctx.expected_time_ms if ctx.expected_time_ms > 0 else 1.0

    quality = map_quality(is_correct, time_ratio, ctx.confidence_override)

    logger.debug(
        "answer_evaluated",
        extra={
            "similarity": round(similarity, 4),
            "time_delta_ms": capped_ms,
            "time_ratio": round(time_ratio, 3),
            "quality": quality,
            "is_correct": is_correct,
            "evaluation_mode": ctx.evaluation_mode.value,
            "confidence_override": ctx.confidence_override,
        },
    )

    return EvaluationResult(
        is_correct=is_correct,
        similarity=similarity,
        quality=quality,
        time_ratio=time_ratio,
        capped_response_ms=capped_ms,
    )


# ============================================================================
# Private — text normalisation
# ============================================================================


def _normalise(text: str) -> str:
    """
    Lowercase, strip leading/trailing whitespace, and remove diacritics.

    "café" → "cafe", "Üniversität" → "universitat"
    """
    text = text.strip().lower()
    # NFD decomposition splits combined characters (e.g. é → e + combining accent)
    # then we discard non-ASCII (i.e. the combining marks)
    text = unicodedata.normalize("NFD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return text


# ============================================================================
# Private — Levenshtein similarity (pure DP, no external dependencies)
# ============================================================================


def _levenshtein_similarity(a: str, b: str) -> float:
    """
    Compute Levenshtein similarity ratio in [0.0, 1.0].

    similarity = 1 - (edit_distance / max(len(a), len(b)))

    Empty-string edge cases:
      ("", "")  → 1.0  (both empty = exact match)
      ("", "x") → 0.0
    """
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0

    m, n = len(a), len(b)

    # Space-optimised two-row DP (O(min(m,n)) space)
    if m < n:
        a, b, m, n = b, a, n, m

    prev = list(range(n + 1))
    curr = [0] * (n + 1)

    for i in range(1, m + 1):
        curr[0] = i
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                curr[j] = prev[j - 1]
            else:
                curr[j] = 1 + min(prev[j], curr[j - 1], prev[j - 1])
        prev, curr = curr, prev

    edit_distance = prev[n]
    return 1.0 - edit_distance / m  # m is the longer string


# ============================================================================
# Private — quality mapping
# ============================================================================


def map_quality(
    is_correct: bool,
    time_ratio: float,
    confidence_override: ConfidenceOverride,
) -> int:
    """
    Deterministic quality score mapping.

    Returns an integer in {1, 3, 4, 5} following the spec:
      - Incorrect                   → 1 (regardless of override)
      - Correct + override 1        → 1 (blackout: user felt completely lost)
      - Correct + override 2        → 3 (hard)
      - Correct + override 3/None   → speed-based quality
      - Correct + override 4        → max(4, speed_quality)
      - Correct + override 5        → 5 (easy/perfect)
      - Correct + fast (< 0.80)     → 5
      - Correct + normal (0.80–1.50)→ 4
      - Correct + slow  (> 1.50)    → 3
    """
    if not is_correct:
        return 1

    if time_ratio < FAST_THRESHOLD:
        speed_quality = 5
    elif time_ratio <= VERY_SLOW_THRESHOLD:
        speed_quality = 4
    else:
        speed_quality = 3

    if confidence_override == 1:
        return 1
    if confidence_override == 2:
        return 3
    if confidence_override == 4:
        return max(4, speed_quality)
    if confidence_override == 5:
        return 5

    return speed_quality


__all__ = [
    "EvaluationContext",
    "EvaluationResult",
    "evaluate",
    "map_quality",
    "SIMILARITY_THRESHOLDS",
    "T_MAX_MS",
    "DEFAULT_EXPECTED_MS",
    "FAST_THRESHOLD",
    "VERY_SLOW_THRESHOLD",
]
