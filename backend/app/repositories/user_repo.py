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

from app.models.enums import UserRole
from app.models.user import User, UserSettings  # UserSettings kept for selectinload typing


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
                selectinload(User.settings).selectinload(UserSettings.interface_language),
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
                selectinload(User.settings).selectinload(UserSettings.interface_language),
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
            select(User.id).where(User.username == username, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none() is not None

    async def get_usernames_batch(self, user_ids: list[int]) -> dict[int, str]:
        """Return {user_id: username} for all given ids that have a username set."""
        if not user_ids:
            return {}
        result = await self._session.execute(
            select(User.id, User.username).where(
                User.id.in_(user_ids),
                User.username.is_not(None),
                User.deleted_at.is_(None),
            )
        )
        return {row.id: row.username for row in result}

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

    async def update_profile_fields(self, user_id: int, patch: dict) -> None:
        await self._session.execute(update(User).where(User.id == user_id).values(**patch))

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
            update(User).where(User.id == user_id).values(deleted_at=datetime.now(timezone.utc))
        )

    async def update_pending_email(self, user_id: int, pending_email: str | None) -> None:
        await self._session.execute(
            update(User).where(User.id == user_id).values(pending_email=pending_email)
        )

    async def confirm_email_change(self, user_id: int, new_email: str) -> None:
        await self._session.execute(
            update(User)
            .where(User.id == user_id)
            .values(email=new_email, pending_email=None, email_verified=True)
        )


__all__ = ["UserRepository"]
