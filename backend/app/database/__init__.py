# backend/app/database/__init__.py
"""Database infrastructure (engine, session, base, mixins)"""

from app.database.base import (
    Base,
    create_async_db_engine,
    create_sync_db_engine,
)
from app.database.mixins import (
    TimestampMixin,
    SoftDeleteMixin,
)
from app.database.session import (
    AsyncSession,
    init_async_session_factory,
    shutdown_db_engine,
    get_db,
    get_session,
    create_all_tables,
)

__all__ = [
    # Base
    "Base",
    # Mixins
    "TimestampMixin",
    "SoftDeleteMixin",
    # Engine
    "create_async_db_engine",
    "create_sync_db_engine",
    # Session
    "AsyncSession",
    "init_async_session_factory",
    "shutdown_db_engine",
    "get_db",
    "get_session",
    "create_all_tables",
]
