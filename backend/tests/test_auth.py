# backend/tests/test_auth.py
"""
Unit tests for auth pure functions.

No DB, no async, no HTTP — pure functions only.

Test groups:
  - validate_password_strength(): all rule branches
  - hash_password() / verify_password(): round-trip + wrong password
  - encode_token() / decode_token(): happy path, expired, invalid, missing exp
  - _parse_accept_language(): standard, multi-lang, edge cases
  - _DUMMY_HASH: timing-safety proof (never matches a real password)
"""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.core.security import (
    TokenExpiredError,
    TokenInvalidError,
    decode_token,
    encode_token,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.services.auth_service import _DUMMY_HASH, _parse_accept_language


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def patch_settings(monkeypatch):
    """Replace get_settings() in security.py with a minimal stub."""
    stub = SimpleNamespace(SECRET_KEY="test-secret-key", ALGORITHM="HS256")
    monkeypatch.setattr("app.core.security.get_settings", lambda: stub)
    return stub


def _future_payload(extra: dict | None = None) -> dict:
    payload = {
        "sub": "42",
        "role": "user",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    if extra:
        payload.update(extra)
    return payload


# ── validate_password_strength ────────────────────────────────────────────────


class TestValidatePasswordStrength:
    def test_valid_password_returns_no_errors(self) -> None:
        assert validate_password_strength("Secure1!") == []

    def test_too_short(self) -> None:
        errors = validate_password_strength("Ab1!")
        assert any("8 characters" in e for e in errors)

    def test_missing_uppercase(self) -> None:
        errors = validate_password_strength("secure1!")
        assert any("uppercase" in e for e in errors)

    def test_missing_lowercase(self) -> None:
        errors = validate_password_strength("SECURE1!")
        assert any("lowercase" in e for e in errors)

    def test_missing_digit(self) -> None:
        errors = validate_password_strength("Securee!")
        assert any("digit" in e for e in errors)

    def test_missing_special_char(self) -> None:
        errors = validate_password_strength("Secure12")
        assert any("special" in e for e in errors)

    def test_exceeds_72_bytes(self) -> None:
        long_password = "Aa1!" + "x" * 70
        errors = validate_password_strength(long_password)
        assert any("72 bytes" in e for e in errors)

    def test_multiple_violations_reported(self) -> None:
        errors = validate_password_strength("short")
        assert len(errors) >= 2


# ── hash_password / verify_password ──────────────────────────────────────────


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self) -> None:
        assert hash_password("Secure1!") != "Secure1!"

    def test_correct_password_verifies(self) -> None:
        hashed = hash_password("Secure1!")
        assert verify_password("Secure1!", hashed) is True

    def test_wrong_password_does_not_verify(self) -> None:
        hashed = hash_password("Secure1!")
        assert verify_password("Wrong1!!", hashed) is False

    def test_same_password_produces_different_hashes(self) -> None:
        # bcrypt uses random salt per call
        assert hash_password("Secure1!") != hash_password("Secure1!")


# ── encode_token / decode_token ───────────────────────────────────────────────


class TestJWT:
    def test_round_trip(self, patch_settings) -> None:
        payload = _future_payload()
        token = encode_token(payload)
        decoded = decode_token(token)
        assert decoded["sub"] == "42"
        assert decoded["role"] == "user"

    def test_missing_exp_raises_value_error(self, patch_settings) -> None:
        with pytest.raises(ValueError, match="exp"):
            encode_token({"sub": "1"})

    def test_expired_token_raises_token_expired_error(self, patch_settings) -> None:
        payload = {
            "sub": "1",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        }
        token = encode_token(payload)
        with pytest.raises(TokenExpiredError):
            decode_token(token)

    def test_tampered_token_raises_token_invalid_error(self, patch_settings) -> None:
        token = encode_token(_future_payload())
        tampered = token[:-4] + "xxxx"
        with pytest.raises(TokenInvalidError):
            decode_token(tampered)

    def test_garbage_string_raises_token_invalid_error(self, patch_settings) -> None:
        with pytest.raises(TokenInvalidError):
            decode_token("not.a.token")


# ── _parse_accept_language ────────────────────────────────────────────────────


class TestParseAcceptLanguage:
    def test_simple_code(self) -> None:
        assert _parse_accept_language("en") == "en"

    def test_region_stripped(self) -> None:
        assert _parse_accept_language("en-US") == "en"

    def test_multi_lang_picks_first(self) -> None:
        assert _parse_accept_language("de-DE,de;q=0.9,en;q=0.8") == "de"

    def test_none_header_returns_none(self) -> None:
        assert _parse_accept_language(None) is None

    def test_empty_string_returns_none(self) -> None:
        assert _parse_accept_language("") is None

    def test_numeric_code_rejected(self) -> None:
        assert _parse_accept_language("123") is None

    def test_lowercases_result(self) -> None:
        assert _parse_accept_language("FR-FR") == "fr"


# ── _DUMMY_HASH timing-safety ─────────────────────────────────────────────────


class TestDummyHash:
    def test_dummy_hash_never_matches_any_password(self) -> None:
        # The dummy hash exists to burn bcrypt time when a user is not found.
        # It must never accidentally verify as a real password.
        assert verify_password("dummy", _DUMMY_HASH) is False
        assert verify_password("", _DUMMY_HASH) is False
        assert verify_password("Secure1!", _DUMMY_HASH) is False
