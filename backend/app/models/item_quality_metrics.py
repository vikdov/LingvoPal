# backend/app/models/item_quality_metrics.py
"""ItemQualityMetrics model — pre-computed pedagogical quality signals per item."""

from datetime import datetime

from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.item import Item


class ItemQualityMetrics(Base):
    """
    Pre-computed aggregate of SM-2 learning outcomes per item across all learners.
    Upserted after each study session finalization. Not a full audit table.
    """

    __tablename__ = "item_quality_metrics"

    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), primary_key=True
    )
    learner_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_ease_factor: Mapped[float] = mapped_column(Float, nullable=False, default=2.5)
    global_success_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_interval: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )

    item: Mapped["Item"] = relationship(back_populates="quality_metrics")

    def __repr__(self) -> str:
        return (
            f"<ItemQualityMetrics item={self.item_id} "
            f"learners={self.learner_count} success={self.global_success_rate:.2f}>"
        )


__all__ = ["ItemQualityMetrics"]
