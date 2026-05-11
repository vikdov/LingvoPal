# backend/app/repositories/audit_repo.py
"""ContentAuditLog repository — append-only audit trail for moderation actions."""

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_audit_log import ContentAuditLog


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def log(
        self,
        table_name: str,
        record_id: int,
        action: str,
        user_id: int | None = None,
        old_values: dict | None = None,
        new_values: dict | None = None,
    ) -> None:
        entry = ContentAuditLog(
            table_name=table_name,
            record_id=record_id,
            action=action,
            user_id=user_id,
            old_values=old_values,
            new_values=new_values,
        )
        self._session.add(entry)
        await self._session.flush()

    async def list_all(
        self,
        *,
        table_name: str | None = None,
        action: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Sequence[ContentAuditLog]:
        stmt = select(ContentAuditLog).order_by(ContentAuditLog.created_at.desc())
        if table_name is not None:
            stmt = stmt.where(ContentAuditLog.table_name == table_name)
        if action is not None:
            stmt = stmt.where(ContentAuditLog.action == action)
        result = await self._session.execute(stmt.offset(skip).limit(limit))
        return result.scalars().all()

    async def count_all(
        self,
        *,
        table_name: str | None = None,
        action: str | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(ContentAuditLog)
        if table_name is not None:
            stmt = stmt.where(ContentAuditLog.table_name == table_name)
        if action is not None:
            stmt = stmt.where(ContentAuditLog.action == action)
        result = await self._session.execute(stmt)
        return result.scalar_one()


__all__ = ["AuditRepository"]
