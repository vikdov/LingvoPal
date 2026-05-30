# backend/app/models/item_synonym_term.py
"""ItemSynonymTerm model — plain string synonyms per item."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.item import Item
    from app.models.language import Language


class ItemSynonymTerm(Base):
    """A synonym word string for a learning item."""

    __tablename__ = "item_synonym_terms"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    language_id: Mapped[int] = mapped_column(
        ForeignKey("languages.id", ondelete="CASCADE"),
        nullable=False,
        comment="Denormalized from item for efficient autocomplete queries",
    )
    term: Mapped[str] = mapped_column(nullable=False)

    item: Mapped["Item"] = relationship(foreign_keys=[item_id])
    language: Mapped["Language"] = relationship(foreign_keys=[language_id])

    __table_args__ = (
        UniqueConstraint("item_id", "term", name="uq_item_synonym_term"),
        Index("idx_item_synonym_terms_lang", "language_id", "term"),
    )

    def __repr__(self) -> str:
        return f"<ItemSynonymTerm item={self.item_id} term={self.term!r}>"


__all__ = ["ItemSynonymTerm"]
