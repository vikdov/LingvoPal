# backend/app/models/set_item.py
"""SetItem association model"""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.set import Set
    from app.models.item import Item


class SetItem(Base):
    """Association between Set and Item"""

    __tablename__ = "set_items"

    set_id: Mapped[int] = mapped_column(
        ForeignKey("sets.id", ondelete="CASCADE"), primary_key=True
    )
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), primary_key=True
    )
    sort_order: Mapped[int] = mapped_column(default=0, nullable=False)

    set: Mapped["Set"] = relationship(back_populates="set_items")
    item: Mapped["Item"] = relationship()

    __table_args__ = (
        Index("idx_set_items_by_set", "set_id", "sort_order"),
        Index("idx_set_items_by_item", "item_id"),
    )

    def __repr__(self) -> str:
        return f"<SetItem set={self.set_id} item={self.item_id}>"


__all__ = ["SetItem"]
