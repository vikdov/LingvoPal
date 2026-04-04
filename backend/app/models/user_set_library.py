# backend/app/models/user_set_library.py
"""UserSetLibrary model"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.set import Set


class UserSetLibrary(Base):
    """User's saved/pinned sets"""

    __tablename__ = "user_set_library"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    set_id: Mapped[int] = mapped_column(
        ForeignKey("sets.id", ondelete="CASCADE"), primary_key=True
    )
    added_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    last_opened_at: Mapped[datetime | None] = mapped_column(nullable=True)
    is_pinned: Mapped[bool] = mapped_column(default=False, nullable=False)

    user: Mapped["User"] = relationship()
    set: Mapped["Set"] = relationship()

    __table_args__ = (
        Index("idx_user_set_library_pinned", "user_id", "is_pinned", "added_at"),
        Index(
            "idx_user_set_library_recent",
            "user_id",
            "last_opened_at",
            postgresql_where=text("last_opened_at IS NOT NULL"),
        ),
    )

    def __repr__(self) -> str:
        return f"<UserSetLibrary user={self.user_id} set={self.set_id}>"


__all__ = ["UserSetLibrary"]
