# backend/migrations/env.py
# Alembic environment configuration with async support.
#
# Reads DATABASE_URL from app.core.config (handles .env loading + URL encoding).
# Runs async migrations via asyncpg with NullPool (no connection pooling).

from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.engine import Connection
from alembic import context
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Base
from app.core.config import get_settings
from app.models import (
    Language, User, UserSettings,
    Item, Translation, Set, SetItem, ItemSynonym,
    UserSetLibrary, StudySession, StudyReview, UserProgress,
    UserDailyStats, UserStatsTotal,
    PendingModeration, PendingSession, ContentAuditLog,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use auto-generated and URL-encoded DATABASE_URL
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine. Calls to context.execute() here emit
    the given string to the script output.

    Use case:
    - Generate migration SQL without connecting to DB
    - DBA review before applying
    - Air-gapped environments
    """
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Execute migrations within a sync context (bridged from async runner)."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_server_default=True,
        include_schemas=True,
        render_as_batch=False,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode (connects to database).

    Creates an async engine, establishes a connection,
    and delegates to the sync migration executor.

    This approach allows us to use async SQLAlchemy while keeping
    Alembic's migration logic synchronous (Alembic doesn't natively
    support async, but we can bridge the gap).
    """
    connectable = create_async_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,  # No pooling for migrations
        echo=False,
    )

    async with connectable.begin() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


# ============================================================================
# Entry Point
# ============================================================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
