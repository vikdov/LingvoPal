import logging

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def get_limiter_storage() -> str:
    settings = get_settings()
    # Always use Redis. In production a missing Redis is caught by the startup
    # health check (main.py lifespan). In development, Redis is expected via
    # docker-compose; if absent, slowapi will fail at the first rate-limited
    # request with a clear error rather than silently falling back to in-memory
    # (which would not work across workers anyway).
    return settings.REDIS_URL


def user_or_ip_identifier(request: Request) -> str:
    """
    Key by authenticated user ID when available, else remote IP.
    User keying requires middleware to populate request.state.user.
    """
    user = getattr(request.state, "user", None)
    if user and hasattr(user, "id"):
        return f"user:{user.id}"
    return get_remote_address(request)


limiter = Limiter(
    key_func=user_or_ip_identifier,
    storage_uri=get_limiter_storage(),
    strategy="moving-window",
    storage_options={"socket_connect_timeout": 1},
)


def auth_rate_limit(limit: str = "5/minute"):
    """Stricter limit for auth routes — brute-force prevention."""
    return limiter.limit(limit)


def global_rate_limit(limit: str = "100/minute"):
    """Standard limit for public/high-traffic endpoints."""
    return limiter.limit(limit)


__all__ = ["limiter", "auth_rate_limit", "global_rate_limit"]
