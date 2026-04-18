# backend/app/repositories/user_settings_repo.py
"""
UserSettings repository — raw DB access only.

Rules:
  - No business logic, no defaults, no validation
  - Every method is async and receives an implicit session via self._session
  - Callers (services) decide what errors mean
"""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import UserSettings


class UserSettingsRepository:
    """
    All DB operations that touch the `user_settings` table.

    Instantiated per-request (injected via FastAPI Depends / service constructor).
    Holds no state beyond the session reference.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Reads ────────────────────────────────────────────────────────────────

    async def get_by_user_id(
        self,
        user_id: int,
        *,
        load_languages: bool = True,
    ) -> UserSettings | None:
        """
        Fetch settings for a user.

        Args:
            load_languages: When True, eagerly loads native_language and
                            interface_language relationships (required for
                            response serialisation).
        """
        stmt = select(UserSettings).where(UserSettings.user_id == user_id)

        if load_languages:
            stmt = stmt.options(
                selectinload(UserSettings.native_language),
                selectinload(UserSettings.interface_language),
            )

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    # ── Writes ───────────────────────────────────────────────────────────────

    async def create(self, user_id: int, data: dict) -> UserSettings:
        """
        Insert a new UserSettings row.

        Args:
            user_id: PK / FK to users table.
            data:    All column values (service is responsible for supplying
                     defaults and validated values — no defaults here).

        Does NOT flush/commit — caller controls the transaction boundary.
        """
        settings = UserSettings(user_id=user_id, **data)
        self._session.add(settings)
        await self._session.flush()  # populate PK without committing
        return settings

    async def update(
        self,
        user_id: int,
        fields: dict,
        *,
        load_languages: bool = True,
    ) -> UserSettings | None:
        """
        Partially update an existing settings row.

        Args:
            user_id:        Target user.
            fields:         Only the fields that should change (service has
                            already merged / validated them).
            load_languages: Whether to eagerly load language relationships
                            in the returned object.

        Returns the refreshed UserSettings row, or None if the row was not found.
        """
        if not fields:
            return await self.get_by_user_id(user_id, load_languages=load_languages)

        await self._session.execute(
            update(UserSettings)
            .where(UserSettings.user_id == user_id)
            .values(**fields)
        )
        await self._session.flush()
        return await self.get_by_user_id(user_id, load_languages=load_languages)


__all__ = ["UserSettingsRepository"]
