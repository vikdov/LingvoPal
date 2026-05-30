# backend/app/services/email_verification_service.py
"""
Email verification token lifecycle — Redis only, no DB access.

Redis key schema:
  email_verify:{token}              → user_id  (TTL 24h)
  email_verify_user:{user_id}       → token    (TTL 24h)
  email_verify_daily:{user_id}:{date} → count  (TTL until next UTC midnight)
"""

import secrets
from datetime import datetime, timedelta, timezone

import redis.asyncio as aioredis

from app.core.exceptions import VerificationRateLimitedError, VerificationTokenInvalidError

TOKEN_TTL = 86400  # 24 hours
DAILY_CAP = 5

# Atomically invalidates old token and stores new one.
# KEYS[1] = email_verify_user:{user_id}
# KEYS[2] = email_verify:{new_token}
# ARGV[1] = TTL seconds
# ARGV[2] = user_id (stored as value under token key)
# ARGV[3] = new token (stored as value under user key)
_LUA_GENERATE_TOKEN = """
local old = redis.call('GET', KEYS[1])
if old then
  redis.call('DEL', 'email_verify:' .. old)
end
redis.call('SETEX', KEYS[2], ARGV[1], ARGV[2])
redis.call('SETEX', KEYS[1], ARGV[1], ARGV[3])
return 1
"""


class EmailVerificationService:
    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    async def generate_token(self, user_id: int) -> str:
        """
        Generate verification token for user_id.
        Atomically invalidates any previous token via Lua script.
        """
        token = secrets.token_urlsafe(32)
        await self._redis.eval(
            _LUA_GENERATE_TOKEN,
            2,
            f"email_verify_user:{user_id}",  # KEYS[1]
            f"email_verify:{token}",  # KEYS[2]
            TOKEN_TTL,  # ARGV[1]
            str(user_id),  # ARGV[2]
            token,  # ARGV[3]
        )
        return token

    async def consume_token(self, token: str) -> int:
        """
        Atomically get-and-delete token. Returns user_id.
        Raises VerificationTokenInvalidError if token is missing or expired.
        GETDEL guarantees single-use — no race condition.
        """
        val = await self._redis.getdel(f"email_verify:{token}")
        if not val:
            raise VerificationTokenInvalidError()
        user_id = int(val)
        await self._redis.delete(f"email_verify_user:{user_id}")
        return user_id

    async def check_and_increment_daily(self, user_id: int) -> None:
        """
        Increment today's send counter. Raises VerificationRateLimitedError
        if DAILY_CAP exceeded. Counter expires at next UTC midnight.
        """
        now = datetime.now(timezone.utc)
        today = now.date().isoformat()
        key = f"email_verify_daily:{user_id}:{today}"

        count = await self._redis.incr(key)
        if count == 1:
            tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            ttl = int((tomorrow - now).total_seconds())
            await self._redis.expire(key, ttl)

        if count > DAILY_CAP:
            raise VerificationRateLimitedError()


__all__ = ["EmailVerificationService"]
