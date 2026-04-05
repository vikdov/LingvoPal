# backend/app/database/session.py
"""
Async SQLAlchemy session management for FastAPI.

Pattern: Dependency injection with async context managers
Lifecycle: Proper engine disposal on shutdown
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


# ============================================================================
# Global State (Session Factory + Engine)
# ============================================================================

async_session_factory: async_sessionmaker | None = None
_engine: AsyncEngine | None = None  # ← Keep reference for shutdown


async def init_async_session_factory(
    database_url: str,
    pool_size: int = 10,
    max_overflow: int = 20,
) -> async_sessionmaker:
    """
    Initialize the async session factory.

    Must be called once during application startup.
    Pairs with shutdown_db_engine() for cleanup.

    ARCHITECTURE NOTE:
    We use global mutable state here because:
    - FastAPI has a single app instance per process
    - This pattern is standard in the FastAPI ecosystem
    - We keep engine reference globally for proper shutdown

    Args:
        database_url: PostgreSQL async connection string
                     Format: postgresql+asyncpg://user:password@host:port/database
        pool_size: Connection pool size (default: 10)
        max_overflow: Max overflow connections (default: 20)

    Returns:
        Configured async_sessionmaker

    Raises:
        ImportError: If SQLAlchemy not installed
        ArgumentError: If database_url is invalid

    Example:
        @app.on_event("startup")
        async def startup():
            await init_async_session_factory(settings.DATABASE_URL)
    """
    global async_session_factory, _engine

    from app.database.base import create_async_db_engine

    _engine = create_async_db_engine(
        database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
    )

    async_session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    return async_session_factory


async def shutdown_db_engine() -> None:
    """
    Shutdown database engine and dispose of all connections.

    Must be called on application shutdown.
    Pairs with init_async_session_factory() for proper lifecycle.

    IMPORTANT:
    - Closes all pooled connections cleanly
    - Allows graceful shutdown
    - Prevents connection leaks

    Example:
        @app.on_event("shutdown")
        async def shutdown():
            await shutdown_db_engine()
    """
    global _engine

    if _engine is not None:
        await _engine.dispose()
        _engine = None


# ============================================================================
# FastAPI Dependency
# ============================================================================


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: yields an async database session.

    Automatically handles:
    - Session creation
    - Error handling (rollback on exception)
    - Connection cleanup

    Usage:
        @app.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item).where(Item.deleted_at.is_(None)))
            return result.scalars().all()

    Yields:
        AsyncSession instance

    Raises:
        RuntimeError: If session factory not initialized

    Flow:
        1. get_db() called by FastAPI
        2. Session created from pool
        3. Endpoint executes
        4. On exception: rollback, close
        5. On success: implicit close, connection returned to pool
    """
    if async_session_factory is None:
        raise RuntimeError(
            "Async session factory not initialized. "
            "Call await init_async_session_factory() in app startup event."
        )

    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


# ============================================================================
# Background Task / Non-FastAPI Contexts
# ============================================================================


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for async sessions outside FastAPI.

    IMPORTANT: Use this for background tasks, not FastAPI endpoints.
    For FastAPI endpoints, use get_db() dependency.

    Guarantees:
    - Automatic cleanup (even on exception)
    - Automatic commit on success
    - Automatic rollback on error
    - Connection returned to pool

    Usage (background task):
        async def process_study_session(user_id: int):
            async with get_session() as db:
                user = await db.get(User, user_id)
                user.updated_at = datetime.now(timezone.utc)
                # work with db
            # session automatically committed and closed

    Yields:
        AsyncSession instance with guaranteed cleanup

    Raises:
        RuntimeError: If session factory not initialized
    """
    if async_session_factory is None:
        raise RuntimeError(
            "Async session factory not initialized. "
            "Call await init_async_session_factory() in app startup event."
        )

    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()


# ============================================================================
# Database Initialization (DEV ONLY)
# ============================================================================


async def create_all_tables(database_url: str) -> None:
    """
    Create all tables in the database.

    WARNING: DO NOT use in production!

    This function is for:
    Development setup
    Testing
    Local environment initialization

    NEVER use in production → use Alembic migrations instead

    Alembic provides:
    - Version control
    - Rollback capability
    - Data migration support
    - Audit trail

    NOTE: This should NOT be called from main.py.
    Instead, use: scripts/dev_setup.py

    Args:
        database_url: PostgreSQL async connection string

    Raises:
        ConnectionError: If database unreachable
    """
    from app.database.base import Base, create_async_db_engine

    engine = create_async_db_engine(database_url)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    finally:
        await engine.dispose()


__all__ = [
    "AsyncSession",
    "init_async_session_factory",
    "shutdown_db_engine",
    "get_db",
    "get_session",
    "create_all_tables",
]
