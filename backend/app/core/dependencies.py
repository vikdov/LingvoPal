# backend/app/core/dependencies.py
"""
FastAPI dependencies with proper async/await patterns.

Dependency injection for:
- Database sessions (async)
- Authentication (JWT tokens)
- Authorization (verified users, admins)
- Settings
"""

from typing import Annotated, AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings, Settings
from app.database.session import get_db
from app.services.stats_service import StatsService
from app.database.session_utils import set_db_current_user
from app.models.user import User
from app.models.enums import UserRole
import redis.asyncio as aioredis

from app.services.auth_service import AuthService
from app.services.item_service import ItemService
from app.services.practice_service import PracticeService
from app.services.set_service import SetService
from app.services.user_settings_service import UserSettingsService
from app.core.security import decode_token as decode_access_token

# ============================================================================
# OAuth2 Scheme
# ============================================================================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ============================================================================
# Database
# ============================================================================


# ============================================================================
# Settings
# ============================================================================


def get_current_settings() -> Settings:
    """
    FastAPI dependency: Get application settings.

    Usage:
        @app.get("/config")
        async def get_config(settings: Settings = Depends(get_current_settings)):
            return {"debug": settings.DEBUG}
    """
    return get_settings()


# ============================================================================
# Authentication
# ============================================================================


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    FastAPI dependency: Get current authenticated user.

    Async: Uses async ORM queries
    Validates JWT token
    Looks up user in database

    Raises:
        HTTPException 401: Invalid or missing token
        HTTPException 401: User not found

    Usage:
        @app.get("/me")
        async def get_profile(user: User = Depends(get_current_user)):
            return user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode JWT token
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise credentials_exception
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    # ASYNC: Use select() + execute()
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_verified_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    FastAPI dependency: Get current user with verified email.

    Requires: User is authenticated + email verified

    Raises:
        HTTPException 403: Email not verified

    Usage:
        @app.post("/items")
        async def create_item(user: User = Depends(get_current_verified_user)):
            # Only verified users can create items
            return user
    """
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified",
        )
    return current_user


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_verified_user)],
) -> User:
    """
    FastAPI dependency: Get current admin user.

    Requires: User is authenticated + verified + is_admin

    Raises:
        HTTPException 403: Not an admin

    Usage:
        @app.delete("/users/{user_id}")
        async def delete_user(admin: User = Depends(get_current_admin)):
            # Only admins can delete users
            return admin
    """
    if current_user.user_status != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


async def get_db_for_writes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AsyncSession:
    """
    A specialized DB dependency for routes that mutate data (INSERT/UPDATE/DELETE).
    Automatically injects the audit user ID into the PostgreSQL transaction.
    """
    await set_db_current_user(db, current_user.id)
    return db


# ============================================================================
# Type Aliases (Modern FastAPI Pattern)
# ============================================================================

# Database
DBSession = Annotated[AsyncSession, Depends(get_db)]
WriteDBSession = Annotated[AsyncSession, Depends(get_db_for_writes)]

# Authentication (increasing privilege levels)
CurrentUser = Annotated[User, Depends(get_current_user)]
VerifiedUser = Annotated[User, Depends(get_current_verified_user)]
AdminUser = Annotated[User, Depends(get_current_admin)]

# Settings
CurrentSettings = Annotated[Settings, Depends(get_current_settings)]

# ============================================================================
# Service Dependencies  (add below your existing type aliases)
# ============================================================================


async def get_auth_service(db: DBSession) -> AuthService:
    """FastAPI dependency: Auth service, injected with current session."""
    return AuthService(db)


async def get_set_service(db: DBSession) -> SetService:
    """FastAPI dependency: Set service, injected with current session."""
    return SetService(db)


async def get_item_service(db: DBSession) -> ItemService:
    """FastAPI dependency: Item service, injected with current session."""
    return ItemService(db)


async def get_user_settings_service(db: DBSession) -> UserSettingsService:
    """FastAPI dependency: UserSettings service, injected with current session."""
    return UserSettingsService(db)


# ── Redis ────────────────────────────────────────────────────────────────────


async def get_redis_client() -> AsyncGenerator[aioredis.Redis, None]:
    """FastAPI dependency: yield the shared async Redis client."""
    from app.core.redis import get_redis

    async for client in get_redis():
        yield client


async def get_practice_service(
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_user)],
    redis: Annotated[aioredis.Redis, Depends(get_redis_client)],
) -> PracticeService:
    """FastAPI dependency: PracticeService, injected with session + Redis + user_id."""
    return PracticeService(db=db, redis=redis, user_id=current_user.id)


async def get_stats_service(
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> StatsService:
    return StatsService(db, current_user.id)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
StatsServiceDep = Annotated[StatsService, Depends(get_stats_service)]
SetServiceDep = Annotated[SetService, Depends(get_set_service)]
ItemServiceDep = Annotated[ItemService, Depends(get_item_service)]
UserSettingsServiceDep = Annotated[
    UserSettingsService, Depends(get_user_settings_service)
]
PracticeServiceDep = Annotated[PracticeService, Depends(get_practice_service)]


__all__ = [
    "oauth2_scheme",
    "get_db",
    "get_db_for_writes",
    "get_current_settings",
    "get_current_user",
    "get_current_verified_user",
    "get_current_admin",
    # Type aliases
    "DBSession",
    "WriteDBSession",
    "CurrentUser",
    "VerifiedUser",
    "AdminUser",
    "CurrentSettings",
    "get_auth_service",
    "get_set_service",
    "get_item_service",
    "get_user_settings_service",
    "get_redis_client",
    "get_stats_service",
    "get_practice_service",
    "AuthServiceDep",
    "SetServiceDep",
    "ItemServiceDep",
    "UserSettingsServiceDep",
    "PracticeServiceDep",
    "StatsServiceDep",
]
