# backend/app/models/translation.py
"""Translation model"""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import ENUM as pgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, SoftDeleteTimestampMixin
from app.models.enums import ContentStatus

if TYPE_CHECKING:
    from app.models.item import Item
    from app.models.language import Language
    from app.models.user import User


class Translation(Base, SoftDeleteTimestampMixin):
    """Translation of an item into another language"""

    __tablename__ = "translations"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), nullable=False
    )
    language_id: Mapped[int] = mapped_column(
        ForeignKey("languages.id", ondelete="RESTRICT"), nullable=False
    )
    term_trans: Mapped[str] = mapped_column(nullable=False)
    context_trans: Mapped[str | None] = mapped_column(nullable=True)
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
    item: Mapped["Item"] = relationship(back_populates="translations")
    language: Mapped["Language"] = relationship(foreign_keys=[language_id])
    creator: Mapped["User"] = relationship(
        foreign_keys=[creator_id],
        primaryjoin="Translation.creator_id == User.id",
    )
    verifier: Mapped["User"] = relationship(
        foreign_keys=[verified_by],
        primaryjoin="Translation.verified_by == User.id",
    )

    __table_args__ = (
        Index(
            "uq_translation_active",
            "item_id",
            "language_id",
            unique=True,  # ← Makes it unique
            postgresql_where=text("deleted_at IS NULL"),  # ← Now valid
        ),
        Index(
            "idx_translations_item",
            "item_id",
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "idx_translations_item_status",
            "item_id",
            "status",
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "idx_translations_creator_status",
            "creator_id",
            "status",
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "idx_translations_status_lang",
            "status",
            "language_id",
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "idx_translations_unverified",
            "created_at",
            postgresql_where=text(
                "deleted_at IS NULL AND verified_by IS NULL"
                " AND status = 'pending_review'"
            ),
        ),
    )

    def __repr__(self) -> str:
        return f"<Translation {self.id}: {self.term_trans}>"


__all__ = ["Translation"]
