# backend/app/models/enums.py
"""Domain enums for LingvoPal"""

from enum import Enum


class ContentStatus(str, Enum):
    """Status of user-generated content in the review workflow"""

    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    OFFICIAL = "OFFICIAL"


class PartOfSpeech(str, Enum):
    """Grammatical part of speech classification"""

    NOUN = "NOUN"
    VERB = "VERB"
    ADJECTIVE = "ADJECTIVE"
    ADVERB = "ADVERB"
    PRONOUN = "PRONOUN"
    PREPOSITION = "PREPOSITION"
    CONJUNCTION = "CONJUNCTION"
    INTERJECTION = "INTERJECTION"
    ARTICLE = "ARTICLE"
    OTHER = "OTHER"


class ModerationTargetType(str, Enum):
    """Type of content being moderated (polymorphic moderation table)"""

    ITEM = "ITEM"
    TRANSLATION = "TRANSLATION"
    SET = "SET"
    MIXED = "MIXED"


__all__ = [
    "ContentStatus",
    "PartOfSpeech",
    "ModerationTargetType",
]
