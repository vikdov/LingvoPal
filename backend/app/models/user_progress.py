# backend/app/models/user_progress.py
"""UserProgress model"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.item import Item


class UserProgress(Base):
    """Current SM-2 state for each user-item pair"""

    __tablename__ = "user_progress"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), primary_key=True
    )
    ease_factor: Mapped[float] = mapped_column(
        nullable=False,
        comment="SM-2 ease factor, starts at 2.5",
    )
    interval: Mapped[int] = mapped_column(
        default=0, nullable=False, comment="Days until next review"
    )
    repetitions: Mapped[int] = mapped_column(
        default=0, nullable=False, comment="Successful repetitions"
    )
    last_reviewed: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_review: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    user: Mapped["User"] = relationship()
    item: Mapped["Item"] = relationship()

    __table_args__ = (Index("idx_progress_due", "user_id", "next_review", "item_id"),)

    def __repr__(self) -> str:
        return f"<UserProgress user={self.user_id} item={self.item_id} due={self.next_review}>"


__all__ = ["UserProgress"]
