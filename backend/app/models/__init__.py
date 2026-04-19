# backend/app/models/__init__.py
"""Domain models for LingvoPal"""

from app.models.enums import (
    ContentStatus,
    EvaluationMode,
    LearningIntensity,
    ModerationStatus,
    ModerationTargetType,
    PartOfSpeech,
    RetentionPriority,
    SessionStatus,
    UserRole,
)
from app.models.language import Language
from app.models.user import User, UserSettings
from app.models.item import Item
from app.models.translation import Translation
from app.models.set import Set
from app.models.set_item import SetItem
from app.models.item_synonym import ItemSynonym
from app.models.user_set_library import UserSetLibrary
from app.models.study_session import StudySession
from app.models.study_review import StudyReview
from app.models.user_progress import UserProgress
from app.models.user_daily_stats import UserDailyStats
from app.models.user_stats_total import UserStatsTotal
from app.models.pending_moderation import PendingModeration
from app.models.pending_session import PendingSession
from app.models.content_audit_log import ContentAuditLog

__all__ = [
    # Enums
    "ContentStatus",
    "EvaluationMode",
    "LearningIntensity",
    "ModerationStatus",
    "ModerationTargetType",
    "PartOfSpeech",
    "RetentionPriority",
    "SessionStatus",
    "UserRole",
    # Reference
    "Language",
    # User
    "User",
    "UserSettings",
    # Content
    "Item",
    "Translation",
    "Set",
    "SetItem",
    "ItemSynonym",
    "UserSetLibrary",
    # Learning
    "StudySession",
    "StudyReview",
    "UserProgress",
    # Stats
    "UserDailyStats",
    "UserStatsTotal",
    # Moderation
    "PendingModeration",
    "ContentAuditLog",
    # Safety valve
    "PendingSession",
]
