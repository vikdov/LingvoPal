# backend/app/models/__init__.py
"""Domain models for LingvoPal"""

from app.models.content_audit_log import ContentAuditLog
from app.models.content_complaint import ContentComplaint
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
from app.models.item import Item
from app.models.item_quality_metrics import ItemQualityMetrics
from app.models.item_synonym_term import ItemSynonymTerm
from app.models.language import Language
from app.models.pending_moderation import PendingModeration
from app.models.pending_session import PendingSession
from app.models.set import Set
from app.models.set_item import SetItem
from app.models.study_review import StudyReview
from app.models.study_session import StudySession
from app.models.translation import Translation
from app.models.user import User, UserSettings
from app.models.user_daily_stats import UserDailyStats
from app.models.user_language import UserLanguage
from app.models.user_progress import UserProgress
from app.models.user_set_library import UserSetLibrary
from app.models.user_stats_total import UserStatsTotal

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
    "UserLanguage",
    # Content
    "Item",
    "Translation",
    "Set",
    "SetItem",
    "ItemSynonymTerm",
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
    "ItemQualityMetrics",
    "ContentComplaint",
    # Safety valve
    "PendingSession",
]
