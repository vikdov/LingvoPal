# backend/app/core/dependencies.py
"""
FastAPI dependencies with proper async/await patterns.

Dependency injection for:
- Database sessions (async)
- Authentication (JWT tokens)
- Authorization (verified users, admins)
- Settings
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings, Settings
from app.core.security import decode_access_token
from app.database.session import get_db
from app.models.user import User

# ============================================================================
# OAuth2 Scheme
# ============================================================================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ============================================================================
# Database
# ============================================================================


async def get_database() -> AsyncSession:
    """
    FastAPI dependency: Get async database session.

    Usage:
        @app.get("/items")
        async def list_items(db: AsyncSession = Depends(get_database)):
            result = await db.execute(select(Item))
            return result.scalars().all()

    Note: This is an alias to app.database.session.get_db()
    but defined here for clarity and centralization.
    """
    async with get_db() as session:
        yield session


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
    db: Annotated[AsyncSession, Depends(get_database)],
) -> User:
    """
    FastAPI dependency: Get current authenticated user.

    ✅ Async: Uses async ORM queries
    ✅ Validates JWT token
    ✅ Looks up user in database

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
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    # ✅ ASYNC: Use select() + execute()
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

    ✅ Requires: User is authenticated + email verified

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

    ✅ Requires: User is authenticated + verified + is_admin

    Raises:
        HTTPException 403: Not an admin

    Usage:
        @app.delete("/users/{user_id}")
        async def delete_user(admin: User = Depends(get_current_admin)):
            # Only admins can delete users
            return admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


# ============================================================================
# Type Aliases (Modern FastAPI Pattern)
# ============================================================================

# Database
DBSession = Annotated[AsyncSession, Depends(get_database)]

# Authentication (increasing privilege levels)
CurrentUser = Annotated[User, Depends(get_current_user)]
VerifiedUser = Annotated[User, Depends(get_current_verified_user)]
AdminUser = Annotated[User, Depends(get_current_admin)]

# Settings
CurrentSettings = Annotated[Settings, Depends(get_current_settings)]


__all__ = [
    "oauth2_scheme",
    "get_database",
    "get_current_settings",
    "get_current_user",
    "get_current_verified_user",
    "get_current_admin",
    # Type aliases
    "DBSession",
    "CurrentUser",
    "VerifiedUser",
    "AdminUser",
    "CurrentSettings",
]
