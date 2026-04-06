# backend/app/schemas/practice.py
"""Practice schemas — Python 3.10+ syntax, no business logic"""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, computed_field


class StartStudySessionRequest(BaseModel):
    """POST /api/v1/practice/sessions"""

    set_id: int = Field(..., gt=0)


class SubmitReviewRequest(BaseModel):
    """POST /api/v1/practice/sessions/{session_id}/reviews"""

    item_id: int = Field(..., gt=0)
    was_correct: bool
    user_answer: str | None = Field(None, max_length=1000)
    response_time: int = Field(
        ...,
        ge=0,
        le=600_000,  # Allow up to 10 minutes
        description="Time to answer (ms). If >60s, consider it a session break.",
    )


class QuestionResponse(BaseModel):
    """Next question to answer"""

    session_id: int
    item_id: int
    term: str
    context: str | None = None
    part_of_speech: str | None = None
    difficulty: int | None = None
    correct_translation: str
    alternative_translations: list[str] = Field(default_factory=list)


class StudyReviewResponse(BaseModel):
    """Single review in a session"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    was_correct: bool
    user_answer: str | None = None
    response_time: int
    ease_before: float
    ease_after: float | None = None
    interval_before: int
    interval_after: int | None = None
    reviewed_at: datetime
    created_at: datetime


class StudySessionResponse(BaseModel):
    """Study session summary"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    set_id: int
    started_at: datetime
    ended_at: datetime | None = None
    correct_count: int
    incorrect_count: int
    total_time_ms: int
    items_reviewed: int
    created_at: datetime

    @computed_field
    @property
    def is_active(self) -> bool:
        return self.ended_at is None

    @computed_field
    @property
    def accuracy_percent(self) -> float:
        total = self.correct_count + self.incorrect_count
        if total == 0:
            return 0.0
        return round((self.correct_count / total) * 100, 2)

    @computed_field
    @property
    def avg_response_time_ms(self) -> float:
        if self.items_reviewed == 0:
            return 0.0
        return round(self.total_time_ms / self.items_reviewed, 0)


class StudySessionDetailResponse(StudySessionResponse):
    """Session with reviews (no business logic here!)"""

    reviews: list[StudyReviewResponse] = Field(default_factory=list)

    # Set by service layer, not computed here
    confidence_level: Literal["low", "medium", "high"] = Field(
        ..., description="Classification from service layer"
    )


class SessionHistoryQueryParams(BaseModel):
    """GET /api/v1/practice/sessions query parameters"""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    set_id: int | None = Field(None, gt=0)
    status: Literal["active", "completed"] | None = None


__all__ = [
    "StartStudySessionRequest",
    "SubmitReviewRequest",
    "QuestionResponse",
    "StudyReviewResponse",
    "StudySessionResponse",
    "StudySessionDetailResponse",
    "SessionHistoryQueryParams",
]
