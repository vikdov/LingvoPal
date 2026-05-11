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

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import encode_token, hash_password, verify_password
from app.models.user import User
from app.models.language import Language
from app.core.exceptions import (
    AlreadyVerifiedError,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    SamePasswordError,
    UsernameAlreadyExistsError,
    VerificationTokenInvalidError,
)
from app.models.user import UserSettings
from app.repositories.user_repo import UserRepository
from app.repositories.user_language_repo import UserLanguageRepository
from app.services.user_settings_service import UserSettingsService
from app.schemas.auth import (
    LoginRequest,
    PasswordChangeRequest,
    SignupRequest,
    TokenResponse,
)
from app.schemas.user import UserPrivateResponse

settings = get_settings()

# Precomputed bcrypt hash for a known dummy password ("dummy").
# Used to ensure constant-time verification when user is not found.
# Prevents timing attacks that could enumerate valid emails.
_DUMMY_HASH = "$2b$12$GHlj3GDmGBhNSBqBVG4N4uK5kHm9VJR3HqE8BgJj1zTdUnkjJOXkG"


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
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    exp = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user.id),
        "role": user.user_status.value,
        "iat": int(now.timestamp()),
        "exp": exp,
    }
    token = encode_token(payload)
    return token, expires_in


def _build_token_response(
    user: User,
    settings: UserSettings,
    active_target_lang_id: int | None,
) -> TokenResponse:
    token, expires_in = _build_token(user)
    return TokenResponse(
        access_token=token,
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

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._user_settings = UserSettingsService(session)
        self._user_languages = UserLanguageRepository(session)

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

        user = await self._users.create(
            email=data.email,
            password_hash=hash_password(data.password),
            username=data.username,
        )

        settings = await self._user_settings.create_for_user(
            user_id=user.id,
            native_lang_id=data.native_lang_id,
            interface_lang_id=interface_lang_id,
        )

        await self._session.commit()
        await self._session.refresh(user)

        active_lang_id = await self._user_languages.get_active_lang_id(user.id)
        return _build_token_response(user, settings, active_lang_id)

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

    async def login(self, data: LoginRequest) -> TokenResponse:
        """
        Validate credentials and return an access token.
        Raises: InvalidCredentialsError

        Timing-safe: bcrypt runs even when the user doesn't exist,
        preventing enumeration via response-time differences.
        """
        user = await self._users.get_by_email(data.email)
        candidate_hash = user.password_hash if user else _DUMMY_HASH

        if not verify_password(data.password, candidate_hash) or not user:
            raise InvalidCredentialsError()

        settings = await self._user_settings.get_or_create(user.id)
        active_lang_id = await self._user_languages.get_active_lang_id(user.id)
        return _build_token_response(user, settings, active_lang_id)

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
