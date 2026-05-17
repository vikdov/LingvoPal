# backend/app/services/refresh_token_service.py
"""
Refresh token lifecycle — Redis only, no DB access.

Redis key schema:
  rtoken:{token}        → user_id  (TTL = REFRESH_TOKEN_EXPIRE_DAYS * 86400)
  rtoken_user:{user_id} → token    (TTL = same; used for revocation)

Non-rotating by default: same token stays valid until expiry or explicit revoke.
The /auth/refresh endpoint rotates the token on each use for forward secrecy.
"""

import secrets

import redis.asyncio as aioredis

from app.core.exceptions import RefreshTokenInvalidError

# Atomically replaces any existing token for this user.
# KEYS[1] = rtoken_user:{user_id}
# KEYS[2] = rtoken:{new_token}
# ARGV[1] = TTL seconds
# ARGV[2] = user_id
# ARGV[3] = new_token
_LUA_GENERATE = """
local old = redis.call('GET', KEYS[1])
if old then
  redis.call('DEL', 'rtoken:' .. old)
end
redis.call('SETEX', KEYS[2], ARGV[1], ARGV[2])
redis.call('SETEX', KEYS[1], ARGV[1], ARGV[3])
return 1
"""


class RefreshTokenService:
    def __init__(self, redis: aioredis.Redis, ttl_seconds: int) -> None:
        self._redis = redis
        self._ttl = ttl_seconds

    async def generate(self, user_id: int) -> str:
        """Issue a new refresh token for user_id, revoking any existing one."""
        token = secrets.token_urlsafe(32)
        await self._redis.eval(
            _LUA_GENERATE,
            2,
            f"rtoken_user:{user_id}",
            f"rtoken:{token}",
            self._ttl,
            str(user_id),
            token,
        )
        return token

    async def verify(self, token: str) -> int:
        """
        Verify token exists and return user_id.
        Does NOT consume the token — call rotate() to invalidate old one.
        Raises RefreshTokenInvalidError if missing or expired.
        """
        val = await self._redis.get(f"rtoken:{token}")
        if not val:
            raise RefreshTokenInvalidError()
        return int(val)

    async def rotate(self, user_id: int) -> str:
        """Revoke existing token for user_id and issue a new one."""
        return await self.generate(user_id)

    async def revoke(self, user_id: int) -> None:
        """Revoke the active refresh token for user_id (called on logout)."""
        token = await self._redis.getdel(f"rtoken_user:{user_id}")
        if token:
            raw = token if isinstance(token, str) else token.decode()
            await self._redis.delete(f"rtoken:{raw}")


__all__ = ["RefreshTokenService"]
