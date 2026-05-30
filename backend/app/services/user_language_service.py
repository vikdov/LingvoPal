# backend/app/services/user_language_service.py
"""Service for managing the languages a user is learning."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateResourceError, ResourceNotFoundError
from app.models.language import Language
from app.models.user_language import UserLanguage
from app.repositories.user_language_repo import UserLanguageRepository


class UserLanguageService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = UserLanguageRepository(session)

    async def _assert_language_exists(self, language_id: int) -> None:
        result = await self._session.execute(select(Language.id).where(Language.id == language_id))
        if result.scalar_one_or_none() is None:
            raise ResourceNotFoundError("Language", language_id)

    async def get_all(self, user_id: int) -> list[UserLanguage]:
        return await self._repo.get_all(user_id)

    async def get_active_lang_id(self, user_id: int) -> int | None:
        return await self._repo.get_active_lang_id(user_id)

    async def add_language(
        self,
        user_id: int,
        language_id: int,
        set_active: bool = True,
    ) -> UserLanguage:
        await self._assert_language_exists(language_id)

        existing = await self._repo.get(user_id, language_id)
        if existing is not None:
            raise DuplicateResourceError("UserLanguage", "language_id", str(language_id))

        await self._repo.add(user_id, language_id)

        if set_active:
            await self._repo.set_active(user_id, language_id)

        await self._session.commit()
        return await self._repo.get(user_id, language_id)  # type: ignore[return-value]

    async def activate_language(self, user_id: int, language_id: int) -> UserLanguage:
        await self._assert_language_exists(language_id)

        existing = await self._repo.get(user_id, language_id)
        if existing is None:
            await self._repo.add(user_id, language_id)

        row = await self._repo.set_active(user_id, language_id)
        await self._session.commit()
        return row  # type: ignore[return-value]

    async def remove_language(self, user_id: int, language_id: int) -> None:
        row = await self._repo.get(user_id, language_id)
        if row is None:
            raise ResourceNotFoundError("UserLanguage", language_id)

        was_active = row.is_active
        removed = await self._repo.remove(user_id, language_id)
        if not removed:
            raise ResourceNotFoundError("UserLanguage", language_id)

        if was_active:
            remaining = await self._repo.get_all(user_id)
            if remaining:
                await self._repo.set_active(user_id, remaining[0].language_id)

        await self._session.commit()


__all__ = ["UserLanguageService"]
