# backend/app/services/item_suggestion_service.py
"""
Orchestrate parallel item enrichment: lemma + AI + TTS + images.
"""

import asyncio
import logging
from typing import TypedDict

from app.core.config import get_settings
from app.services.ai_enrichment_service import AIEnrichment, AIEnrichmentService
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
    image_query: str | None

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
        context: str | None = None,
    ) -> ItemSuggestion:
        """
        Generate complete item suggestions.

        Pipeline:
        1. Lemma (spaCy for English; LLM for all other languages)
        2. AI enrichment, TTS, images (all parallel, 20s timeout)

        Args:
            term: Vocabulary term
            source_language: Language name (e.g., "Spanish")
            source_language_code: ISO 639-1 or BCP-47 code (e.g., "es", "en-US")
            target_language: Optional for translations

        Returns:
            Complete suggestion ready to save as item
        """
        warnings = []

        # Step 1: Extract lemma (spaCy for English, LLM fallback for other languages — run in thread)
        try:
            lemma = await asyncio.to_thread(
                self.lemmatizer.extract_lemma, term, source_language, source_language_code
            )
        except Exception as e:
            logger.warning(f"Lemmatization failed for '{term}': {e}")
            warnings.append("lemmatization_failed")
            lemma = None

        # Step 2: AI enrichment + TTS in parallel
        try:
            phase1 = await asyncio.wait_for(
                asyncio.gather(
                    self.ai.enrich(term, source_language, target_language, context),
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
                image_query=None,
                warnings=["pipeline_timeout"],
            )

        # Unpack phase 1
        ai_result: AIEnrichment
        tts_url: str | None
        image_suggestions: list[ImageSuggestion]

        if isinstance(phase1[0], Exception):
            logger.warning("AI enrichment failed", extra={"error": type(phase1[0]).__name__})
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
            logger.warning("TTS generation failed", extra={"error": type(phase1[1]).__name__})
            warnings.append("tts_generation_failed")
            tts_url = None
        else:
            tts_url = phase1[1]

        # Step 3: Image search + context TTS in parallel
        ai_context = ai_result.get("context")
        context_for_audio = context or ai_context

        # AI generates a focused image_query that includes term + context-specific domain words.
        # Fall back to term + first synonym if AI didn't return one.
        synonyms = ai_result.get("synonyms", [])
        ai_image_query = ai_result.get("image_query")
        if ai_image_query:
            image_query = ai_image_query
        elif synonyms:
            image_query = f"{term} {synonyms[0]}"
        else:
            image_query = term

        async def _context_tts() -> str | None:
            if not context_for_audio:
                return None
            return await self.tts.generate_audio(context_for_audio, source_language_code)

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
            logger.warning("Image search failed", extra={"error": type(phase2_results[0]).__name__})
            warnings.append("image_search_failed")
            image_suggestions = []
        else:
            image_suggestions = phase2_results[0]

        if isinstance(phase2_results[1], Exception):
            logger.warning("Context TTS failed", extra={"error": type(phase2_results[1]).__name__})
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
            image_query=image_query,
            warnings=warnings,
        )

    async def search_images(self, query: str, count: int = 4) -> list[ImageSuggestion]:
        return await self.images.search_images(query, count=count)

    async def generate_audio(
        self,
        term: str,
        language_code: str,
        context: str | None = None,
    ) -> dict[str, str | None]:
        """Generate TTS for term and optional context sentence."""
        tasks = [self.tts.generate_audio(term, language_code)]
        if context:
            tasks.append(self.tts.generate_audio(context, language_code))

        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=15.0,
            )
        except asyncio.TimeoutError:
            return {"audio_url": None, "context_audio_url": None}

        audio_url = results[0] if not isinstance(results[0], Exception) else None
        context_audio_url = (
            results[1] if len(results) > 1 and not isinstance(results[1], Exception) else None
        )
        return {"audio_url": audio_url, "context_audio_url": context_audio_url}

    async def close(self):
        """Cleanup resources."""
        await self.ai.close()
        await self.tts.close()
        await self.images.close()


__all__ = ["ItemSuggestionService", "ItemSuggestion"]
