# backend/app/models/user_stats_total.py
"""UserStatsTotal model"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.language import Language


class UserStatsTotal(Base):
    """Aggregated statistics across all time per user per language"""

    __tablename__ = "user_stats_total"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    language_id: Mapped[int] = mapped_column(
        ForeignKey("languages.id", ondelete="RESTRICT"), primary_key=True
    )
    total_seconds: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0"),
        nullable=False,
    )
    total_words: Mapped[int] = mapped_column(default=0, nullable=False)
    last_repaired: Mapped[datetime | None] = mapped_column(nullable=True)

    user: Mapped["User"] = relationship()
    language: Mapped["Language"] = relationship()

    __table_args__ = (
        CheckConstraint("total_seconds >= 0", name="chk_total_seconds"),
        CheckConstraint("total_words >= 0", name="chk_total_words"),
    )

    def __repr__(self) -> str:
        return f"<UserStatsTotal {self.user_id}:{self.language_id}>"


__all__ = ["UserStatsTotal"]
