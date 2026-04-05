# backend/app/main.py
"""FastAPI application factory with async database lifecycle management"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database import (
    init_async_session_factory,
    shutdown_db_engine,
    create_all_tables,
)

# Configure logging
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

    Shutdown:
    - Dispose of all database connections cleanly
    """
    # STARTUP
    logger.info("🚀 Starting LingvoPal...")

    try:
        # Initialize async session factory
        await init_async_session_factory(
            settings.DATABASE_URL,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
        )
        logger.info("✅ Async session factory initialized")

        # Create tables (development only)
        # In production: use Alembic migrations
        if settings.DEBUG:
            logger.warning("⚠️  Running in DEBUG mode - creating tables")
            await create_all_tables(settings.DATABASE_URL)
            logger.info("✅ Database tables created/verified")
        else:
            logger.info("ℹ️  Production mode - using Alembic migrations")

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

    yield  # Application runs here

    # SHUTDOWN
    logger.info("🛑 Shutting down LingvoPal...")
    try:
        await shutdown_db_engine()
        logger.info("✅ Database engine disposed cleanly")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")


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
    # Include Routers (add as you build them)
    # ========================================================================
    # from app.routes import auth_router, items_router, practice_router
    # app.include_router(auth_router, prefix="/api/v1")
    # app.include_router(items_router, prefix="/api/v1")
    # app.include_router(practice_router, prefix="/api/v1")

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
