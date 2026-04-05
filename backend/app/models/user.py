# backend/app/models/user.py
"""User management models"""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, SoftDeleteTimestampMixin

if TYPE_CHECKING:
    from app.models.language import Language


class User(Base, SoftDeleteTimestampMixin):
    """User account"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    is_admin: Mapped[bool] = mapped_column(
        default=False, nullable=False, comment="User is administrator"
    )
    email: Mapped[str] = mapped_column(
        unique=True, nullable=False, comment="User email (unique, used for login)"
    )
    email_verified: Mapped[bool] = mapped_column(
        default=False, nullable=False, comment="User has verified their email"
    )
    password_hash: Mapped[str] = mapped_column(
        nullable=False, comment="Hashed password (never plain text)"
    )
    username: Mapped[str | None] = mapped_column(
        unique=True,
        nullable=True,
        comment="Display name (optional, unique if provided)",
    )

    # Relationships
    settings: Mapped["UserSettings"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User {self.id}: {self.email}>"

    def __str__(self) -> str:
        return self.username or self.email


class UserSettings(Base):
    """User preferences and configuration"""

    __tablename__ = "user_settings"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        comment="User this settings belongs to",
    )
    native_lang_id: Mapped[int] = mapped_column(
        ForeignKey("languages.id", ondelete="RESTRICT"),
        nullable=False,
        comment="User's native language",
    )
    interface_lang_id: Mapped[int] = mapped_column(
        ForeignKey("languages.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Language for app interface",
    )

    # Relationships
    user: Mapped[User] = relationship(back_populates="settings", foreign_keys=[user_id])
    native_language: Mapped["Language"] = relationship(foreign_keys=[native_lang_id])
    interface_language: Mapped["Language"] = relationship(
        foreign_keys=[interface_lang_id]
    )

    def __repr__(self) -> str:
        return f"<UserSettings user_id={self.user_id}>"


__all__ = ["User", "UserSettings"]
