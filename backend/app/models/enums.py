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


__all__ = [
    "ContentStatus",
    "PartOfSpeech",
    "ModerationTargetType",
]
