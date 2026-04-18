# backend/app/services/set_service.py
"""
Set service — all business logic for sets and the user set library.

Design decisions documented here:
  - Private set  = status DRAFT  (only visible to creator)
  - Public set   = status APPROVED (visible to everyone; user-controlled, no moderation)
  - Library save = creates a UserSetLibrary row (bookmark); set content is NOT copied
  - Fork set     = creates a new owned DRAFT set; SetItem rows copy (shared item refs, not duplicates)
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DuplicateResourceError,
    NotAuthorizedError,
    ResourceNotFoundError,
)
from app.models.enums import ContentStatus
from app.models.set import Set
from app.models.user_set_library import UserSetLibrary
from app.repositories.item_repo import ItemRepository
from app.repositories.set_repo import SetRepository
from app.schemas.set import SetCreateRequest, SetUpdateRequest

_PUBLIC_STATUSES = (ContentStatus.APPROVED, ContentStatus.OFFICIAL)


def _is_visible_to(s: Set, user_id: int) -> bool:
    """A set is visible if the requesting user owns it, or if it is public."""
    return s.creator_id == user_id or s.status in _PUBLIC_STATUSES


class SetService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._sets = SetRepository(session)
        self._items = ItemRepository(session)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def create_set(self, user_id: int, data: SetCreateRequest) -> tuple[Set, int]:
        """
        Create a new set owned by the user.
        Returns (set, item_count=0).
        """
        s = await self._sets.create(
            title=data.title,
            description=data.description,
            difficulty=data.difficulty,
            source_lang_id=data.source_lang_id,
            target_lang_id=data.target_lang_id,
            creator_id=user_id,
            status=ContentStatus.DRAFT,
        )
        await self._session.commit()
        await self._session.refresh(s)
        return s, 0

    async def get_set(self, user_id: int, set_id: int) -> tuple[Set, int]:
        """
        Fetch a single set visible to the user.
        Raises ResourceNotFoundError if not found or not accessible.
        Returns (set, item_count).
        """
        s = await self._sets.get_by_id(set_id)
        if not s or not _is_visible_to(s, user_id):
            raise ResourceNotFoundError("Set", set_id)
        item_count = await self._sets.count_items(set_id)
        return s, item_count

    async def get_my_sets(
        self,
        user_id: int,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[tuple[Set, int]], int]:
        """
        List all sets owned by the user, with their item counts.
        Returns ([(set, item_count), ...], total).
        """
        sets = await self._sets.get_owned(user_id, skip=skip, limit=limit)
        total = await self._sets.count_owned(user_id)
        results = [(s, await self._sets.count_items(s.id)) for s in sets]
        return results, total

    async def update_set(
        self, user_id: int, set_id: int, data: SetUpdateRequest
    ) -> tuple[Set, int]:
        """
        Update a set the user owns.
        Raises ResourceNotFoundError, NotAuthorizedError.
        Returns (updated_set, item_count).
        """
        s = await self._sets.get_by_id(set_id)
        if not s:
            raise ResourceNotFoundError("Set", set_id)
        if s.creator_id != user_id:
            raise NotAuthorizedError("update this set")

        await self._sets.update(
            set_id,
            title=data.title,
            description=data.description,
            difficulty=data.difficulty,
        )
        await self._session.commit()

        updated = await self._sets.get_by_id(set_id)
        item_count = await self._sets.count_items(set_id)
        return updated, item_count

    async def delete_set(self, user_id: int, set_id: int) -> None:
        """
        Soft-delete a set the user owns.
        SetItem rows remain in DB but become inaccessible (filtered via deleted_at on Set).
        Items themselves are unaffected — they may still exist in other sets.
        Raises ResourceNotFoundError, NotAuthorizedError.
        """
        s = await self._sets.get_by_id(set_id)
        if not s:
            raise ResourceNotFoundError("Set", set_id)
        if s.creator_id != user_id:
            raise NotAuthorizedError("delete this set")

        await self._sets.soft_delete(set_id)
        await self._session.commit()

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    async def search_public_sets(
        self,
        *,
        query: str | None = None,
        source_lang_id: int | None = None,
        target_lang_id: int | None = None,
        difficulty: int | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[tuple[Set, int]], int]:
        """
        Search public (APPROVED/OFFICIAL) sets with optional filters.
        Returns ([(set, item_count), ...], total).
        """
        sets = await self._sets.search_public(
            query=query,
            source_lang_id=source_lang_id,
            target_lang_id=target_lang_id,
            difficulty=difficulty,
            skip=skip,
            limit=limit,
        )
        total = await self._sets.count_public(
            query=query,
            source_lang_id=source_lang_id,
            target_lang_id=target_lang_id,
            difficulty=difficulty,
        )
        results = [(s, await self._sets.count_items(s.id)) for s in sets]
        return results, total

    # ------------------------------------------------------------------
    # User set library
    # ------------------------------------------------------------------

    async def get_user_library(
        self,
        user_id: int,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> list[UserSetLibrary]:
        """Return the user's saved library entries (sets are eagerly loaded)."""
        return list(await self._sets.get_user_library(user_id, skip=skip, limit=limit))

    async def save_set_to_library(
        self, user_id: int, set_id: int
    ) -> UserSetLibrary:
        """
        Bookmark a set in the user's library.
        The set must be visible to the user (own or public).
        Raises: ResourceNotFoundError if not visible, DuplicateResourceError if already saved.
        """
        s = await self._sets.get_by_id(set_id)
        if not s or not _is_visible_to(s, user_id):
            raise ResourceNotFoundError("Set", set_id)

        existing = await self._sets.get_library_entry(user_id, set_id)
        if existing:
            raise DuplicateResourceError("UserSetLibrary", "set_id", str(set_id))

        entry = await self._sets.save_to_library(user_id, set_id)
        await self._session.commit()
        return entry

    async def remove_set_from_library(self, user_id: int, set_id: int) -> None:
        """
        Remove a set from the user's library.
        Raises ResourceNotFoundError if the entry doesn't exist.
        """
        existing = await self._sets.get_library_entry(user_id, set_id)
        if not existing:
            raise ResourceNotFoundError("UserSetLibrary entry for set", set_id)

        await self._sets.remove_from_library(user_id, set_id)
        await self._session.commit()

    async def fork_set(self, user_id: int, set_id: int) -> tuple[Set, int]:
        """
        Create an owned private copy of a visible set.

        Behavior:
          - Creates a new DRAFT set with the same metadata, owned by the user.
          - Copies SetItem rows pointing to the *same* Item records (shared references, not duplicates).
          - The fork is private by default; the user can make it public later.

        Raises ResourceNotFoundError if source set is not found or not accessible.
        """
        source = await self._sets.get_by_id(set_id)
        if not source or not _is_visible_to(source, user_id):
            raise ResourceNotFoundError("Set", set_id)

        forked = await self._sets.create(
            title=source.title,
            description=source.description,
            difficulty=source.difficulty,
            source_lang_id=source.source_lang_id,
            target_lang_id=source.target_lang_id,
            creator_id=user_id,
            status=ContentStatus.DRAFT,
        )

        # Copy item references (not the items themselves)
        item_rows = await self._items.get_item_ids_for_set(set_id)
        for item_id, sort_order in item_rows:
            await self._items.add_to_set(forked.id, item_id, sort_order)

        await self._session.commit()
        await self._session.refresh(forked)
        return forked, len(item_rows)


__all__ = ["SetService"]
