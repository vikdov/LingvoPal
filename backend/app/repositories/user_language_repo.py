# backend/app/repositories/user_language_repo.py
"""UserLanguage repository — raw DB access only."""

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user_language import UserLanguage


class UserLanguageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self, user_id: int) -> list[UserLanguage]:
        result = await self._session.execute(
            select(UserLanguage)
            .where(UserLanguage.user_id == user_id)
            .options(selectinload(UserLanguage.language))
            .order_by(UserLanguage.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_active(self, user_id: int) -> UserLanguage | None:
        result = await self._session.execute(
            select(UserLanguage)
            .where(
                UserLanguage.user_id == user_id,
                UserLanguage.is_active == True,  # noqa: E712
            )
            .options(selectinload(UserLanguage.language))
        )
        return result.scalar_one_or_none()

    async def get_active_lang_id(self, user_id: int) -> int | None:
        result = await self._session.execute(
            select(UserLanguage.language_id).where(
                UserLanguage.user_id == user_id,
                UserLanguage.is_active == True,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def get(self, user_id: int, language_id: int) -> UserLanguage | None:
        result = await self._session.execute(
            select(UserLanguage)
            .where(
                UserLanguage.user_id == user_id,
                UserLanguage.language_id == language_id,
            )
            .options(selectinload(UserLanguage.language))
        )
        return result.scalar_one_or_none()

    async def add(self, user_id: int, language_id: int) -> UserLanguage:
        row = UserLanguage(user_id=user_id, language_id=language_id, is_active=False)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row, attribute_names=["language"])
        return row

    async def deactivate_all(self, user_id: int) -> None:
        await self._session.execute(
            update(UserLanguage)
            .where(UserLanguage.user_id == user_id)
            .values(is_active=False)
        )

    async def set_active(self, user_id: int, language_id: int) -> UserLanguage | None:
        await self.deactivate_all(user_id)
        await self._session.execute(
            update(UserLanguage)
            .where(
                UserLanguage.user_id == user_id,
                UserLanguage.language_id == language_id,
            )
            .values(is_active=True)
        )
        await self._session.flush()
        return await self.get(user_id, language_id)

    async def remove(self, user_id: int, language_id: int) -> bool:
        result = await self._session.execute(
            delete(UserLanguage).where(
                UserLanguage.user_id == user_id,
                UserLanguage.language_id == language_id,
            )
        )
        return result.rowcount > 0


__all__ = ["UserLanguageRepository"]
