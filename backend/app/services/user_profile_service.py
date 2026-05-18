# backend/app/services/user_profile_service.py
"""
UserProfileService — business logic for the authenticated user's own profile.

Owns:
  - Username uniqueness check before update
  - Profile field updates
  - Account soft-deletion

Routes call this service instead of touching UserRepository directly.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateResourceError
from app.repositories.user_repo import UserRepository


class UserProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = UserRepository(session)
        self._session = session

    async def update_profile(self, user_id: int, patch: dict) -> None:
        """
        Apply profile field updates, enforcing username uniqueness.
        Raises DuplicateResourceError if the requested username is taken.
        Does NOT commit — caller owns the transaction boundary.
        """
        if "username" in patch and patch["username"] is not None:
            existing = await self._repo.get_by_username(patch["username"])
            if existing is not None and existing.id != user_id:
                raise DuplicateResourceError("This username is already taken.")

        await self._repo.update_profile_fields(user_id, patch)

    async def soft_delete(self, user_id: int) -> None:
        """Soft-delete user account. Does NOT commit — caller owns transaction."""
        await self._repo.soft_delete(user_id)
