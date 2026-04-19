# backend/app/models/item_synonym.py
"""ItemSynonym model"""

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import ENUM as pgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, SoftDeleteTimestampMixin
from app.models.enums import ContentStatus

if TYPE_CHECKING:
    from app.models.item import Item
    from app.models.user import User


class ItemSynonym(Base, SoftDeleteTimestampMixin):
    """Relationship between synonym items"""

    __tablename__ = "item_synonyms"

    item_a_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), primary_key=True
    )
    item_b_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), primary_key=True
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
    item_a: Mapped["Item"] = relationship(
        foreign_keys=[item_a_id],
        primaryjoin="ItemSynonym.item_a_id == Item.id",
    )
    item_b: Mapped["Item"] = relationship(
        foreign_keys=[item_b_id],
        primaryjoin="ItemSynonym.item_b_id == Item.id",
    )
    creator: Mapped["User | None"] = relationship(
        foreign_keys=[creator_id],
        primaryjoin="ItemSynonym.creator_id == User.id",
    )
    verifier: Mapped["User | None"] = relationship(
        foreign_keys=[verified_by],
        primaryjoin="ItemSynonym.verified_by == User.id",
    )

    __table_args__ = (
        CheckConstraint("item_a_id < item_b_id", name="chk_synonym_order"),
        Index(
            "idx_item_synonyms_status",
            "status",
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("idx_item_synonyms_item_b_id", "item_b_id"),
    )

    def __repr__(self) -> str:
        return f"<ItemSynonym {self.item_a_id} <-> {self.item_b_id}>"


__all__ = ["ItemSynonym"]
