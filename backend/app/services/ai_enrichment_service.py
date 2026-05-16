# backend/app/services/ai_enrichment_service.py
"""
AI linguistic enrichment (LEMMA-FREE).

Lemmatization is handled by LemmatizationService separately.
This service only provides: POS, CEFR, context, translations, synonyms.

Providers: "groq" (default, free tier) | "google" (Gemini, requires billing)
Switch via AI_PROVIDER env var.
"""

import json
import logging
import re
from typing import TypedDict

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class AIEnrichment(TypedDict):
    """AI-generated enrichment (lemma excluded, handled separately)."""

    part_of_speech: str | None
    cefr_level: str | None
    context: str | None  # Single example sentence (becomes item.context)
    translations: list[dict[str, str]]  # [{text, language}]
    synonyms: list[str]


class AIEnrichmentService:
    """Enrich vocabulary items (NOT lemmatization)."""

    def __init__(self):
        settings = get_settings()
        self.provider = settings.AI_PROVIDER
        self.model = settings.AI_MODEL
        self.api_key = settings.AI_API_KEY
        self._http = httpx.AsyncClient(timeout=30.0)

        if self.provider == "google":
            from google import genai

            self._google_client = genai.Client(api_key=self.api_key)

    async def close(self) -> None:
        await self._http.aclose()

    async def enrich(
        self,
        term: str,
        source_language: str,
        target_language: str | None = None,
    ) -> AIEnrichment:
        """
        Enrich term with linguistic metadata.

        ⚠️ DOES NOT handle lemmatization (use LemmatizationService).

        Args:
            term: Vocabulary term
            source_language: Language name
            target_language: Optional for translations

        Returns:
            AIEnrichment (all None if LLM fails)
        """
        prompt = self._build_prompt(term, source_language, target_language)

        try:
            if self.provider == "groq":
                return await self._enrich_groq(term, prompt)
            else:
                return await self._enrich_google(term, prompt)
        except Exception as e:
            logger.error(f"LLM enrichment failed for '{term}': {e}")
            return self._empty_enrichment()

    async def _enrich_groq(self, term: str, prompt: str) -> AIEnrichment:
        response = await self._http.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 300,
            },
        )
        response.raise_for_status()
        text = response.json()["choices"][0]["message"]["content"]

        if not text:
            logger.warning(f"Empty LLM response for '{term}'")
            return self._empty_enrichment()
        return self._parse_response(text, term)

    async def _enrich_google(self, term: str, prompt: str) -> AIEnrichment:
        from google.genai import types as genai_types

        response = await self._google_client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=300,
            ),
        )

        if not response.text:
            logger.warning(f"Empty LLM response for '{term}'")
            return self._empty_enrichment()
        return self._parse_response(response.text, term)

    def _parse_response(self, text: str, term: str) -> AIEnrichment:
        text = text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
        try:
            result = json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"LLM JSON decode failed for '{term}': {e}")
            return self._empty_enrichment()

        return AIEnrichment(
            part_of_speech=result.get("part_of_speech"),
            cefr_level=result.get("cefr_level"),
            context=result.get("context"),
            translations=result.get("translations", []),
            synonyms=result.get("synonyms", []),
        )

    def _build_prompt(
        self,
        term: str,
        source_language: str,
        target_language: str | None,
    ) -> str:
        target_note = ""
        if target_language:
            target_note = f"\nTarget Language: {target_language}"

        return f"""You are a language teacher. Provide metadata for this vocabulary item.

Term: {term}
Source Language: {source_language}{target_note}

Return ONLY this JSON (no extra text):
{{
  "part_of_speech": "noun|verb|adjective|adverb|preposition|conjunction|phrase|idiom|phrasal_verb|collocation",
  "cefr_level": "A1|A2|B1|B2|C1|C2",
  "context": "One clear example sentence using '{term}' for a learner",
  "translations": [
    {{"text": "translated_term", "language": "{target_language or "N/A"}"}}
  ],
  "synonyms": ["synonym1", "synonym2", "synonym3"]
}}

Rules:
- Return ONLY valid JSON
- "context": exactly ONE sentence, natural, clear
- Use null for unknown fields
- "synonyms": 2-3 related terms
- "translations": include language field
"""

    @staticmethod
    def _empty_enrichment() -> AIEnrichment:
        return AIEnrichment(
            part_of_speech=None,
            cefr_level=None,
            context=None,
            translations=[],
            synonyms=[],
        )


__all__ = ["AIEnrichmentService", "AIEnrichment"]
