# backend/app/repositories/base_repo.py
from typing import TypeVar, Generic, Type, Sequence, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.base import Base
from app.database.mixins import SoftDeleteTimestampMixin

# Type variables for the generic repository
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository providing standard CRUD operations.
    Handles soft-delete logic explicitly.
    """

    def __init__(self, model: Type[ModelType]):
        self.model = model
        # Check once at initialization if this model supports soft deletes
        self.is_soft_deletable = issubclass(model, SoftDeleteTimestampMixin)

    async def get_by_id(
        self, db: AsyncSession, id: Any, include_deleted: bool = False
    ) -> ModelType | None:
        """Fetch a single record by ID, excluding soft-deleted by default."""
        query = select(self.model).where(self.model.id == id)

        if self.is_soft_deletable and not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_active(self, db: AsyncSession) -> Sequence[ModelType]:
        """Fetch all active (non-deleted) records."""
        query = select(self.model)

        if self.is_soft_deletable:
            query = query.where(self.model.deleted_at.is_(None))

        result = await db.execute(query)
        return result.scalars().all()

    async def soft_delete(self, db: AsyncSession, db_obj: ModelType) -> None:
        """Safely soft-delete a record."""
        if not self.is_soft_deletable:
            raise TypeError(f"{self.model.__name__} does not support soft deletion.")

        db_obj.soft_delete()  # Calls the method from your mixin
        db.add(db_obj)
        # Note: commit() is usually handled by the caller/service layer
