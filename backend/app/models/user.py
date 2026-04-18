# backend/app/models/user.py
"""User management models"""

from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Enum as pgEnum

from app.database import Base, SoftDeleteTimestampMixin, TimestampMixin
from app.models.enums import (
    EvaluationMode,
    LearningIntensity,
    RetentionPriority,
    UserRole,
)

if TYPE_CHECKING:
    from app.models.language import Language


class User(Base, SoftDeleteTimestampMixin):
    """User account"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_status: Mapped[UserRole] = mapped_column(
        pgEnum(UserRole, name="user_role", create_type=False, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=UserRole.USER,
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

    @property
    def is_admin(self) -> bool:
        return self.user_status == UserRole.ADMIN

    def __repr__(self) -> str:
        return f"<User {self.id}: {self.email}>"

    def __str__(self) -> str:
        return self.username or self.email


class UserSettings(Base, TimestampMixin):
    """User preferences and configuration (1:1 with User)"""

    __tablename__ = "user_settings"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        comment="User this settings belongs to",
    )

    # ── Language settings ────────────────────────────────────────────────────

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

    # ── Learning behaviour ───────────────────────────────────────────────────

    learning_intensity: Mapped[LearningIntensity] = mapped_column(
        pgEnum(LearningIntensity, name="learning_intensity", create_type=False, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        comment="Pace at which new material is introduced",
    )
    evaluation_mode: Mapped[EvaluationMode] = mapped_column(
        pgEnum(EvaluationMode, name="evaluation_mode", create_type=False, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        comment="How strictly typed answers are graded",
    )
    show_hints_on_fails: Mapped[bool] = mapped_column(
        nullable=False,
        comment="Show a hint after a wrong answer",
    )

    # ── Scheduling ───────────────────────────────────────────────────────────

    daily_study_goal: Mapped[int] = mapped_column(
        nullable=False,
        comment="Target number of items to study per day",
    )
    reminder_time: Mapped[time | None] = mapped_column(
        Time(timezone=False),
        nullable=True,
        comment="Local time of day for study reminder (NULL = disabled)",
    )
    streak_reminders_enabled: Mapped[bool] = mapped_column(
        nullable=False,
        comment="Send reminders to maintain study streak",
    )

    # ── UI preferences ───────────────────────────────────────────────────────

    show_translations: Mapped[bool] = mapped_column(nullable=False)
    show_images: Mapped[bool] = mapped_column(nullable=False)
    show_synonyms: Mapped[bool] = mapped_column(nullable=False)
    show_part_of_speech: Mapped[bool] = mapped_column(nullable=False)
    auto_play_audio: Mapped[bool] = mapped_column(nullable=False)

    # ── Advanced settings ────────────────────────────────────────────────────

    new_items_per_day_limit: Mapped[int] = mapped_column(
        nullable=False,
        comment="Hard cap on new vocabulary introduced per day",
    )
    new_items_per_session: Mapped[int] = mapped_column(
        nullable=False,
        comment="Max new items introduced in a single practice session",
    )
    retention_priority: Mapped[RetentionPriority] = mapped_column(
        pgEnum(RetentionPriority, name="retention_priority", create_type=False, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        comment="Speed vs. long-term mastery trade-off",
    )
    max_review_load_per_day: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="Cap on total reviews per day (NULL = unlimited)",
    )

    # ── Relationships ────────────────────────────────────────────────────────

    user: Mapped[User] = relationship(back_populates="settings", foreign_keys=[user_id])
    native_language: Mapped["Language"] = relationship(foreign_keys=[native_lang_id])
    interface_language: Mapped["Language"] = relationship(
        foreign_keys=[interface_lang_id]
    )

    def __repr__(self) -> str:
        return f"<UserSettings user_id={self.user_id}>"


__all__ = ["User", "UserSettings"]
