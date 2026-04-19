# backend/app/main.py
"""FastAPI application factory with async database lifecycle management"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.database import init_async_session_factory, shutdown_db_engine

settings = get_settings()

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


# ============================================================================
# Lifespan Context Manager (Startup/Shutdown)
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle: startup and shutdown.

    Startup:
    - Initialize async session factory
    - Create database tables (dev only)
    - Start background session sweeper

    Shutdown:
    - Flush all active practice sessions (best-effort)
    - Stop sweeper
    - Dispose DB and Redis connections
    """
    # STARTUP
    logger.info("Starting LingvoPal...")

    try:
        await init_async_session_factory(
            settings.DATABASE_URL,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
        )
        logger.info("Async session factory initialized")
        if settings.DEBUG:
            from app.database import create_all_tables

            logger.warning("Running in DEBUG mode - creating tables")
            await create_all_tables(settings.DATABASE_URL)
            logger.info("Database tables created/verified")
        else:
            logger.info("Production mode - using Alembic migrations")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    # Start session sweeper
    sweeper = None
    try:
        from app.core.redis import get_redis_client
        from app.database.session import get_session
        from app.services.session_sweeper import SessionSweeper

        sweeper = SessionSweeper(db_factory=get_session, redis=get_redis_client())
        sweeper.start()
        logger.info("Session sweeper started")
    except Exception as e:
        logger.warning(f"Session sweeper failed to start: {e}")

    yield  # Application runs here

    # SHUTDOWN
    logger.info("Shutting down LingvoPal...")

    if sweeper is not None:
        try:
            await sweeper.flush_all_active()
        except Exception as e:
            logger.warning(f"Shutdown session flush error: {e}")
        await sweeper.stop()

    try:
        await shutdown_db_engine()
        logger.info("Database engine disposed cleanly")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

    try:
        from app.core.redis import close_redis

        await close_redis()
        logger.info("Redis client closed cleanly")
    except Exception as e:
        logger.error(f"Redis shutdown error: {e}")


# ============================================================================
# FastAPI Application
# ============================================================================


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    app = FastAPI(
        title=settings.API_TITLE,
        description="Spaced repetition language learning platform",
        version=settings.API_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    # ========================================================================
    # Rate Limiting
    # ========================================================================
    from app.core.limiter import limiter

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ========================================================================
    # CORS Middleware
    # ========================================================================
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ========================================================================
    # Health Check Endpoint
    # ========================================================================
    @app.get("/health", tags=["system"])
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "ok",
            "app": settings.API_TITLE,
            "version": settings.API_VERSION,
            "debug": settings.DEBUG,
        }

    # ========================================================================
    # Include Routers
    # ========================================================================
    from app.routes.admin import router as admin_router
    from app.routes.auth import router as auth_router
    from app.routes.items import items_router, set_items_router
    from app.routes.languages import router as languages_router
    from app.routes.moderation import router as moderation_router
    from app.routes.practice import router as practice_router
    from app.routes.sets import router as sets_router
    from app.routes.stats import router as stats_router
    from app.routes.user_settings import router as user_settings_router
    from app.routes.users import router as users_router

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(languages_router, prefix="/api/v1")
    app.include_router(sets_router, prefix="/api/v1")
    app.include_router(items_router, prefix="/api/v1")
    app.include_router(set_items_router, prefix="/api/v1")
    app.include_router(moderation_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")
    app.include_router(user_settings_router, prefix="/api/v1")
    app.include_router(stats_router, prefix="/api/v1")
    app.include_router(practice_router, prefix="/api/v1")

    # Serve uploaded images
    upload_dir = Path("static/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory="static"), name="static")

    return app


# ============================================================================
# Application Instance
# ============================================================================

app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
