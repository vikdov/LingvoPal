# backend/app/models/content_audit_log.py
"""ContentAuditLog model"""

from typing import Any, TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, CreatedAtMixin

if TYPE_CHECKING:
    from app.models.user import User


class ContentAuditLog(Base, CreatedAtMixin):
    """Comprehensive audit trail of all content changes"""

    __tablename__ = "content_audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    table_name: Mapped[str] = mapped_column(nullable=False)
    record_id: Mapped[int] = mapped_column(nullable=False)
    action: Mapped[str] = mapped_column(
        nullable=False, comment="INSERT | UPDATE | DELETE"
    )
    old_values: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    new_values: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    user: Mapped["User"] = relationship()

    __table_args__ = (Index("idx_content_audit_log_target", "table_name", "record_id"),)

    def __repr__(self) -> str:
        return f"<ContentAuditLog {self.action} {self.table_name}:{self.record_id}>"


__all__ = ["ContentAuditLog"]
