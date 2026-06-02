# backend/tests/test_redis_token_services.py
"""
Unit tests for Redis-backed token services.

Uses AsyncMock to avoid a live Redis connection.
Tests cover:
  - EmailChangeService: generate / consume / cancel
  - EmailVerificationService: generate / consume / check_and_increment_daily
  - RefreshTokenService: generate / verify / rotate / revoke

All tests are async, executed via anyio (no pytest-asyncio needed).
"""

from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import (
    EmailChangeTokenInvalidError,
    PasswordResetTokenInvalidError,
    RefreshTokenInvalidError,
    VerificationRateLimitedError,
    VerificationTokenInvalidError,
)
from app.services.email_change_service import EmailChangeService
from app.services.email_verification_service import DAILY_CAP, EmailVerificationService
from app.services.password_reset_service import PasswordResetService
from app.services.refresh_token_service import RefreshTokenService

# ── Helpers ───────────────────────────────────────────────────────────────────


def _redis() -> AsyncMock:
    """Return a fresh AsyncMock mimicking redis.asyncio.Redis."""
    r = AsyncMock()
    r.eval = AsyncMock(return_value=1)
    r.getdel = AsyncMock(return_value=None)
    r.get = AsyncMock(return_value=None)
    r.delete = AsyncMock(return_value=1)
    r.incr = AsyncMock(return_value=1)
    r.expire = AsyncMock(return_value=1)
    return r


# ── EmailChangeService ────────────────────────────────────────────────────────


class TestEmailChangeService:
    @pytest.mark.anyio
    async def test_generate_token_returns_urlsafe_string(self) -> None:
        svc = EmailChangeService(_redis())
        token = await svc.generate_token(42, "new@example.com")
        assert isinstance(token, str)
        assert len(token) > 10
        # URL-safe base64 chars only
        allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
        assert all(c in allowed for c in token)

    @pytest.mark.anyio
    async def test_generate_token_calls_eval_with_correct_keys(self) -> None:
        r = _redis()
        svc = EmailChangeService(r)
        token = await svc.generate_token(7, "new@example.com")

        r.eval.assert_called_once()
        args = r.eval.call_args[0]
        assert args[2] == "email_change_user:7"       # KEYS[1]
        assert args[3] == f"email_change:{token}"     # KEYS[2]

    @pytest.mark.anyio
    async def test_generate_token_each_call_produces_unique_token(self) -> None:
        svc = EmailChangeService(_redis())
        t1 = await svc.generate_token(1, "a@x.com")
        t2 = await svc.generate_token(1, "a@x.com")
        assert t1 != t2

    @pytest.mark.anyio
    async def test_consume_token_returns_user_id_and_email(self) -> None:
        r = _redis()
        r.getdel.return_value = b"99|changed@example.com"
        svc = EmailChangeService(r)
        user_id, email = await svc.consume_token("some-token")
        assert user_id == 99
        assert email == "changed@example.com"

    @pytest.mark.anyio
    async def test_consume_token_accepts_str_value(self) -> None:
        r = _redis()
        r.getdel.return_value = "5|str@example.com"
        svc = EmailChangeService(r)
        user_id, email = await svc.consume_token("tok")
        assert user_id == 5
        assert email == "str@example.com"

    @pytest.mark.anyio
    async def test_consume_token_handles_pipe_in_email(self) -> None:
        r = _redis()
        # Email itself does not contain pipe — but split("|", 1) ensures robustness
        r.getdel.return_value = b"3|user+tag@host.com"
        svc = EmailChangeService(r)
        user_id, email = await svc.consume_token("tok")
        assert user_id == 3
        assert email == "user+tag@host.com"

    @pytest.mark.anyio
    async def test_consume_token_raises_on_missing_token(self) -> None:
        r = _redis()
        r.getdel.return_value = None
        svc = EmailChangeService(r)
        with pytest.raises(EmailChangeTokenInvalidError):
            await svc.consume_token("nonexistent")

    @pytest.mark.anyio
    async def test_consume_token_deletes_user_key_after_consume(self) -> None:
        r = _redis()
        r.getdel.return_value = b"10|x@y.com"
        svc = EmailChangeService(r)
        await svc.consume_token("tok")
        r.delete.assert_called_once_with("email_change_user:10")

    @pytest.mark.anyio
    async def test_cancel_token_deletes_both_keys(self) -> None:
        r = _redis()
        r.getdel.return_value = b"abc123"
        svc = EmailChangeService(r)
        await svc.cancel_token(55)
        r.getdel.assert_called_once_with("email_change_user:55")
        r.delete.assert_called_once_with("email_change:abc123")

    @pytest.mark.anyio
    async def test_cancel_token_noop_when_no_pending(self) -> None:
        r = _redis()
        r.getdel.return_value = None
        svc = EmailChangeService(r)
        await svc.cancel_token(55)
        r.delete.assert_not_called()


# ── EmailVerificationService ──────────────────────────────────────────────────


class TestEmailVerificationService:
    @pytest.mark.anyio
    async def test_generate_token_returns_string(self) -> None:
        svc = EmailVerificationService(_redis())
        token = await svc.generate_token(1)
        assert isinstance(token, str) and len(token) > 10

    @pytest.mark.anyio
    async def test_generate_token_calls_eval_with_user_key(self) -> None:
        r = _redis()
        svc = EmailVerificationService(r)
        token = await svc.generate_token(3)
        args = r.eval.call_args[0]
        assert args[2] == "email_verify_user:3"
        assert args[3] == f"email_verify:{token}"

    @pytest.mark.anyio
    async def test_consume_token_returns_user_id(self) -> None:
        r = _redis()
        r.getdel.return_value = b"77"
        svc = EmailVerificationService(r)
        result = await svc.consume_token("valid-token")
        assert result == 77

    @pytest.mark.anyio
    async def test_consume_token_raises_on_missing(self) -> None:
        r = _redis()
        r.getdel.return_value = None
        svc = EmailVerificationService(r)
        with pytest.raises(VerificationTokenInvalidError):
            await svc.consume_token("bad-token")

    @pytest.mark.anyio
    async def test_consume_token_cleans_up_user_key(self) -> None:
        r = _redis()
        r.getdel.return_value = b"8"
        svc = EmailVerificationService(r)
        await svc.consume_token("tok")
        r.delete.assert_called_once_with("email_verify_user:8")

    @pytest.mark.anyio
    async def test_daily_first_send_sets_expire(self) -> None:
        r = _redis()
        r.incr.return_value = 1  # first send of the day
        svc = EmailVerificationService(r)
        await svc.check_and_increment_daily(1)
        r.expire.assert_called_once()  # TTL must be set

    @pytest.mark.anyio
    async def test_daily_second_send_skips_expire(self) -> None:
        r = _redis()
        r.incr.return_value = 2  # already sent once today
        svc = EmailVerificationService(r)
        await svc.check_and_increment_daily(1)
        r.expire.assert_not_called()

    @pytest.mark.anyio
    async def test_daily_at_cap_does_not_raise(self) -> None:
        r = _redis()
        r.incr.return_value = DAILY_CAP  # exactly at cap — still allowed
        svc = EmailVerificationService(r)
        await svc.check_and_increment_daily(1)  # must not raise

    @pytest.mark.anyio
    async def test_daily_over_cap_raises(self) -> None:
        r = _redis()
        r.incr.return_value = DAILY_CAP + 1
        svc = EmailVerificationService(r)
        with pytest.raises(VerificationRateLimitedError):
            await svc.check_and_increment_daily(1)

    @pytest.mark.anyio
    async def test_daily_key_includes_today(self) -> None:
        from datetime import datetime, timezone
        r = _redis()
        r.incr.return_value = 1
        svc = EmailVerificationService(r)
        await svc.check_and_increment_daily(99)
        key_used = r.incr.call_args[0][0]
        today = datetime.now(timezone.utc).date().isoformat()
        assert key_used == f"email_verify_daily:99:{today}"


# ── RefreshTokenService ───────────────────────────────────────────────────────


class TestRefreshTokenService:
    @pytest.mark.anyio
    async def test_generate_returns_urlsafe_string(self) -> None:
        svc = RefreshTokenService(_redis(), ttl_seconds=3600)
        token = await svc.generate(1)
        assert isinstance(token, str) and len(token) > 10

    @pytest.mark.anyio
    async def test_generate_calls_eval_with_user_and_token_keys(self) -> None:
        r = _redis()
        svc = RefreshTokenService(r, ttl_seconds=3600)
        token = await svc.generate(42)
        args = r.eval.call_args[0]
        assert args[2] == "rtoken_user:42"
        assert args[3] == f"rtoken:{token}"

    @pytest.mark.anyio
    async def test_verify_returns_user_id(self) -> None:
        r = _redis()
        r.get.return_value = b"15"
        svc = RefreshTokenService(r, ttl_seconds=3600)
        user_id = await svc.verify("valid-token")
        assert user_id == 15

    @pytest.mark.anyio
    async def test_verify_raises_on_missing_token(self) -> None:
        r = _redis()
        r.get.return_value = None
        svc = RefreshTokenService(r, ttl_seconds=3600)
        with pytest.raises(RefreshTokenInvalidError):
            await svc.verify("bad-token")

    @pytest.mark.anyio
    async def test_verify_does_not_consume_token(self) -> None:
        r = _redis()
        r.get.return_value = b"5"
        svc = RefreshTokenService(r, ttl_seconds=3600)
        await svc.verify("tok")
        r.delete.assert_not_called()
        r.getdel.assert_not_called()

    @pytest.mark.anyio
    async def test_rotate_returns_new_token(self) -> None:
        svc = RefreshTokenService(_redis(), ttl_seconds=3600)
        t1 = await svc.generate(1)
        t2 = await svc.rotate(1)
        assert isinstance(t2, str)
        assert t1 != t2

    @pytest.mark.anyio
    async def test_revoke_deletes_token_key(self) -> None:
        r = _redis()
        r.getdel.return_value = b"mytoken"
        svc = RefreshTokenService(r, ttl_seconds=3600)
        await svc.revoke(20)
        r.getdel.assert_called_once_with("rtoken_user:20")
        r.delete.assert_called_once_with("rtoken:mytoken")

    @pytest.mark.anyio
    async def test_revoke_noop_when_no_token(self) -> None:
        r = _redis()
        r.getdel.return_value = None
        svc = RefreshTokenService(r, ttl_seconds=3600)
        await svc.revoke(20)
        r.delete.assert_not_called()

    @pytest.mark.anyio
    async def test_revoke_handles_str_token(self) -> None:
        r = _redis()
        r.getdel.return_value = "strtoken"
        svc = RefreshTokenService(r, ttl_seconds=3600)
        await svc.revoke(3)
        r.delete.assert_called_once_with("rtoken:strtoken")


# ── PasswordResetService ──────────────────────────────────────────────────────


class TestPasswordResetService:
    @pytest.mark.anyio
    async def test_generate_token_returns_urlsafe_string(self) -> None:
        svc = PasswordResetService(_redis())
        token = await svc.generate_token(1)
        assert isinstance(token, str)
        assert len(token) > 10
        allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
        assert all(c in allowed for c in token)

    @pytest.mark.anyio
    async def test_generate_token_calls_eval_with_correct_keys(self) -> None:
        r = _redis()
        svc = PasswordResetService(r)
        token = await svc.generate_token(42)
        r.eval.assert_called_once()
        args = r.eval.call_args[0]
        assert args[2] == "password_reset_user:42"
        assert args[3] == f"password_reset:{token}"

    @pytest.mark.anyio
    async def test_generate_token_passes_ttl_and_user_id(self) -> None:
        r = _redis()
        svc = PasswordResetService(r)
        token = await svc.generate_token(7)
        args = r.eval.call_args[0]
        assert args[4] == 3600          # TOKEN_TTL
        assert args[5] == "7"           # user_id as string
        assert args[6] == token         # token stored under user key

    @pytest.mark.anyio
    async def test_generate_token_each_call_produces_unique_token(self) -> None:
        svc = PasswordResetService(_redis())
        t1 = await svc.generate_token(1)
        t2 = await svc.generate_token(1)
        assert t1 != t2

    @pytest.mark.anyio
    async def test_consume_token_returns_user_id(self) -> None:
        r = _redis()
        r.getdel.return_value = b"99"
        svc = PasswordResetService(r)
        user_id = await svc.consume_token("valid-token")
        assert user_id == 99

    @pytest.mark.anyio
    async def test_consume_token_accepts_str_value(self) -> None:
        r = _redis()
        r.getdel.return_value = "5"
        svc = PasswordResetService(r)
        user_id = await svc.consume_token("tok")
        assert user_id == 5

    @pytest.mark.anyio
    async def test_consume_token_raises_on_missing(self) -> None:
        r = _redis()
        r.getdel.return_value = None
        svc = PasswordResetService(r)
        with pytest.raises(PasswordResetTokenInvalidError):
            await svc.consume_token("nonexistent")

    @pytest.mark.anyio
    async def test_consume_token_deletes_user_key(self) -> None:
        r = _redis()
        r.getdel.return_value = b"10"
        svc = PasswordResetService(r)
        await svc.consume_token("tok")
        r.delete.assert_called_once_with("password_reset_user:10")

    @pytest.mark.anyio
    async def test_consume_token_uses_correct_redis_key(self) -> None:
        r = _redis()
        r.getdel.return_value = b"1"
        svc = PasswordResetService(r)
        await svc.consume_token("my-reset-token")
        r.getdel.assert_called_once_with("password_reset:my-reset-token")

    @pytest.mark.anyio
    async def test_consume_token_single_use(self) -> None:
        """Second consume on same token must raise (getdel returns None after first)."""
        r = _redis()
        r.getdel.side_effect = [b"3", None]
        svc = PasswordResetService(r)
        await svc.consume_token("tok")
        with pytest.raises(PasswordResetTokenInvalidError):
            await svc.consume_token("tok")
