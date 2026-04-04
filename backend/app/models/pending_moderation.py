# backend/app/models/pending_moderation.py
"""PendingModeration model"""

from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import ENUM as pgEnum, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ModerationTargetType

if TYPE_CHECKING:
    from app.models.user import User


class PendingModeration(Base):
    """Content pending moderator review"""

    __tablename__ = "pending_moderation"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target_type: Mapped[ModerationTargetType] = mapped_column(
        pgEnum(ModerationTargetType, name="moderation_target_type", create_type=False),
        nullable=False,
    )
    target_id: Mapped[int] = mapped_column(nullable=False)
    creator_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    feedback: Mapped[str | None] = mapped_column(nullable=True)
    patch_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(nullable=True)
    moderator_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resolution_feedback: Mapped[str | None] = mapped_column(nullable=True)

    creator: Mapped["User"] = relationship(
        foreign_keys=[creator_id],
        primaryjoin="PendingModeration.creator_id == User.id",
    )
    moderator: Mapped["User"] = relationship(
        foreign_keys=[moderator_id],
        primaryjoin="PendingModeration.moderator_id == User.id",
    )

    __table_args__ = (
        Index(
            "idx_pending_mod_unresolved",
            "resolved_at",
            "created_at",
            postgresql_where=text("resolved_at IS NULL"),
        ),
        Index(
            "idx_pending_mod_creator_unresolved",
            "creator_id",
            "resolved_at",
            postgresql_where=text("resolved_at IS NULL"),
        ),
    )

    def __repr__(self) -> str:
        return f"<PendingModeration {self.id}: {self.target_type}:{self.target_id}>"


__all__ = ["PendingModeration"]
