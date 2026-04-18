# backend/app/repositories/user_repo.py
"""
User repository — raw DB access only.

Rules:
  - No business logic, no HTTP, no password hashing
  - Every method is async, receives a Session, returns ORM objects or None
  - Raises nothing domain-specific — callers decide what errors mean
"""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User, UserSettings  # UserSettings kept for selectinload typing
from app.models.enums import UserRole


class UserRepository:
    """
    All DB operations that touch the `users` / `user_settings` tables.

    Instantiated per-request (injected via FastAPI Depends).
    Holds no state beyond the session reference.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    async def get_by_id(
        self,
        user_id: int,
        *,
        load_settings: bool = False,
    ) -> User | None:
        stmt = select(User).where(
            User.id == user_id,
            User.deleted_at.is_(None),
        )
        if load_settings:
            stmt = stmt.options(
                selectinload(User.settings).selectinload(UserSettings.native_language),
                selectinload(User.settings).selectinload(
                    UserSettings.interface_language
                ),
            )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(
        self,
        email: str,
        *,
        load_settings: bool = False,
    ) -> User | None:
        stmt = select(User).where(
            User.email == email,
            User.deleted_at.is_(None),
        )
        if load_settings:
            stmt = stmt.options(
                selectinload(User.settings).selectinload(UserSettings.native_language),
                selectinload(User.settings).selectinload(
                    UserSettings.interface_language
                ),
            )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self._session.execute(
            select(User).where(
                User.username == username,
                User.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        result = await self._session.execute(
            select(User.id).where(User.email == email, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none() is not None

    async def username_exists(self, username: str) -> bool:
        result = await self._session.execute(
            select(User.id).where(User.username == username)
        )
        return result.scalar_one_or_none() is not None

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    async def create(
        self,
        *,
        email: str,
        password_hash: str,
        username: str | None = None,
        is_admin: bool = False,
    ) -> User:
        """
        Insert a new User row.
        Does NOT flush/commit — caller controls the transaction boundary.
        """
        user = User(
            email=email,
            password_hash=password_hash,
            username=username,
            user_status=UserRole.ADMIN if is_admin else UserRole.USER,
        )
        self._session.add(user)
        await self._session.flush()  # populate user.id without committing
        return user

    async def update_password(self, user_id: int, new_hash: str) -> None:
        await self._session.execute(
            update(User).where(User.id == user_id).values(password_hash=new_hash)
        )

    async def set_email_verified(self, user_id: int) -> None:
        await self._session.execute(
            update(User).where(User.id == user_id).values(email_verified=True)
        )

    async def soft_delete(self, user_id: int) -> None:
        """
        Delegates to SoftDeleteTimestampMixin convention —
        sets deleted_at to now via a targeted UPDATE.
        """
        from datetime import datetime, timezone

        await self._session.execute(
            update(User)
            .where(User.id == user_id)
            .values(deleted_at=datetime.now(timezone.utc))
        )


__all__ = ["UserRepository"]
