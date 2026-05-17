# backend/app/services/set_service.py
"""
Set service — all business logic for sets and the user set library.

Design decisions documented here:
  - Private set  = status DRAFT  (only visible to creator)
  - Public set   = status APPROVED (visible to everyone; user-controlled, no moderation)
  - Library save = creates a UserSetLibrary row (bookmark); set content is NOT copied
  - Fork set     = creates a new owned DRAFT set; SetItem rows copy (shared item refs, not duplicates)
"""

from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BusinessRuleViolationError,
    DuplicateResourceError,
    NotAuthorizedError,
    ResourceNotFoundError,
)
from app.models.enums import ContentStatus, SessionStatus
from app.models.set import Set
from app.models.study_session import StudySession
from app.models.user_set_library import UserSetLibrary
from app.repositories.item_repo import ItemRepository
from app.repositories.practice_repo import PracticeRepository
from app.repositories.set_repo import SetRepository
from app.repositories.user_repo import UserRepository
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
        self._users = UserRepository(session)
        self._practice = PracticeRepository(session)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def create_set(self, user_id: int, data: SetCreateRequest) -> tuple[Set, int]:
        """
        Create a new set owned by the user and auto-add it to their library.
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
        await self._session.flush()
        await self._sets.save_to_library(user_id, s.id)
        await self._session.commit()
        await self._session.refresh(s)
        return s, 0

    async def get_set(self, user_id: int, set_id: int) -> tuple[Set, int, str | None]:
        """
        Fetch a single set visible to the user.
        Raises ResourceNotFoundError if not found or not accessible.
        Returns (set, item_count, creator_username).
        """
        s = await self._sets.get_by_id(set_id)
        if not s or not _is_visible_to(s, user_id):
            raise ResourceNotFoundError("Set", set_id)
        item_count = await self._sets.count_items(set_id)
        creator_username: str | None = None
        if s.creator_id is not None:
            usernames = await self._users.get_usernames_batch([s.creator_id])
            creator_username = usernames.get(s.creator_id)
        return s, item_count, creator_username

    async def get_my_sets(
        self,
        user_id: int,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[tuple[Set, int, bool]], int]:
        """
        List all sets owned by the user, with item counts and pin status.
        Returns ([(set, item_count, is_pinned), ...], total).
        """
        sets = await self._sets.get_owned(user_id, skip=skip, limit=limit)
        total = await self._sets.count_owned(user_id)
        set_ids = [s.id for s in sets]
        counts = await self._sets.count_items_batch(set_ids)
        pins = await self._sets.get_library_pins_batch(user_id, set_ids)
        results = [(s, counts[s.id], pins.get(s.id, False)) for s in sets]
        return results, total

    async def update_set(
        self, user_id: int, set_id: int, data: SetUpdateRequest
    ) -> tuple[Set, int]:
        """
        Update a set the user owns.
        Raises ResourceNotFoundError, NotAuthorizedError, BusinessRuleViolationError.
        Returns (updated_set, item_count).
        """
        s = await self._sets.get_by_id(set_id)
        if not s:
            raise ResourceNotFoundError("Set", set_id)
        if s.creator_id != user_id:
            raise NotAuthorizedError("update this set")

        sent = data.model_fields_set

        # Guard: source language cannot differ from item languages when items exist
        if "source_lang_id" in sent and data.source_lang_id is not None:
            item_langs = await self._items.get_distinct_item_languages(set_id)
            if item_langs and data.source_lang_id not in item_langs:
                raise BusinessRuleViolationError(
                    f"Cannot change source language: items in this set use "
                    f"language ID(s) {sorted(item_langs)}. Update or remove items first."
                )

        await self._sets.update(
            set_id,
            title=data.title if "title" in sent else None,
            description=data.description if "description" in sent else None,
            difficulty=data.difficulty if "difficulty" in sent else None,
            source_lang_id=data.source_lang_id if "source_lang_id" in sent else None,
            **({"target_lang_id": data.target_lang_id} if "target_lang_id" in sent else {}),
        )
        await self._session.commit()

        updated = await self._sets.get_by_id(set_id)
        item_count = await self._sets.count_items(set_id)
        return updated, item_count

    async def delete_set(self, user_id: int, set_id: int) -> None:
        """
        Soft-delete a set the user owns.
        Also soft-deletes any items owned by the user that are orphaned
        (only membership was in this set — not shared into other sets).
        Raises ResourceNotFoundError, NotAuthorizedError.
        """
        s = await self._sets.get_by_id(set_id)
        if not s:
            raise ResourceNotFoundError("Set", set_id)
        if s.creator_id != user_id:
            raise NotAuthorizedError("delete this set")

        await self._session.execute(
            update(StudySession)
            .where(
                StudySession.set_id == set_id,
                StudySession.status == SessionStatus.IN_PROGRESS,
            )
            .values(status=SessionStatus.ABANDONED, ended_at=datetime.now(timezone.utc))
        )

        orphaned = await self._items.get_orphaned_item_ids(set_id, user_id)
        await self._items.soft_delete_bulk(orphaned)

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
    ) -> tuple[list[tuple[Set, int, str | None]], int]:
        """
        Search public (APPROVED/OFFICIAL) sets with optional filters.
        Returns ([(set, item_count, creator_username), ...], total).
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
        counts = await self._sets.count_items_batch([s.id for s in sets])
        creator_ids = [s.creator_id for s in sets if s.creator_id is not None]
        usernames = await self._users.get_usernames_batch(creator_ids)
        results = [(s, counts[s.id], usernames.get(s.creator_id) if s.creator_id else None) for s in sets]
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
    ) -> tuple[list[tuple[UserSetLibrary, int, int]], int]:
        """Return (entry, item_count, due_count) triples and total count."""
        entries = list(await self._sets.get_user_library(user_id, skip=skip, limit=limit))
        total = await self._sets.count_user_library(user_id)
        set_ids = [e.set_id for e in entries]
        counts = await self._sets.count_items_batch(set_ids)
        due_counts = await self._practice.count_due_items_by_set(user_id, set_ids)
        return [(e, counts.get(e.set_id, 0), due_counts.get(e.set_id, 0)) for e in entries], total

    async def is_in_library(self, user_id: int, set_id: int) -> bool:
        entry = await self._sets.get_library_entry(user_id, set_id)
        return entry is not None

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

    async def touch_set(self, user_id: int, set_id: int) -> None:
        """
        Update last_opened_at for the user's library entry.
        No-op if the set isn't in their library.
        """
        await self._sets.touch_library_entry(user_id, set_id)
        await self._session.commit()

    async def toggle_pin(self, user_id: int, set_id: int, is_pinned: bool) -> None:
        """
        Set the is_pinned flag on a library entry, creating one if needed.
        """
        entry = await self._sets.get_library_entry(user_id, set_id)
        if not entry:
            entry = await self._sets.save_to_library(user_id, set_id)
        entry.is_pinned = is_pinned
        await self._session.commit()

    async def fork_set(self, user_id: int, set_id: int) -> tuple[Set, int]:
        """
        Create an owned private copy of a visible set.

        Behavior:
          - Creates a new DRAFT set with the same metadata, owned by the user.
          - Copies SetItem rows pointing to the *same* Item records (shared references, not duplicates).
          - The fork is private by default; the user can make it public later.
          - If the original was in the user's library, the library entry is swapped to the fork
            (preserving is_pinned), so the user studies their own copy going forward.

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

        # Swap library entry: remove original, add fork (preserve is_pinned)
        original_entry = await self._sets.get_library_entry(user_id, set_id)
        was_pinned = original_entry.is_pinned if original_entry else False
        if original_entry:
            await self._sets.remove_from_library(user_id, set_id)
        fork_entry = await self._sets.save_to_library(user_id, forked.id)
        if was_pinned:
            fork_entry.is_pinned = True

        await self._session.commit()
        await self._session.refresh(forked)
        return forked, len(item_rows)


__all__ = ["SetService"]
