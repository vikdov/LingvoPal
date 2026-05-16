# backend/app/services/item_suggestion_service.py
"""
Orchestrate parallel item enrichment: lemma + AI + TTS + images.
"""

import asyncio
import logging
from typing import TypedDict

from app.core.config import get_settings
from app.services.ai_enrichment_service import AIEnrichmentService, AIEnrichment
from app.services.image_search_service import ImageSearchService, ImageSuggestion
from app.services.lemmatization_service import get_lemmatization_service
from app.services.tts_service import TTSService

logger = logging.getLogger(__name__)

_PIPELINE_TIMEOUT = 20.0


class ItemSuggestion(TypedDict):
    """Complete auto-filled item suggestion (ready to save)."""

    # System use (hidden from user)
    lemma: str | None

    # Shown during practice
    part_of_speech: str | None
    cefr_level: str | None
    context: str | None  # Becomes item.context

    # Collections
    translations: list[dict[str, str]]  # [{text, language}]
    synonyms: list[str]

    # Media
    tts_audio_url: str | None
    context_tts_audio_url: str | None
    image_suggestions: list[ImageSuggestion]

    # Diagnostics
    warnings: list[str]


class ItemSuggestionService:
    """Orchestrate parallel suggestion generation."""

    def __init__(self):
        settings = get_settings()
        self.image_count = settings.IMAGE_COUNT
        self.lemmatizer = get_lemmatization_service()
        self.ai = AIEnrichmentService()
        self.tts = TTSService()
        self.images = ImageSearchService()

    async def suggest_complete(
        self,
        term: str,
        source_language: str,
        source_language_code: str,
        target_language: str | None = None,
    ) -> ItemSuggestion:
        """
        Generate complete item suggestions.

        Pipeline:
        1. Lemma (spaCy instant + LLM fallback if needed)
        2. AI enrichment, TTS, images (all parallel, 20s timeout)

        Args:
            term: Vocabulary term
            source_language: Language name (e.g., "English")
            source_language_code: BCP-47 code (e.g., "en-US")
            target_language: Optional for translations

        Returns:
            Complete suggestion ready to save as item
        """
        warnings = []

        # Step 1: Extract lemma (spaCy offline, LLM fallback via sync HTTP — run in thread)
        lemma = await asyncio.to_thread(
            self.lemmatizer.extract_lemma, term, source_language, source_language_code
        )

        # Step 2: AI enrichment + TTS in parallel
        try:
            phase1 = await asyncio.wait_for(
                asyncio.gather(
                    self.ai.enrich(term, source_language, target_language),
                    self.tts.generate_audio(term, source_language_code),
                    return_exceptions=True,
                ),
                timeout=_PIPELINE_TIMEOUT,
            )
        except asyncio.TimeoutError:
            logger.warning(f"Suggestion pipeline timed out for '{term}'")
            return ItemSuggestion(
                lemma=lemma,
                part_of_speech=None,
                cefr_level=None,
                context=None,
                translations=[],
                synonyms=[],
                tts_audio_url=None,
                context_tts_audio_url=None,
                image_suggestions=[],
                warnings=["pipeline_timeout"],
            )

        # Unpack phase 1
        ai_result: AIEnrichment
        tts_url: str | None
        image_suggestions: list[ImageSuggestion]

        if isinstance(phase1[0], Exception):
            logger.warning(f"AI enrichment failed: {phase1[0]}")
            warnings.append("ai_enrichment_failed")
            ai_result = {
                "part_of_speech": None,
                "cefr_level": None,
                "context": None,
                "translations": [],
                "synonyms": [],
            }
        else:
            ai_result = phase1[0]

        if isinstance(phase1[1], Exception):
            logger.warning(f"TTS generation failed: {phase1[1]}")
            warnings.append("tts_generation_failed")
            tts_url = None
        else:
            tts_url = phase1[1]

        # Step 3: Image search + context TTS in parallel (context available now from AI)
        image_query = ai_result.get("context") or term
        context_sentence = ai_result.get("context")

        async def _context_tts() -> str | None:
            if not context_sentence:
                return None
            return await self.tts.generate_audio(context_sentence, source_language_code)

        try:
            phase2_results = await asyncio.wait_for(
                asyncio.gather(
                    self.images.search_images(image_query, count=self.image_count),
                    _context_tts(),
                    return_exceptions=True,
                ),
                timeout=10.0,
            )
        except asyncio.TimeoutError:
            logger.warning(f"Image/context-TTS phase timed out for '{term}'")
            phase2_results = [[], None]

        if isinstance(phase2_results[0], Exception):
            logger.warning(f"Image search failed: {phase2_results[0]}")
            warnings.append("image_search_failed")
            image_suggestions = []
        else:
            image_suggestions = phase2_results[0]

        if isinstance(phase2_results[1], Exception):
            logger.warning(f"Context TTS failed: {phase2_results[1]}")
            warnings.append("context_tts_generation_failed")
            context_tts_url = None
        else:
            context_tts_url = phase2_results[1]

        # Step 4: Combine and return
        return ItemSuggestion(
            lemma=lemma,
            part_of_speech=ai_result.get("part_of_speech"),
            cefr_level=ai_result.get("cefr_level"),
            context=ai_result.get("context"),
            translations=ai_result.get("translations", []),
            synonyms=ai_result.get("synonyms", []),
            tts_audio_url=tts_url,
            context_tts_audio_url=context_tts_url,
            image_suggestions=image_suggestions,
            warnings=warnings,
        )

    async def close(self):
        """Cleanup resources."""
        await self.ai.close()
        await self.tts.close()
        await self.images.close()


__all__ = ["ItemSuggestionService", "ItemSuggestion"]
