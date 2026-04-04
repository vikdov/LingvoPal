# backend/app/core/config.py
"""
Application configuration with environment layering.

Pydantic v2 style with .env file layering.

ENV files loaded in order (later overrides earlier):
1. .env              (base, shared settings)
2. .env.{ENV}        (environment-specific)
3. .env.local        (local machine overrides, gitignored)

IMPORTANT DESIGN DECISION:
- We use os.getenv("ENV") at module level to determine which .env.{ENV} to load
- This is evaluated ONCE when the module loads
- Pydantic then handles all validation and type safety
- We trust Pydantic's core system (no manual setattr, no bypassing validators)
"""

import os
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ✅ Single source of truth: Determine ENV once at module load
env = os.getenv("ENV", "development").lower()


class Settings(BaseSettings):
    """
    Application settings from environment variables.

    All validation happens via Pydantic's standard mechanisms.
    No manual overrides, no bypassing of validators.
    """

    # =====================================================================
    # Environment
    # =====================================================================

    ENV: Literal["development", "staging", "production"] = "development"

    # =====================================================================
    # Database Configuration
    # =====================================================================

    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str

    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # =====================================================================
    # Application Settings
    # =====================================================================

    DEBUG: bool = False
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # =====================================================================
    # API Configuration
    # =====================================================================

    API_TITLE: str = "LingvoPal"
    API_VERSION: str = "1.0.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # =====================================================================
    # Security Settings
    # =====================================================================

    SECRET_KEY: str = Field(
        ...,
        min_length=32,
        description="Secret key for JWT signing (minimum 32 characters)",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # =====================================================================
    # CORS Settings
    # =====================================================================

    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"],
        description="Allowed CORS origins",
    )

    # =====================================================================
    # Pydantic Configuration
    # =====================================================================

    model_config = SettingsConfigDict(
        # ✅ CORRECT: Load files in order, later overrides earlier
        # Module-level 'env' variable determines which .env.{ENV} to load
        env_file=(
            ".env",
            f".env.{env}",
            ".env.local",
        ),
        extra="ignore",
        case_sensitive=True,
    )

    # =====================================================================
    # Field Validators (run automatically by Pydantic)
    # =====================================================================

    @field_validator("ENV", mode="before")
    @classmethod
    def validate_env(cls, v: str) -> str:
        """Normalize ENV to lowercase"""
        return (v or "development").lower()

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Normalize LOG_LEVEL to uppercase"""
        return (v or "INFO").upper()

    # =====================================================================
    # Computed Properties
    # =====================================================================

    @property
    def DATABASE_URL(self) -> str:
        """PostgreSQL async connection string (asyncpg driver)"""
        return (
            f"postgresql+asyncpg://"
            f"{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}"
            f"/{self.DATABASE_NAME}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        """PostgreSQL sync connection string (psycopg2 driver, for migrations)"""
        return (
            f"postgresql://"
            f"{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}"
            f"/{self.DATABASE_NAME}"
        )

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENV == "production"

    @property
    def is_staging(self) -> bool:
        """Check if running in staging"""
        return self.ENV == "staging"

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENV == "development"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance (singleton).

    Caching ensures settings are loaded once and reused.
    """
    return Settings()


settings = get_settings()

__all__ = ["settings", "get_settings"]
