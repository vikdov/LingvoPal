"""Practice session schemas — request/response validation."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ── Comparison config (sent at session start, consumed by frontend) ───────────


class ComparisonConfig(BaseModel):
    """
    Tells the frontend how to do approximate string comparison and
    which hints to surface per item.

    Derived from UserSettings at session creation. Re-sent if the user
    changes settings mid-session via PATCH /sessions/{id}/config.
    """

    evaluation_mode: Literal["strict", "normal", "forgiving"] = "normal"
    show_hints_on_fails: bool = True
    show_translations: bool = True
    show_images: bool = True
    show_synonyms: bool = True
    show_part_of_speech: bool = True
    auto_play_audio: bool = False


# ── Per-item hint (one entry per item in the full batch) ──────────────────────


class ItemHintSchema(BaseModel):
    """
    Everything the frontend needs to render one practice card and do
    the approximate correctness check locally.

    answer       — item.term: the word the user must type (used for comparison)
    prompt       — translation.term_trans shown as the "fill in the gap" hint
    context      — source-language sentence containing the gap
    context_trans — target-language version of the context sentence
    synonyms     — other accepted spellings / related terms (display only)
    last_reviewed — how long ago the user last saw this item (display only)
    """

    item_id: int
    answer: str
    prompt: str
    context: str | None = None
    context_trans: str | None = None
    image_url: str | None = None
    audio_url: str | None = None
    part_of_speech: str | None = None
    synonyms: list[str] = Field(default_factory=list)
    last_reviewed: datetime | None = None
    translation_id: int | None = None


# ── Session start ─────────────────────────────────────────────────────────────


class StartSessionRequest(BaseModel):
    set_id: int = Field(..., gt=0)


class SessionStartedResponse(BaseModel):
    """
    Returned when a session is created.

    The full item batch is sent upfront so the frontend can practice
    entirely offline — no per-card round-trips needed.
    """

    session_id: int
    set_id: int
    items: list[ItemHintSchema]
    comparison_config: ComparisonConfig


# ── Per-answer submission (fire-and-forget) ───────────────────────────────────


class SubmitAnswerRequest(BaseModel):
    answer_id: str = Field(
        ..., min_length=1, max_length=64, description="UUID4 idempotency key"
    )
    item_id: int = Field(..., gt=0)
    user_answer: str = Field(..., max_length=500)
    response_time_ms: int = Field(..., ge=100, le=120_000)
    confidence_override: int | None = Field(None, ge=1, le=5)


class AnswerBufferedResponse(BaseModel):
    """202 Accepted — answer stored in Redis, SM-2 deferred to finalise."""

    buffered: bool = True
    remaining_count: int
    is_batch_complete: bool
    is_correct: bool
    similarity: float


# ── Finalise / abandon ────────────────────────────────────────────────────────


class SessionSummaryResponse(BaseModel):
    session_id: int
    status: str
    total_reviewed: int
    correct_count: int
    accuracy: float
    avg_response_ms: int
    leech_item_ids: list[int]


# ── Active session recovery ───────────────────────────────────────────────────


class ActiveSessionResponse(BaseModel):
    has_active_session: bool
    session_id: int | None = None
    set_id: int | None = None
    remaining_count: int | None = None


__all__ = [
    "ComparisonConfig",
    "ItemHintSchema",
    "StartSessionRequest",
    "SessionStartedResponse",
    "SubmitAnswerRequest",
    "AnswerBufferedResponse",
    "SessionSummaryResponse",
    "ActiveSessionResponse",
]
