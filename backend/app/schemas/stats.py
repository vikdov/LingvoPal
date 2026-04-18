# backend/app/schemas/stats.py
"""Statistics schemas — Python 3.10+ syntax"""

from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, computed_field


class DailyStatsResponse(BaseModel):
    """Daily stats per user per language per day"""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    language_id: int
    stat_date: date
    correct_count: int = Field(..., ge=0)
    incorrect_count: int = Field(..., ge=0)
    new_words_count: int = Field(..., ge=0)
    seconds_spent: Decimal = Field(..., ge=0)

    @computed_field
    @property
    def total_reviews(self) -> int:
        return self.correct_count + self.incorrect_count

    @computed_field
    @property
    def accuracy_percent(self) -> float:
        if self.total_reviews == 0:
            return 0.0
        return round((self.correct_count / self.total_reviews) * 100, 2)

    @computed_field
    @property
    def hours_spent(self) -> float:
        return round(float(self.seconds_spent) / 3600, 2)


class TotalStatsResponse(BaseModel):
    """Lifetime stats per user per language"""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    language_id: int
    total_seconds: Decimal = Field(..., ge=0)
    total_words: int = Field(..., ge=0)
    last_repaired: datetime | None = None

    @computed_field
    @property
    def total_hours(self) -> float:
        return round(float(self.total_seconds) / 3600, 2)

    @computed_field
    @property
    def avg_time_per_word(self) -> float:
        if self.total_words == 0:
            return 0.0
        return round(float(self.total_seconds) / self.total_words, 2)


class StatsRangeResponse(BaseModel):
    """Stats over a date range"""

    user_id: int
    language_id: int
    start_date: date
    end_date: date
    daily_stats: list[DailyStatsResponse] = Field(default_factory=list)

    @computed_field
    @property
    def total_correct(self) -> int:
        return sum(s.correct_count for s in self.daily_stats)

    @computed_field
    @property
    def total_incorrect(self) -> int:
        return sum(s.incorrect_count for s in self.daily_stats)

    @computed_field
    @property
    def total_reviews(self) -> int:
        return self.total_correct + self.total_incorrect

    @computed_field
    @property
    def accuracy_percent(self) -> float:
        if self.total_reviews == 0:
            return 0.0
        return round((self.total_correct / self.total_reviews) * 100, 2)

    @computed_field
    @property
    def total_hours(self) -> float:
        total_seconds = sum(s.seconds_spent for s in self.daily_stats)
        return round(float(total_seconds) / 3600, 2)

    @computed_field
    @property
    def days_active(self) -> int:
        return sum(1 for s in self.daily_stats if s.total_reviews > 0)

    @computed_field
    @property
    def avg_reviews_per_day(self) -> float:
        if self.days_active == 0:
            return 0.0
        return round(self.total_reviews / self.days_active, 2)


class StatsRangeQueryParams(BaseModel):
    """GET /api/v1/stats/range query parameters"""

    language_id: int = Field(..., gt=0)
    start_date: date
    end_date: date


class DailyStatsQueryParams(BaseModel):
    """GET /api/v1/stats/daily query parameters"""

    language_id: int = Field(..., gt=0)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=30, ge=1, le=365)


class HardestItemResponse(BaseModel):
    item_id: int
    term: str
    language_id: int
    total_reviews: int
    failure_rate: float


__all__ = [
    "DailyStatsResponse",
    "TotalStatsResponse",
    "StatsRangeResponse",
    "StatsRangeQueryParams",
    "DailyStatsQueryParams",
    "HardestItemResponse",
]
