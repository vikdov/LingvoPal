# backend/app/services/email_change_service.py
"""
Email change token lifecycle — Redis only, no DB access.

Redis key schema:
  email_change:{token}          → "{user_id}|{new_email}"  (TTL 24h)
  email_change_user:{user_id}   → token                    (TTL 24h)
"""

import secrets

import redis.asyncio as aioredis

from app.core.exceptions import EmailChangeTokenInvalidError

TOKEN_TTL = 86400  # 24 hours

# Atomically invalidates old token and stores new one.
# KEYS[1] = email_change_user:{user_id}
# KEYS[2] = email_change:{new_token}
# ARGV[1] = TTL seconds
# ARGV[2] = "{user_id}|{new_email}" (stored under token key)
# ARGV[3] = new token (stored under user key)
_LUA_GENERATE_TOKEN = """
local old = redis.call('GET', KEYS[1])
if old then
  redis.call('DEL', 'email_change:' .. old)
end
redis.call('SETEX', KEYS[2], ARGV[1], ARGV[2])
redis.call('SETEX', KEYS[1], ARGV[1], ARGV[3])
return 1
"""


class EmailChangeService:
    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    async def generate_token(self, user_id: int, new_email: str) -> str:
        """Generate email change token. Atomically invalidates any prior pending token."""
        token = secrets.token_urlsafe(32)
        await self._redis.eval(
            _LUA_GENERATE_TOKEN,
            2,
            f"email_change_user:{user_id}",  # KEYS[1]
            f"email_change:{token}",  # KEYS[2]
            TOKEN_TTL,  # ARGV[1]
            f"{user_id}|{new_email}",  # ARGV[2]
            token,  # ARGV[3]
        )
        return token

    async def consume_token(self, token: str) -> tuple[int, str]:
        """
        Atomically get-and-delete token. Returns (user_id, new_email).
        Raises EmailChangeTokenInvalidError if missing or expired.
        """
        val = await self._redis.getdel(f"email_change:{token}")
        if not val:
            raise EmailChangeTokenInvalidError()
        val_str = val.decode() if isinstance(val, bytes) else val
        user_id_str, new_email = val_str.split("|", 1)
        user_id = int(user_id_str)
        await self._redis.delete(f"email_change_user:{user_id}")
        return user_id, new_email

    async def cancel_token(self, user_id: int) -> None:
        """Cancel pending email change. Removes both Redis keys."""
        token = await self._redis.getdel(f"email_change_user:{user_id}")
        if token:
            token_str = token.decode() if isinstance(token, bytes) else token
            await self._redis.delete(f"email_change:{token_str}")


__all__ = ["EmailChangeService"]
