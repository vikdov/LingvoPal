# backend/app/services/lemmatization_service.py
"""
Intelligent lemmatization: spaCy primary (English), LLM fallback for all other languages.

Only en_core_web_sm is required. For any language without an installed spaCy model,
lemmatization goes directly to the LLM — no blank-model fallback, no spaCy download needed.
"""

import logging
from functools import lru_cache

import spacy
from spacy.language import Language

logger = logging.getLogger(__name__)


class LemmatizationService:
    """spaCy-first lemmatizer (English); LLM fallback for all other languages."""

    def __init__(self):
        self._ai_service = None

    @staticmethod
    @lru_cache(maxsize=10)
    def _load_model(language: str) -> Language | None:
        """Load spaCy model by 2-char language code. Returns None if not installed."""
        model_name = f"{language}_core_web_sm"
        try:
            return spacy.load(model_name)
        except OSError:
            logger.debug(f"No spaCy model for '{language}' — LLM will handle lemmatization.")
            return None

    def extract_lemma(
        self,
        term: str,
        source_language: str | None = None,
        source_language_code: str = "en-US",
    ) -> str:
        """
        Extract lemma. spaCy used when a model is installed; LLM otherwise.

        Args:
            term: Word or phrase
            source_language: Language name (for LLM prompt)
            source_language_code: BCP-47 code used to select spaCy model

        Returns:
            Lemmatized form, or original term if all methods fail
        """
        if not term or not term.strip():
            return term

        lang = source_language_code.split("-")[0].lower()
        nlp = self._load_model(lang)

        if nlp is None:
            # No spaCy model installed for this language — go straight to LLM.
            llm_lemma = self._get_llm_lemma(term, source_language)
            return llm_lemma if llm_lemma else term

        spacy_lemma = self._extract_with_spacy(term, nlp)

        if self._should_verify_with_llm(term, spacy_lemma):
            logger.debug(
                f"spaCy uncertain for '{term}': '{spacy_lemma}'. Requesting LLM verification."
            )
            llm_lemma = self._get_llm_lemma(term, source_language)
            if llm_lemma and llm_lemma != term:
                return llm_lemma

        return spacy_lemma if spacy_lemma else term

    def _extract_with_spacy(self, term: str, nlp: Language) -> str:
        """Extract lemma using spaCy (fast, offline)."""
        try:
            doc = nlp(term.strip().lower())

            if len(doc) == 0:
                return term
            if len(doc) == 1:
                return doc[0].lemma_

            return " ".join(token.lemma_ for token in doc)

        except Exception as e:
            logger.warning(f"spaCy failed for '{term}': {e}")
            return term

    def _should_verify_with_llm(self, original: str, spacy_result: str) -> bool:
        """Decide if spaCy result needs LLM verification."""
        if " " in original.strip():
            return True
        if "-PRON-" in spacy_result:
            return True
        return False

    def _get_llm_lemma(self, term: str, source_language: str | None = None) -> str | None:
        """Get lemma from LLM via sync HTTP (only called for ~5% of items)."""
        from app.core.config import get_settings

        if self._ai_service is None:
            from app.services.ai_enrichment_service import AIEnrichmentService

            self._ai_service = AIEnrichmentService()

        settings = get_settings()
        prompt = (
            f"Extract the base/dictionary form of this {source_language or 'English'} term.\n"
            f"Term: {term}\n"
            "Return ONLY the base form, nothing else. No JSON, no explanation.\n"
            "Examples: 'running' → run | 'went' → go | 'take into account' → take into account"
        )

        try:
            if settings.AI_PROVIDER == "groq":
                import httpx

                resp = httpx.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.AI_API_KEY}"},
                    json={
                        "model": settings.AI_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                        "max_tokens": 20,
                    },
                    timeout=10.0,
                )
                resp.raise_for_status()
                text = resp.json()["choices"][0]["message"]["content"]
                return text.strip().lower() if text else None

            elif settings.AI_PROVIDER == "google":
                from google import genai

                client = genai.Client(api_key=settings.AI_API_KEY)
                resp = client.models.generate_content(
                    model=settings.AI_MODEL,
                    contents=prompt,
                )
                return resp.text.strip().lower() if resp.text else None

        except Exception as e:
            logger.warning(f"LLM lemma failed for '{term}': {e}")
        return None


_lemmatizer: LemmatizationService | None = None


def get_lemmatization_service() -> LemmatizationService:
    """Get lemmatizer singleton."""
    global _lemmatizer
    if _lemmatizer is None:
        _lemmatizer = LemmatizationService()
    return _lemmatizer


__all__ = ["LemmatizationService", "get_lemmatization_service"]
