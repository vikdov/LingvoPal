# backend/app/models/pending_session.py
"""PendingSession model — Redis safety valve"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.study_session import StudySession


class PendingSession(Base):
    """
    Safety valve: raw session events serialised from Redis before TTL expiry.

    When the TTL sweeper detects a session key nearing expiry, it writes all
    accumulated RawAnswerEvents here so they can survive a Redis restart or
    extended user absence.

    On session reconstruction (app-start recovery), the service checks this
    table if no Redis key is present and no study_reviews exist yet.
    """

    __tablename__ = "pending_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("study_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="One pending-session record per study session",
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    raw_events_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="JSON array of RawAnswerEvent — buffered per-answer data",
    )
    session_state_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Snapshot of SessionState metadata (item_order, current_index, config)",
    )
    saved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    recovered: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="True once finalise_session has processed this record",
    )

    study_session: Mapped["StudySession"] = relationship()
    user: Mapped["User"] = relationship()

    __table_args__ = (
        Index("idx_pending_sessions_user", "user_id", "recovered"),
    )

    def __repr__(self) -> str:
        return f"<PendingSession session={self.session_id} recovered={self.recovered}>"


__all__ = ["PendingSession"]
