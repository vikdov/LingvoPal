# backend/app/models/user_daily_stats.py
"""UserDailyStats model"""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.language import Language


class UserDailyStats(Base):
    """Daily aggregated statistics per user per language"""

    __tablename__ = "user_daily_stats"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    language_id: Mapped[int] = mapped_column(
        ForeignKey("languages.id", ondelete="RESTRICT"), primary_key=True
    )
    stat_date: Mapped[date] = mapped_column(primary_key=True)
    correct_count: Mapped[int] = mapped_column(default=0, nullable=False)
    incorrect_count: Mapped[int] = mapped_column(default=0, nullable=False)
    new_words_count: Mapped[int] = mapped_column(default=0, nullable=False)
    seconds_spent: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0"),
        nullable=False,
        comment="NUMERIC avoids float truncation",
    )

    user: Mapped["User"] = relationship()
    language: Mapped["Language"] = relationship()

    __table_args__ = (
        CheckConstraint("correct_count >= 0", name="chk_daily_correct"),
        CheckConstraint("incorrect_count >= 0", name="chk_daily_incorrect"),
        CheckConstraint("new_words_count >= 0", name="chk_daily_new_words"),
        CheckConstraint("seconds_spent >= 0", name="chk_daily_seconds"),
        Index("idx_daily_stats_date", "user_id", "language_id", "stat_date"),
        Index("idx_daily_stats_user_range", "user_id", "stat_date"),
    )

    def __repr__(self) -> str:
        return f"<UserDailyStats {self.user_id}:{self.language_id} {self.stat_date}>"


__all__ = ["UserDailyStats"]
