# backend/app/models/study_session.py
"""StudySession model"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import ENUM as pgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import SessionStatus

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.set import Set
    from app.models.study_review import StudyReview


class StudySession(Base):
    """Study session tracking"""

    __tablename__ = "study_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    set_id: Mapped[int] = mapped_column(
        ForeignKey("sets.id", ondelete="CASCADE"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(nullable=True)
    status: Mapped[SessionStatus] = mapped_column(
        pgEnum(SessionStatus, name="session_status_type", create_type=False, values_callable=lambda obj: [e.value for e in obj]),
        default=SessionStatus.IN_PROGRESS,
        nullable=False,
    )
    correct_count: Mapped[int] = mapped_column(default=0, nullable=False)
    incorrect_count: Mapped[int] = mapped_column(default=0, nullable=False)
    total_time_ms: Mapped[int] = mapped_column(default=0, nullable=False)
    items_reviewed: Mapped[int] = mapped_column(default=0, nullable=False)

    user: Mapped["User"] = relationship()
    set: Mapped["Set"] = relationship()
    reviews: Mapped[list["StudyReview"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )
    __table_args__ = (
        Index("idx_study_sessions_user", "user_id", "started_at"),
        Index("idx_study_sessions_active", "user_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<StudySession {self.id}: user={self.user_id}>"


__all__ = ["StudySession"]
