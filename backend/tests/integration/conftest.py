# tests/integration/conftest.py
"""
Integration test fixtures.

Requirements:
  - TEST_DATABASE_URL env var pointing to a PostgreSQL test database
    e.g. postgresql+asyncpg://test_user:test_pass@localhost:5432/lingvopal_test
  - Tests are skipped automatically when TEST_DATABASE_URL is absent.

Each test gets:
  - A clean database session wrapped in a transaction that is rolled back.
  - A fakeredis client (full Lua support) — no real Redis required.
  - An httpx AsyncClient wired to the FastAPI app via ASGITransport.
"""

import os
import pytest
import pytest_asyncio
import fakeredis.aioredis
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.database.session import get_db
from app.core.redis import get_redis_client

# ── Skip all integration tests if no DB configured ───────────────────────────

TEST_DB_URL = os.environ.get("TEST_DATABASE_URL", "")

pytestmark = pytest.mark.asyncio


def _skip_without_db():
    if not TEST_DB_URL:
        pytest.skip("TEST_DATABASE_URL not set — skipping integration tests")


# ── Shared engine (one per session) ──────────────────────────────────────────

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create async engine and initialise schema once per test session."""
    _skip_without_db()
    engine = create_async_engine(TEST_DB_URL, echo=False)
    from app.database.base import Base
    # Import all models so Base.metadata is populated
    import app.models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture()
async def db_session(test_engine):
    """Per-test session wrapped in a savepoint — rolled back after each test."""
    conn = await test_engine.connect()
    await conn.begin()
    session_factory = async_sessionmaker(bind=conn, expire_on_commit=False)
    session = session_factory()
    # Nested savepoint so each test is isolated
    await conn.begin_nested()

    yield session

    await session.close()
    await conn.rollback()
    await conn.close()


@pytest_asyncio.fixture()
async def redis_client():
    """fakeredis client with Lua scripting enabled."""
    client = fakeredis.aioredis.FakeRedis(version=(7, 0, 0))
    yield client
    await client.aclose()


@pytest_asyncio.fixture()
async def client(db_session, redis_client):
    """
    httpx AsyncClient pointing at the FastAPI app.
    DB and Redis dependencies are overridden with test doubles.
    """
    from app.main import create_app

    app = create_app()

    async def _override_db():
        yield db_session

    def _override_redis():
        return redis_client

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_redis_client] = _override_redis

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
