# backend/app/models/content_complaint.py
"""ContentComplaint model — user-filed reports on community content."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM as pgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.mixins import CreatedAtMixin
from app.models.enums import ComplaintReason, ModerationTargetType

if TYPE_CHECKING:
    from app.models.user import User


class ContentComplaint(Base, CreatedAtMixin):
    """
    A user-filed report on a COMMUNITY item or set.
    One complaint per (reporter, target). Escalation threshold checked by service.
    No status field — complaints are consumed by escalation and remain for audit.
    """

    __tablename__ = "content_complaints"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target_type: Mapped[ModerationTargetType] = mapped_column(
        pgEnum(ModerationTargetType, name="moderation_target_type", create_type=False, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    target_id: Mapped[int] = mapped_column(nullable=False)
    reporter_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    reason: Mapped[ComplaintReason] = mapped_column(
        pgEnum(ComplaintReason, name="complaintreason"),
        nullable=False,
    )
    details: Mapped[str | None] = mapped_column(nullable=True)

    reporter: Mapped["User"] = relationship()

    __table_args__ = (
        UniqueConstraint("reporter_id", "target_type", "target_id", name="uq_complaint_per_user"),
        Index("idx_complaints_target", "target_type", "target_id"),
        Index("idx_complaints_reporter_day", "reporter_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<ContentComplaint {self.id}: {self.target_type.value} "
            f"{self.target_id} by user {self.reporter_id}>"
        )


__all__ = ["ContentComplaint"]
