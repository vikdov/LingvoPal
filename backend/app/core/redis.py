# backend/app/core/redis.py
"""
Async Redis client factory for LingvoPal.

Design notes:
  - Uses redis.asyncio for async/await compatibility.
  - The client is created once and reused (connection pool under the hood).
  - Yields the same client instance throughout the app's lifetime.
  - No RedisJSON (Stack) dependency assumed; sessions are stored as JSON strings.
"""

from functools import lru_cache
from typing import AsyncGenerator

import redis.asyncio as aioredis

from app.core.config import get_settings


@lru_cache(maxsize=1)
def _get_redis_client() -> aioredis.Redis:
    """
    Create and cache a single async Redis client for the lifetime of the process.

    The underlying connection pool is initialised lazily on first use.
    Call redis_client.aclose() during shutdown to cleanly drain the pool.
    """
    settings = get_settings()
    return aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """
    FastAPI dependency: yield the shared async Redis client.

    Usage:
        @router.get("/")
        async def handler(redis: aioredis.Redis = Depends(get_redis)):
            await redis.set("key", "value")
    """
    yield _get_redis_client()


async def close_redis() -> None:
    """Close the Redis connection pool (call from lifespan shutdown)."""
    client = _get_redis_client()
    await client.aclose()
    _get_redis_client.cache_clear()


__all__ = ["get_redis", "close_redis"]
