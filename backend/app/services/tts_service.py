# backend/app/services/tts_service.py
"""
Text-to-Speech using Google Cloud TTS or ElevenLabs.

Caching: S3 is used as a permanent cache. Key is sha256(language_code:term)[:16].
Same term + language → same key → HEAD check before any API call.
Calling generate_audio 100x for "wanderlust/en-US" costs exactly one TTS API call.
"""

import asyncio
import hashlib
import json
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _tts_cache_key(term: str, language_code: str) -> str:
    """Deterministic S3 key for TTS audio. Normalizes term so casing/whitespace don't matter."""
    normalized = f"{language_code}:{term.strip().lower()}"
    digest = hashlib.sha256(normalized.encode()).hexdigest()[:16]
    return f"tts/{language_code}/{digest}.mp3"


class TTSService:
    """Generate audio pronunciation for terms. S3-cached: each unique (term, lang) costs one API call ever."""

    def __init__(self):
        from app.services.storage import StorageService

        settings = get_settings()
        self.provider = settings.TTS_PROVIDER
        self.api_key = settings.TTS_API_KEY
        self.google_client = None
        self._storage = StorageService()

        if self.provider == "google_cloud":
            try:
                from google.cloud import texttospeech

                self.google_client = texttospeech.TextToSpeechClient(
                    credentials=self._get_google_credentials()
                )
            except Exception as e:
                logger.error(f"Failed to initialize Google TTS: {e}")

    async def generate_audio(
        self,
        term: str,
        language_code: str = "en-US",
    ) -> str | None:
        """
        Return audio URL for term. Checks S3 cache before calling TTS API.

        Args:
            term: Vocabulary term
            language_code: BCP-47 code (e.g., "en-US", "es-ES")

        Returns:
            URL to audio file (S3), or None if generation fails
        """
        if not term or not term.strip():
            return None

        cache_key = _tts_cache_key(term, language_code)

        # Cache hit: object already in S3, no API call needed
        cached_url = await self._storage.get_url_if_exists(cache_key)
        if cached_url:
            logger.debug(f"TTS cache hit: '{term}' ({language_code})")
            return cached_url

        # Cache miss: generate audio bytes
        audio_bytes: bytes | None = None
        try:
            if self.provider == "google_cloud" and self.google_client:
                audio_bytes = await self._google_tts_bytes(term, language_code)
            elif self.provider == "elevenlabs":
                audio_bytes = await self._elevenlabs_tts_bytes(term)
            else:
                logger.warning(f"TTS provider '{self.provider}' not initialized")
                return None
        except Exception as e:
            logger.error(f"TTS failed for '{term}': {e}")
            return None

        if not audio_bytes:
            return None

        return await self._storage.upload_at_key(audio_bytes, cache_key, "audio/mpeg")

    async def _google_tts_bytes(self, term: str, language_code: str) -> bytes | None:
        """Generate raw MP3 bytes via Google Cloud TTS."""
        try:
            from google.cloud import texttospeech

            synthesis_input = texttospeech.SynthesisInput(text=term)
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
            )

            response = await asyncio.to_thread(
                self.google_client.synthesize_speech,
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config,
            )
            return response.audio_content

        except Exception as e:
            logger.error(f"Google TTS bytes failed for '{term}': {e}")
            return None

    async def _elevenlabs_tts_bytes(self, term: str) -> bytes | None:
        """Generate raw MP3 bytes via ElevenLabs."""
        try:
            from elevenlabs import generate

            audio = await asyncio.to_thread(generate, text=term, voice="Rachel")
            return audio

        except Exception as e:
            logger.error(f"ElevenLabs TTS failed for '{term}': {e}")
            return None

    @staticmethod
    def _get_google_credentials():
        """Load Google Cloud service account credentials from the path in settings."""
        from google.oauth2 import service_account

        settings = get_settings()
        path = settings.GOOGLE_APPLICATION_CREDENTIALS
        # validate_tts_credentials() guarantees this is set — this is a safety net
        if not path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not configured.")

        try:
            with open(path) as f:
                credentials_dict = json.load(f)
            return service_account.Credentials.from_service_account_info(
                credentials_dict,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
        except FileNotFoundError:
            raise ValueError(
                f"GOOGLE_APPLICATION_CREDENTIALS file not found: {path!r}\n"
                "Set the path to your service account JSON file."
            )
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Invalid service account JSON at {path!r}: {e}") from e

    async def close(self):
        """Close TTS client."""
        if self.google_client:
            try:
                self.google_client.close()
            except Exception:  # nosec B110
                pass


__all__ = ["TTSService"]
