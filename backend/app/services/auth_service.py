# backend/app/services/auth_service.py
"""
Auth service — domain-level authentication logic.

Responsibilities:
  - Orchestrates UserRepository for all DB access
  - Owns JWT payload structure (what claims go in the token)
  - Delegates crypto to core/security.py
  - Raises typed domain exceptions (never HTTP errors)
  - Controls transaction boundaries (commit / rollback)
"""

from datetime import datetime, timedelta, timezone

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    AccountDisabledError,
    AlreadyVerifiedError,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    RefreshTokenInvalidError,
    SamePasswordError,
    UsernameAlreadyExistsError,
    VerificationTokenInvalidError,
)
from app.core.security import encode_token, hash_password, verify_password
from app.models.language import Language
from app.models.user import User, UserSettings
from app.repositories.user_language_repo import UserLanguageRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import (
    LoginRequest,
    PasswordChangeRequest,
    RefreshResponse,
    SignupRequest,
    TokenResponse,
)
from app.schemas.user import UserPrivateResponse
from app.services.refresh_token_service import RefreshTokenService
from app.services.user_settings_service import UserSettingsService

# Precomputed bcrypt hash for a known dummy password ("dummy").
# Used to ensure constant-time verification when user is not found.
# Prevents timing attacks that could enumerate valid emails.
_DUMMY_HASH = "$2b$12$GHlj3GDmGBhNSBqBVG4N4uK5kHm9VJR3HqE8BgJj1zTdUnkjJOXkG"

_LOGIN_FAIL_PREFIX = "login_fails:"
_MAX_LOGIN_FAILS = 10
_LOCKOUT_TTL_SECONDS = 900  # 15 minutes

# Atomically increment a fail counter, set TTL on first increment, return new count.
# Prevents a race where two concurrent INCR calls both get count=1 and each try to
# set the TTL, or where the TTL is never set if the key already exists.
_LUA_INCR_WITH_EXPIRE = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
    redis.call('EXPIRE', KEYS[1], tonumber(ARGV[1]))
end
return count
"""


# ============================================================================
# PRIVATE HELPERS  (module-level pure functions, easy to unit-test)
# ============================================================================


def _parse_accept_language(header: str | None) -> str | None:
    """Extract primary language code from Accept-Language header.

    'en-US,en;q=0.9,de;q=0.8' → 'en'
    Returns None if header is absent or unparseable.
    """
    if not header:
        return None
    primary = header.split(",")[0].split(";")[0].strip()
    code = primary.split("-")[0].lower()
    return code if code.isalpha() else None


def _build_token(user: User) -> tuple[str, int]:
    """
    Decide what goes into the JWT payload, then delegate signing to security.py.

    Owning payload structure here means:
      - Adding a new claim = one-line change in one place
      - security.py never needs to know about User or roles
    """
    settings = get_settings()
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    now = datetime.now(timezone.utc)
    exp = now + timedelta(seconds=expires_in)

    payload = {
        "sub": str(user.id),
        "role": user.user_status.value,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    token = encode_token(payload)
    return token, expires_in


async def _build_token_response(
    user: User,
    settings: UserSettings,
    active_target_lang_id: int | None,
    refresh_svc: RefreshTokenService,
) -> TokenResponse:
    token, expires_in = _build_token(user)
    refresh_token = await refresh_svc.generate(user.id)
    return TokenResponse(
        access_token=token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        user=UserPrivateResponse(
            id=user.id,
            created_at=user.created_at,
            username=user.username,
            email=user.email,
            email_verified=user.email_verified,
            is_admin=user.is_admin,
            native_lang_id=settings.native_lang_id,
            active_target_lang_id=active_target_lang_id,
        ),
    )


# ============================================================================
# AUTH SERVICE
# ============================================================================


class AuthService:
    """
    Stateless per-request service.
    Instantiated with a session; repositories are constructed internally.
    """

    def __init__(self, session: AsyncSession, refresh_svc: RefreshTokenService, redis: aioredis.Redis) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._user_settings = UserSettingsService(session)
        self._user_languages = UserLanguageRepository(session)
        self._refresh = refresh_svc
        self._redis = redis

    async def get_user_by_email(self, email: str) -> "User | None":
        return await self._users.get_by_email(email)

    async def signup(
        self, data: SignupRequest, accept_language: str | None = None
    ) -> TokenResponse:
        """
        Register a new account and return an access token immediately.
        Raises: EmailAlreadyExistsError, UsernameAlreadyExistsError

        interface_lang_id is auto-detected from the Accept-Language header;
        falls back to native_lang_id if the code isn't in our language table.
        """
        if await self._users.email_exists(data.email):
            raise EmailAlreadyExistsError()

        if data.username and await self._users.username_exists(data.username):
            raise UsernameAlreadyExistsError()

        interface_lang_id = await self._resolve_interface_language(
            accept_language, fallback=data.native_lang_id
        )

        try:
            user = await self._users.create(
                email=data.email,
                password_hash=hash_password(data.password),
                username=data.username,
            )
        except IntegrityError:
            await self._session.rollback()
            raise EmailAlreadyExistsError()

        settings = await self._user_settings.create_for_user(
            user_id=user.id,
            native_lang_id=data.native_lang_id,
            interface_lang_id=interface_lang_id,
        )

        await self._session.commit()
        await self._session.refresh(user)

        active_lang_id = await self._user_languages.get_active_lang_id(user.id)
        return await _build_token_response(user, settings, active_lang_id, self._refresh)

    async def _resolve_interface_language(
        self, accept_language: str | None, fallback: int
    ) -> int:
        code = _parse_accept_language(accept_language)
        if code:
            result = await self._session.execute(
                select(Language).where(Language.code == code)
            )
            lang = result.scalar_one_or_none()
            if lang:
                return lang.id
        return fallback

    async def _check_login_lockout(self, email: str, client_ip: str | None) -> None:
        keys = [f"{_LOGIN_FAIL_PREFIX}{email}"]
        if client_ip:
            keys.append(f"login_fails_ip:{client_ip}")
        for key in keys:
            count = await self._redis.get(key)
            if count and int(count) >= _MAX_LOGIN_FAILS:
                raise AccountDisabledError(
                    f"Account temporarily locked after {_MAX_LOGIN_FAILS} failed attempts. "
                    f"Try again in {_LOCKOUT_TTL_SECONDS // 60} minutes."
                )

    async def _record_login_fail(self, email: str, client_ip: str | None) -> None:
        keys = [f"{_LOGIN_FAIL_PREFIX}{email}"]
        if client_ip:
            keys.append(f"login_fails_ip:{client_ip}")
        for key in keys:
            await self._redis.eval(_LUA_INCR_WITH_EXPIRE, 1, key, _LOCKOUT_TTL_SECONDS)

    async def _clear_login_fails(self, email: str, client_ip: str | None) -> None:
        keys = [f"{_LOGIN_FAIL_PREFIX}{email}"]
        if client_ip:
            keys.append(f"login_fails_ip:{client_ip}")
        await self._redis.delete(*keys)

    async def login(self, data: LoginRequest, client_ip: str | None = None) -> TokenResponse:
        """
        Validate credentials and return an access token.
        Raises: InvalidCredentialsError, AccountDisabledError (temporary lockout)

        Timing-safe: bcrypt runs even when the user doesn't exist,
        preventing enumeration via response-time differences.
        Lockout: 10 consecutive failures lock the account for 15 minutes.
        Keyed on both email and client IP to prevent victim-targeted DoS lockout.
        """
        await self._check_login_lockout(data.email, client_ip)

        user = await self._users.get_by_email(data.email)
        candidate_hash = user.password_hash if user else _DUMMY_HASH

        if not verify_password(data.password, candidate_hash) or not user:
            if user:
                await self._record_login_fail(data.email, client_ip)
            raise InvalidCredentialsError()

        await self._clear_login_fails(data.email, client_ip)
        settings = await self._user_settings.get_or_create(user.id)
        active_lang_id = await self._user_languages.get_active_lang_id(user.id)
        return await _build_token_response(user, settings, active_lang_id, self._refresh)

    async def change_password(
        self,
        user_id: int,
        data: PasswordChangeRequest,
    ) -> None:
        """
        Verify current password, then store the new hash.
        Raises: InvalidCredentialsError, SamePasswordError
        """
        user = await self._users.get_by_id(user_id)

        if not user or not verify_password(data.current_password, user.password_hash):
            raise InvalidCredentialsError()

        # Service-layer check (schema already caught raw-string equality)
        if verify_password(data.new_password, user.password_hash):
            raise SamePasswordError()

        await self._users.update_password(user_id, hash_password(data.new_password))
        await self._session.commit()

    async def reset_password(self, user_id: int, new_password: str) -> None:
        """
        Set a new password for a user whose reset token was already consumed.
        Raises VerificationTokenInvalidError if user not found (stale token).
        """
        user = await self._users.get_by_id(user_id)
        if not user:
            raise VerificationTokenInvalidError()
        await self._users.update_password(user_id, hash_password(new_password))
        await self._session.commit()

    async def refresh(self, token: str) -> RefreshResponse:
        """
        Validate refresh token, rotate it, return new access + refresh tokens.
        Raises RefreshTokenInvalidError if token is missing, expired, or revoked.
        """
        user_id = await self._refresh.verify(token)
        user = await self._users.get_by_id(user_id)
        if not user:
            await self._refresh.revoke(user_id)
            raise RefreshTokenInvalidError()

        access_token, expires_in = _build_token(user)
        new_refresh = await self._refresh.rotate(user_id)
        return RefreshResponse(
            access_token=access_token,
            refresh_token=new_refresh,
            expires_in=expires_in,
        )

    async def revoke_refresh_token(self, user_id: int) -> None:
        """Revoke refresh token on logout."""
        await self._refresh.revoke(user_id)

    async def mark_email_verified(self, user_id: int) -> None:
        """
        Mark user's email as verified.
        Raises VerificationTokenInvalidError if user not found (stale token).
        Raises AlreadyVerifiedError if already verified (idempotent guard).
        """
        user = await self._users.get_by_id(user_id)
        if not user:
            raise VerificationTokenInvalidError()
        if user.email_verified:
            raise AlreadyVerifiedError()
        await self._users.set_email_verified(user_id)
        await self._session.commit()


__all__ = ["AuthService"]
