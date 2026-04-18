# backend/app/models/enums.py
"""Domain enums for LingvoPal"""

from enum import Enum


class ContentStatus(str, Enum):
    """Status of user-generated content in the review workflow"""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    OFFICIAL = "official"


class PartOfSpeech(str, Enum):
    """Grammatical part of speech classification"""

    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"
    PRONOUN = "pronoun"
    PREPOSITION = "preposition"
    CONJUNCTION = "conjunction"
    INTERJECTION = "interjection"
    ARTICLE = "article"
    OTHER = "other"


class ModerationTargetType(str, Enum):
    """Type of content being moderated (polymorphic moderation table)"""

    ITEM = "item"
    TRANSLATION = "translation"
    SET = "set"
    MIXED = "mixed"


class ModerationStatus(str, Enum):
    """Resolution state of a moderation entry"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class UserRole(str, Enum):
    """User roles for access control"""

    USER = "user"
    ADMIN = "admin"


class LearningIntensity(str, Enum):
    """How aggressively new material is introduced"""

    LIGHT = "light"
    BALANCED = "balanced"
    INTENSIVE = "intensive"


class EvaluationMode(str, Enum):
    """How strictly typed answers are judged"""

    STRICT = "strict"
    NORMAL = "normal"
    FORGIVING = "forgiving"


class RetentionPriority(str, Enum):
    """Trade-off between learning speed and long-term retention"""

    SPEED_LEARNING = "speed_learning"
    BALANCED = "balanced"
    LONG_TERM_MASTERY = "long_term_mastery"


class SessionStatus(str, Enum):
    """Lifecycle state of a study session"""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


__all__ = [
    "ContentStatus",
    "PartOfSpeech",
    "ModerationTargetType",
    "ModerationStatus",
    "UserRole",
    "LearningIntensity",
    "EvaluationMode",
    "RetentionPriority",
    "SessionStatus",
]
