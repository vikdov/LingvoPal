# backend/app/models/set.py
"""Set (collection of items) model"""

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import ENUM as pgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, SoftDeleteTimestampMixin
from app.models.enums import ContentStatus

if TYPE_CHECKING:
    from app.models.language import Language
    from app.models.user import User
    from app.models.set_item import SetItem
    from app.models.item import Item


class Set(Base, SoftDeleteTimestampMixin):
    """Collection of items to study together"""

    __tablename__ = "sets"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    difficulty: Mapped[int | None] = mapped_column(nullable=True, comment="1–7 scale")
    source_lang_id: Mapped[int] = mapped_column(
        ForeignKey("languages.id", ondelete="RESTRICT"), nullable=False
    )
    target_lang_id: Mapped[int] = mapped_column(
        ForeignKey("languages.id", ondelete="RESTRICT"), nullable=False
    )
    creator_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    verified_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[ContentStatus] = mapped_column(
        pgEnum(ContentStatus, name="content_status", create_type=False, values_callable=lambda obj: [e.value for e in obj]),
        default=ContentStatus.DRAFT,
        nullable=False,
    )
    source_language: Mapped["Language"] = relationship(foreign_keys=[source_lang_id])
    target_language: Mapped["Language"] = relationship(foreign_keys=[target_lang_id])
    creator: Mapped["User"] = relationship(
        foreign_keys=[creator_id],
        primaryjoin="Set.creator_id == User.id",
    )
    verifier: Mapped["User"] = relationship(
        foreign_keys=[verified_by],
        primaryjoin="Set.verified_by == User.id",
    )
    set_items: Mapped[list["SetItem"]] = relationship(
        back_populates="set",
        cascade="all, delete-orphan",
    )
    items: Mapped[list["Item"]] = relationship(
        secondary="set_items",
        viewonly=True,
    )

    __table_args__ = (
        CheckConstraint(
            "source_lang_id != target_lang_id",
            name="chk_lang_pair_different",
        ),
        CheckConstraint("difficulty BETWEEN 1 AND 7", name="chk_set_difficulty"),
        Index(
            "idx_sets_discovery",
            "status",
            "target_lang_id",
            "difficulty",
            postgresql_where=text(
                "deleted_at IS NULL AND status IN ('approved', 'official')"
            ),
        ),
    )

    def __repr__(self) -> str:
        return f"<Set {self.id}: {self.title}>"


__all__ = ["Set"]
