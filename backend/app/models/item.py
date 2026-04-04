# backend/app/models/item.py
"""Item (learning vocabulary) model"""

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin, SoftDeleteMixin
from app.models.enums import ContentStatus, PartOfSpeech

if TYPE_CHECKING:
    from app.models.language import Language
    from app.models.user import User
    from app.models.translation import Translation


class Item(Base, TimestampMixin, SoftDeleteMixin):
    """Learning item (vocabulary word or phrase)"""

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    language_id: Mapped[int] = mapped_column(
        ForeignKey("languages.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Language this item is in",
    )
    term: Mapped[str] = mapped_column(nullable=False)
    difficulty: Mapped[int | None] = mapped_column(nullable=True, comment="1–7 scale")
    context: Mapped[str | None] = mapped_column(nullable=True)
    image_url: Mapped[str | None] = mapped_column(nullable=True)
    audio_url: Mapped[str | None] = mapped_column(nullable=True)
    part_of_speech: Mapped[PartOfSpeech | None] = mapped_column(nullable=True)
    lemma: Mapped[str | None] = mapped_column(nullable=True, comment="Base word form")
    creator_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    verified_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[ContentStatus] = mapped_column(
        default=ContentStatus.DRAFT, nullable=False
    )

    language: Mapped["Language"] = relationship(foreign_keys=[language_id])
    creator: Mapped["User"] = relationship(
        foreign_keys=[creator_id],
        primaryjoin="Item.creator_id == User.id",
    )
    verifier: Mapped["User"] = relationship(
        foreign_keys=[verified_by],
        primaryjoin="Item.verified_by == User.id",
    )
    translations: Mapped[list["Translation"]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("difficulty BETWEEN 1 AND 7", name="chk_item_difficulty"),
        Index("idx_items_lookup", "language_id", "term"),
        Index(
            "idx_items_unverified",
            "created_at",
            postgresql_where=text(
                "deleted_at IS NULL AND verified_by IS NULL"
                " AND status = 'pending_review'"
            ),
        ),
        Index(
            "idx_items_by_creator",
            "creator_id",
            "status",
            "created_at",
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    def __repr__(self) -> str:
        return f"<Item {self.id}: {self.term}>"


__all__ = ["Item"]
