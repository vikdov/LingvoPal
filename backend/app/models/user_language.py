# backend/app/models/user_language.py
"""UserLanguage — join table tracking the languages a user is learning."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.language import Language
    from app.models.user import User


class UserLanguage(Base):
    """
    Tracks which languages a user is learning.

    Composite PK (user_id, language_id).
    At most one row per user can have is_active=True (enforced via partial
    unique index in the migration — not expressible as a pure ORM constraint).
    """

    __tablename__ = "user_languages"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    language_id: Mapped[int] = mapped_column(
        ForeignKey("languages.id", ondelete="CASCADE"),
        primary_key=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Exactly one row per user may be True (enforced by partial index)",
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="languages", foreign_keys=[user_id])
    language: Mapped["Language"] = relationship(foreign_keys=[language_id])

    __table_args__ = (
        UniqueConstraint("user_id", "language_id", name="uq_user_languages"),
    )

    def __repr__(self) -> str:
        return f"<UserLanguage user={self.user_id} lang={self.language_id} active={self.is_active}>"


__all__ = ["UserLanguage"]
