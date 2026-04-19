# backend/app/models/study_review.py
"""StudyReview model"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Index, text
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.item import Item
    from app.models.language import Language
    from app.models.translation import Translation
    from app.models.set import Set
    from app.models.study_session import StudySession


class StudyReview(Base):
    """Immutable append-only log of study activities"""

    __tablename__ = "study_reviews"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), nullable=False
    )
    language_id: Mapped[int] = mapped_column(
        ForeignKey("languages.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Denormalized for performance — avoids join on hot path",
    )
    translation_id: Mapped[int | None] = mapped_column(
        ForeignKey("translations.id", ondelete="SET NULL"), nullable=True
    )
    set_id: Mapped[int] = mapped_column(
        ForeignKey("sets.id", ondelete="CASCADE"), nullable=False
    )
    session_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("study_sessions.id", ondelete="CASCADE"), nullable=False
    )
    was_correct: Mapped[bool] = mapped_column(nullable=False)
    user_answer: Mapped[str | None] = mapped_column(nullable=True)
    response_time: Mapped[int] = mapped_column(nullable=False, comment="Milliseconds")
    ease_before: Mapped[float] = mapped_column(nullable=False)
    interval_before: Mapped[int] = mapped_column(nullable=False, comment="Days")
    ease_after: Mapped[float | None] = mapped_column(nullable=True)
    interval_after: Mapped[int | None] = mapped_column(nullable=True, comment="Days")
    reviewed_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship()
    item: Mapped["Item"] = relationship()
    language: Mapped["Language"] = relationship()
    translation: Mapped["Translation"] = relationship()
    set: Mapped["Set"] = relationship()
    session: Mapped["StudySession"] = relationship(back_populates="reviews")

    __table_args__ = (
        Index("idx_study_reviews_user_item", "user_id", "item_id", "reviewed_at"),
        Index("idx_study_reviews_set_user", "set_id", "user_id", "reviewed_at"),
        Index("idx_study_reviews_reviewed_at", "reviewed_at"),
        Index(
            "idx_study_reviews_incorrect",
            "user_id",
            "reviewed_at",
            postgresql_where=text("was_correct = FALSE"),
        ),
        Index(
            "uq_study_reviews_session_item",
            "session_id",
            "item_id",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<StudyReview {self.id}: item={self.item_id} correct={self.was_correct}>"
        )


__all__ = ["StudyReview"]
