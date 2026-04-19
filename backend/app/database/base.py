# backend/app/database/base.py
"""
SQLAlchemy 2.0 declarative base with async support.

ARCHITECTURE:
- Async SQLAlchemy with asyncpg driver
- Database-driven timestamps (timezone-aware UTC)
- Pydantic for serialization (not ORM)
- Conservative connection pooling (scale with metrics)
"""

from datetime import datetime
from sqlalchemy import MetaData, create_engine, DateTime, event
from sqlalchemy.dialects.postgresql import JSONB, TEXT
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapper
# ============================================================================
# PostgreSQL Metadata Setup
# ============================================================================

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=naming_convention)


# ============================================================================
# Base Declarative Class
# ============================================================================


class Base(DeclarativeBase):
    """Base class for all ORM models"""

    metadata = metadata
    type_annotation_map = {
        dict: JSONB,
        datetime: DateTime(timezone=True),
        str: TEXT,
    }


@event.listens_for(Mapper, "mapper_configured")
def _set_global_async_lazy_loading(mapper: Mapper, _class: type) -> None:
    """
    Automatically sets lazy='raise_on_sql' for ALL relationships globally.
    Prevents synchronous lazy-loading and 'MissingGreenlet' crashes in asyncpg.
    """
    for relationship_property in mapper.relationships:
        # If the developer didn't explicitly define a lazy strategy,
        # it defaults to "select". We change that default to "raise_on_sql".
        if relationship_property.lazy == "select":
            relationship_property.lazy = "raise_on_sql"


# ============================================================================
# Async Engine Factory
# ============================================================================


def create_async_db_engine(
    database_url: str,
    echo: bool = False,
    pool_size: int = 10,
    max_overflow: int = 20,
) -> AsyncEngine:
    """
    Create an async SQLAlchemy engine for PostgreSQL with asyncpg.

    NOTE: This function is synchronous (not async).
    create_async_engine() creates the engine without I/O.

    Args:
        database_url: PostgreSQL async connection string
                     Format: postgresql+asyncpg://user:password@host:port/database
        echo: Whether to log SQL statements (debug mode)
        pool_size: Number of pre-created connections (default: 10)
        max_overflow: Max additional connections beyond pool_size (default: 20)

    Returns:
        AsyncEngine instance (ready to use)

    Raises:
        ArgumentError: If database_url format is invalid

    POOL SIZING STRATEGY:
    - Start conservative: pool_size=10, max_overflow=20 (total 30 per instance)
    - Monitor with: SELECT count(*) FROM pg_stat_activity;
    - Scale up only based on metrics
    - Remember: N instances × pool_size = total connections

    Example:
        # Single instance: 10 + 20 = 30 connections
        engine = create_async_db_engine(settings.DATABASE_URL)

        # 4 instances: 4 × 30 = 120 connections (watch PG limits!)

    Example usage:
        engine = create_async_db_engine(settings.DATABASE_URL)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()
    """

    engine = create_async_engine(
        database_url,
        echo=echo,
        # Connection pooling (conservative defaults)
        pool_size=pool_size,  # Pre-created connections
        max_overflow=max_overflow,  # Max additional connections
        pool_recycle=3600,  # Recycle connections after 1 hour
        pool_pre_ping=True,  # Verify connection before use
        pool_timeout=30,
        # PostgreSQL configuration
        connect_args={
            "server_settings": {
                "application_name": "lingvopal",
                # Removed: "jit": "off"
                # Reason: JIT helps some queries, hurts others
                # Let PostgreSQL decide based on query patterns
                # Monitor performance; enable/disable at DB level if needed
            }
        },
    )

    return engine


# ============================================================================
# Sync Engine Factory (for migrations/admin)
# ============================================================================


def create_sync_db_engine(
    database_url: str,
    echo: bool = False,
    pool_size: int = 5,
    max_overflow: int = 10,
):
    """
    Create a synchronous SQLAlchemy engine for PostgreSQL.

    Used for:
    - Alembic migrations
    - Database admin tasks
    - Initial setup scripts

    Args:
        database_url: PostgreSQL sync connection string
                     Format: postgresql://user:password@host:port/database
                     NOTE: Not the asyncpg version!
        echo: Whether to log SQL statements
        pool_size: Number of pre-created connections (default: 5)
        max_overflow: Max additional connections (default: 10)

    Returns:
        Synchronous SQLAlchemy engine

    Note:
        Sync engine uses smaller pool since migrations are one-time operations

    Example:
        engine = create_sync_db_engine(settings.DATABASE_URL_SYNC)
        Base.metadata.create_all(bind=engine)
    """

    engine = create_engine(
        database_url,
        echo=echo,
        pool_size=pool_size,  # Smaller for sync
        max_overflow=max_overflow,
        pool_recycle=3600,
        pool_pre_ping=True,
    )

    return engine


__all__ = [
    "Base",
    "metadata",
    "create_async_db_engine",
    "create_sync_db_engine",
]
