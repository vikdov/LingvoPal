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
    translations: list[dict[str, str]]  # [{text, context_trans, language}]
    synonyms: list[str]
    image_query: str | None  # Optimized 2-4 word image search query


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
        context: str | None = None,
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
        prompt = self._build_prompt(term, source_language, target_language, context)

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
            image_query=result.get("image_query"),
        )

    def _build_prompt(
        self,
        term: str,
        source_language: str,
        target_language: str | None,
        context: str | None = None,
    ) -> str:
        target_note = ""
        if target_language:
            target_note = f"\nTarget Language: {target_language}"

        if context:
            context_block = f'\nUser\'s context hint: "{context}" — use this as inspiration or improve it into a full sentence'
            context_rule = '- "context": one natural sentence inspired by the user\'s hint above'
        else:
            context_block = ""
            context_rule = '- "context": exactly ONE sentence, natural, clear'
        context_field = (
            f'\n  "context": "One clear example sentence using \'{term}\' for a learner",'
        )

        return f"""You are a language teacher. Provide metadata for this vocabulary item.

Term: {term}
Source Language: {source_language}{target_note}{context_block}

Return ONLY this JSON (no extra text):
{{{context_field}
  "part_of_speech": "noun|verb|adjective|adverb|preposition|conjunction|phrase|idiom|phrasal_verb|collocation",
  "cefr_level": "A1|A2|B1|B2|C1|C2",
  "translations": [
    {{
      "text": "translated_term",
      "context_trans": "translation of the context sentence with {{translated_term}} wrapped in curly braces",
      "language": "{target_language or "N/A"}"
    }}
  ],
  "synonyms": ["synonym1", "synonym2", "synonym3"],
  "image_query": "2-4 word image search query that visually represents this term in this specific context"
}}

Rules:
- Return ONLY valid JSON
- Use null for unknown fields
- "synonyms": 2-3 related terms, context-appropriate if context provided
- "translations": include language field; "context_trans" must translate the "context" sentence above into the target language, with the translated form of "{term}" wrapped in single curly braces like {{word}}
- {context_rule}
- "image_query": be specific to context (e.g. "chip manufacturing semiconductor", not just "manufacturing"); term should appear first
"""

    @staticmethod
    def _empty_enrichment() -> AIEnrichment:
        return AIEnrichment(
            part_of_speech=None,
            cefr_level=None,
            context=None,
            translations=[],
            synonyms=[],
            image_query=None,
        )


__all__ = ["AIEnrichmentService", "AIEnrichment"]
