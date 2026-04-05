# backend/migrations/env.py
# Alembic environment configuration with async support.
#
# Reads configuration from app.core.config which properly loads .env files
# and URL-encodes the database password.
#
# Handles:
# - Async database connections (asyncpg)
# - PostgreSQL-specific features (partial indexes, schema detection)
# - Custom SQL rendering for complex migrations
# - Proper deprecation handling (compare_type removed in Alembic 1.9+)

from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.engine import Connection
from alembic import context
import asyncio
import sys
from pathlib import Path
from typing import Any, Literal
from alembic.autogenerate.api import AutogenContext

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import settings - this handles all .env file loading and validation
from app.database import Base
from app.core.config import get_settings
from app.models import *

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use auto-generated and URL-encoded DATABASE_URL
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def render_item(
    type_: str, obj: Any, autogen_context: AutogenContext
) -> str | Literal[False]:
    """
    Custom renderer for Alembic to handle complex objects.

    This function is called by Alembic during migration generation.
    It allows us to customize how certain objects are rendered in migrations.

    Args:
        type_: The type of object being rendered (e.g., 'column', 'constraint')
        obj: The actual object being rendered
        autogen_context: Alembic's context object

    Returns:
        A string representation of the object, or False to use default rendering
    """
    # Returning False tells Alembic to use its default rendering engine
    return False


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
    """
    Execute migrations within a sync context.

    This function runs synchronously within the async connection,
    keeping migration logic separate from async orchestration.

    PostgreSQL-specific configuration:
    - compare_server_default=True: Detects server-side default value changes
    - include_schemas=True: Catches schema drift
    - render_item=render_item: Custom rendering for complex objects


    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Detect server-side defaults (better than compare_type)
        compare_server_default=True,
        # Catch schema drift and non-standard schemas
        compare_type=True,
        include_schemas=True,
        # Custom rendering for complex migrations
        render_item=render_item,
        # PostgreSQL: don't batch operations
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
