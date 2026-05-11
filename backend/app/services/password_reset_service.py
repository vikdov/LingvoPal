# backend/app/services/password_reset_service.py
"""
Password reset token lifecycle — Redis only, no DB access.

Redis key schema:
  password_reset:{token}          → user_id  (TTL 1h)
  password_reset_user:{user_id}   → token    (TTL 1h)
"""

import secrets

import redis.asyncio as aioredis

from app.core.exceptions import PasswordResetTokenInvalidError

TOKEN_TTL = 3600  # 1 hour — short window for security

# Atomically invalidates old token and stores new one.
# KEYS[1] = password_reset_user:{user_id}
# KEYS[2] = password_reset:{new_token}
# ARGV[1] = TTL seconds
# ARGV[2] = user_id (stored under token key)
# ARGV[3] = new token (stored under user key)
_LUA_GENERATE_TOKEN = """
local old = redis.call('GET', KEYS[1])
if old then
  redis.call('DEL', 'password_reset:' .. old)
end
redis.call('SETEX', KEYS[2], ARGV[1], ARGV[2])
redis.call('SETEX', KEYS[1], ARGV[1], ARGV[3])
return 1
"""


class PasswordResetService:
    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    async def generate_token(self, user_id: int) -> str:
        """Generate reset token. Atomically invalidates any prior pending token."""
        token = secrets.token_urlsafe(32)
        await self._redis.eval(
            _LUA_GENERATE_TOKEN,
            2,
            f"password_reset_user:{user_id}",  # KEYS[1]
            f"password_reset:{token}",          # KEYS[2]
            TOKEN_TTL,                          # ARGV[1]
            str(user_id),                       # ARGV[2]
            token,                              # ARGV[3]
        )
        return token

    async def consume_token(self, token: str) -> int:
        """
        Atomically get-and-delete token. Returns user_id.
        Raises PasswordResetTokenInvalidError if missing or expired.
        """
        val = await self._redis.getdel(f"password_reset:{token}")
        if not val:
            raise PasswordResetTokenInvalidError()
        user_id = int(val)
        await self._redis.delete(f"password_reset_user:{user_id}")
        return user_id


__all__ = ["PasswordResetService"]
