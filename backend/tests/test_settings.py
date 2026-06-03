# backend/tests/test_settings.py
"""
Unit tests for Settings validators.

Covers production constraint validation and AI provider/model pairing.
No DB, no async — pure Pydantic model instantiation.
"""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def _base_kwargs(**overrides) -> dict:
    """Minimal valid settings for testing validators."""
    defaults = {
        "ENV": "development",
        "DATABASE_USER": "u",
        "DATABASE_PASSWORD": "p",
        "DATABASE_HOST": "localhost",
        "DATABASE_NAME": "db",
        "SECRET_KEY": "a" * 32,
        "S3_ACCESS_KEY": "key",
        "S3_SECRET_KEY": "secret",
        "AI_API_KEY": "ai-key",
        "IMAGE_SEARCH_API_KEY": "img-key",
        # TTS disabled to skip credential checks in unit tests
        "TTS_ENABLED": False,
    }
    defaults.update(overrides)
    return defaults


# ── validate_production_constraints ──────────────────────────────────────────


class TestProductionConstraints:
    def _prod(self, **overrides) -> dict:
        base = _base_kwargs(
            ENV="production",
            SECRET_KEY="abcdefghijklmnopqrstuvwxyz012345",  # 32 chars, 10+ unique
            CORS_ORIGINS=["https://lingvopal.com"],
            DEBUG=False,
            S3_USE_TLS=True,
        )
        base.update(overrides)
        return base

    def test_valid_production_passes(self) -> None:
        Settings(**self._prod())

    def test_debug_true_rejected_in_production(self) -> None:
        with pytest.raises(ValidationError, match="DEBUG must be False"):
            Settings(**self._prod(DEBUG=True))

    def test_wildcard_cors_rejected_in_production(self) -> None:
        with pytest.raises(ValidationError, match="Wildcard CORS"):
            Settings(**self._prod(CORS_ORIGINS=["*"]))

    def test_localhost_cors_rejected_in_production(self) -> None:
        with pytest.raises(ValidationError, match="Localhost origin"):
            Settings(**self._prod(CORS_ORIGINS=["http://localhost:5173"]))

    def test_low_entropy_secret_key_rejected_in_production(self) -> None:
        # Only 3 unique chars — way below the 10-char minimum
        with pytest.raises(ValidationError, match="entropy"):
            Settings(**self._prod(SECRET_KEY="aaaaaabbbbbbccccccddddddeeeeeeee"))

    def test_s3_tls_required_in_production(self) -> None:
        with pytest.raises(ValidationError, match="S3_USE_TLS"):
            Settings(**self._prod(S3_USE_TLS=False))

    def test_production_constraints_not_applied_in_development(self) -> None:
        # All constraints that would fail in production should pass in development
        Settings(
            **_base_kwargs(
                ENV="development",
                DEBUG=True,
                CORS_ORIGINS=["http://localhost:5173"],
                S3_USE_TLS=False,
                SECRET_KEY="a" * 32,
            )
        )


# ── validate_ai_model_provider_pairing ───────────────────────────────────────


class TestAiModelProviderPairing:
    def test_groq_model_with_groq_provider_passes(self) -> None:
        Settings(**_base_kwargs(AI_PROVIDER="groq", AI_MODEL="llama-3.3-70b-versatile"))

    def test_google_model_with_google_provider_passes(self) -> None:
        Settings(**_base_kwargs(AI_PROVIDER="google", AI_MODEL="gemini-2.0-flash-lite"))

    def test_google_model_with_groq_provider_raises(self) -> None:
        with pytest.raises(ValidationError, match="Google model"):
            Settings(**_base_kwargs(AI_PROVIDER="groq", AI_MODEL="gemini-2.0-flash-lite"))

    def test_groq_model_with_google_provider_raises(self) -> None:
        with pytest.raises(ValidationError, match="Groq model"):
            Settings(**_base_kwargs(AI_PROVIDER="google", AI_MODEL="llama-3.3-70b-versatile"))

    def test_unknown_model_passes_both_providers(self) -> None:
        # Unknown model is allowed — new models not in the known set should not be blocked
        Settings(**_base_kwargs(AI_PROVIDER="groq", AI_MODEL="some-future-model"))
        Settings(**_base_kwargs(AI_PROVIDER="google", AI_MODEL="some-future-model"))


# ── SECRET_KEY minimum length ─────────────────────────────────────────────────


class TestSecretKeyValidation:
    def test_32_char_key_accepted(self) -> None:
        Settings(**_base_kwargs(SECRET_KEY="a" * 32))

    def test_short_key_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Settings(**_base_kwargs(SECRET_KEY="tooshort"))


# ── S3_ENDPOINT_URL computed field ───────────────────────────────────────────


class TestS3EndpointUrl:
    def test_http_when_tls_disabled(self) -> None:
        s = Settings(**_base_kwargs(S3_HOST="minio", S3_PORT=9000, S3_USE_TLS=False))
        assert s.S3_ENDPOINT_URL == "http://minio:9000"

    def test_https_when_tls_enabled(self) -> None:
        s = Settings(**_base_kwargs(S3_HOST="storage.example.com", S3_PORT=443, S3_USE_TLS=True))
        assert s.S3_ENDPOINT_URL == "https://storage.example.com"
