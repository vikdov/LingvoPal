# backend/app/core/config.py
# Application configuration with proper environment loading and security.
#
# Architecture:
# 1. Resolve project root using docker-compose.yml as anchor (not fragile depth)
# 2. Load .env file from project root (canonical single source of truth)
# 3. Parse ENV variable from that file reliably
# 4. Construct env_file tuple dynamically based on actual ENV value
# 5. Pydantic loads in correct order with proper precedence
# 6. DATABASE_URL is URL-encoded to handle special characters safely
# 7. Production settings are strictly validated (CORS, SECRET_KEY entropy)

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Literal
import urllib.parse

from dotenv import dotenv_values
from pydantic import Field, field_validator, computed_field, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


def _resolve_project_root() -> Path:
    """
    Resolve the project root directory by walking up until docker-compose.yml is found.

    This approach survives directory restructuring and is self-documenting.
    docker-compose.yml is always at the project root by convention.

    Returns:
        Path object pointing to project root (LingvoPal/)

    Raises:
        RuntimeError: If docker-compose.yml cannot be found (broken project structure)
    """
    current = Path(__file__).resolve()

    # Walk up the directory tree looking for docker-compose.yml
    for parent in current.parents:
        if (parent / "docker-compose.yml").exists():
            return parent

    # If we get here, the project structure is broken
    raise RuntimeError(
        f"Could not find project root from {current}. "
        f"Looked for docker-compose.yml in parent directories. "
        f"This indicates a broken project structure."
    )


def _get_env_variable() -> str:
    """
    Reliably determine the ENV variable by parsing the root .env file first.

    This solves the bootstrapping problem where ENV might be defined in .env
    but not yet exported to the shell environment. By reading the file directly,
    we get the canonical value.

    Returns:
        The ENV value (development, staging, or production)
    """
    try:
        project_root = _resolve_project_root()
        root_env_path = project_root / ".env"

        # Try to read from root .env first (reliable, canonical source)
        if root_env_path.exists():
            env_dict = dotenv_values(root_env_path)
            # Use 'or' to catch both None and empty strings ""
            env_value = env_dict.get("ENV") or "development"
            return env_value.lower()
    except RuntimeError as e:
        # Project structure is broken (docker-compose.yml not found); fall back to system environment
        logging.getLogger(__name__).warning(
            "Could not resolve project root: %s. Falling back to system environment.", e
        )

    # Fallback to system environment (less reliable, but works in CI/CD)
    sys_env = os.getenv("ENV") or "development"
    return sys_env.lower()


def _get_env_files() -> tuple[str, ...]:
    """
    Construct the env_file tuple based on the actual ENV variable.

    Files are loaded in order (later overrides earlier):
    1. .env                 (base, from root - canonical single source of truth)
    2. .env.{ENV}          (environment-specific overrides)
    3. .env.local          (personal machine overrides - highest priority)

    Only files that exist are included in the tuple.

    Returns:
        Tuple of env file paths to load (Pydantic will load in order)
    """
    try:
        env_value = _get_env_variable()
        project_root = _resolve_project_root()
    except RuntimeError:
        # If we can't resolve project root, return empty tuple
        # Pydantic will fall back to system environment
        return tuple()

    files = []

    # Base .env in root (SINGLE SOURCE OF TRUTH)
    base_env = project_root / ".env"
    if base_env.exists():
        files.append(str(base_env))

    # Environment-specific overrides (development, staging, production)
    env_specific = project_root / f".env.{env_value}"
    if env_specific.exists():
        files.append(str(env_specific))

    # Personal local overrides (highest priority, git-ignored)
    local_env = project_root / ".env.local"
    if local_env.exists():
        files.append(str(local_env))

    return tuple(files)


class Settings(BaseSettings):
    """
    Application settings from environment variables.

    Database URL is URL-encoded to handle special characters in passwords.
    Production settings are strictly validated.
    All validation happens via Pydantic's standard mechanisms.
    """

    # =====================================================================
    # Environment
    # =====================================================================

    ENV: Literal["development", "staging", "production"] = "development"

    # =====================================================================
    # Database Configuration
    # =====================================================================
    # Can come from root .env, .env.{ENV}, or .env.local
    # setup.sh or local development can override DATABASE_HOST

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
    # Security Settings (STRICTLY VALIDATED IN PRODUCTION)
    # =====================================================================

    SECRET_KEY: str = Field(
        ...,
        min_length=32,
        description="Secret key for JWT signing (minimum 32 characters, must have entropy)",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # =====================================================================
    # CORS Settings (STRICTLY VALIDATED IN PRODUCTION)
    # =====================================================================

    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"],
        description="Allowed CORS origins (wildcard not allowed in production)",
    )

    # =====================================================================
    # Redis (Optional)
    # =====================================================================

    REDIS_URL: str = "redis://redis:6379/0"

    # =====================================================================
    # Pydantic Configuration
    # =====================================================================

    model_config = SettingsConfigDict(
        # Dynamically construct env_file list based on actual ENV value
        # Uses docker-compose.yml anchor for reliable root detection
        env_file=_get_env_files(),
        extra="ignore",
        case_sensitive=True,
    )

    # =====================================================================
    # Field Validators
    # =====================================================================

    @field_validator("ENV", mode="before")
    @classmethod
    def validate_env(cls, v: str) -> str:
        """Normalize ENV to lowercase"""
        if not v:
            return "development"
        return v.lower()

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Normalize LOG_LEVEL to uppercase"""
        if not v:
            return "INFO"
        return v.upper()

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info: ValidationInfo) -> str:
        """
        Validate SECRET_KEY has sufficient entropy.

        In production, prevent copy-paste placeholder values.
        Check that key has reasonable character variety (at least 10 unique chars).
        """
        env = info.data.get("ENV", "development")

        # Development: more lenient (for testing)
        if env != "production":
            return v

        # Production: strictly validate entropy
        unique_chars = len(set(v))
        if unique_chars < 10:
            raise ValueError(
                f"SECRET_KEY in production must have sufficient entropy. "
                f"Found {unique_chars} unique characters, minimum is 10. "
                f'Generate with: python -c "import secrets; '
                f'print(secrets.token_urlsafe(32))"'
            )

        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """
        Parse CORS origins from a comma-separated string or list.
        Allows `.env` to use: CORS_ORIGINS="http://localhost,https://example.com"
        """
        if isinstance(v, str):
            # Strip whitespace and ignore empty strings
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def validate_cors_origins_safety(
        cls, v: list[str], info: ValidationInfo
    ) -> list[str]:
        """
        Validate CORS origins are safe for the environment.
        In production, reject wildcard and localhost.
        """
        env = info.data.get("ENV", "development")

        if env != "production":
            return v

        if "*" in v:
            raise ValueError(
                "Wildcard CORS origin '*' is not allowed in production. "
                "Specify exact domains: ['https://example.com']"
            )

        for origin in v:
            if "localhost" in origin or "127.0.0.1" in origin:
                raise ValueError(
                    f"Localhost origin '{origin}' not allowed in production. "
                    f"Use production domain instead."
                )

        return v

    @field_validator("DEBUG")
    @classmethod
    def validate_debug(cls, v: bool, info: ValidationInfo) -> bool:
        """
        Enforce DEBUG=False in production.

        DEBUG=True exposes sensitive information and must never be enabled
        in production, even accidentally.
        """
        env = info.data.get("ENV", "development")

        if env == "production" and v is True:
            raise ValueError(
                "DEBUG must be False in production. "
                "Debug mode exposes sensitive information."
            )

        return v

    # =====================================================================
    # Computed Properties (Auto-generated, never duplicated)
    # =====================================================================

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """
        Auto-generated PostgreSQL async connection string (asyncpg driver).

        PASSWORD IS URL-ENCODED to handle special characters safely.

        This prevents sqlalchemy parsing errors with passwords containing
        special characters like @, /, ?, #, %, etc.

        Example:
            password="p@ss#word" becomes "p%40ss%23word" in URL
        """
        safe_password = urllib.parse.quote_plus(self.DATABASE_PASSWORD)
        safe_user = urllib.parse.quote_plus(self.DATABASE_USER)

        return (
            f"postgresql+asyncpg://"
            f"{safe_user}:{safe_password}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}"
            f"/{self.DATABASE_NAME}"
        )

    @computed_field
    @property
    def DATABASE_URL_SYNC(self) -> str:
        """
        Auto-generated PostgreSQL sync connection string (psycopg2 driver).
        Used by Alembic migrations.

        PASSWORD IS URL-ENCODED for safety.

        Note: If using async migrations with asyncpg, ensure alembic/env.py
        is configured for async execution with proper asyncio runner.
        """
        safe_password = urllib.parse.quote_plus(self.DATABASE_PASSWORD)
        safe_user = urllib.parse.quote_plus(self.DATABASE_USER)

        return (
            f"postgresql://"
            f"{safe_user}:{safe_password}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}"
            f"/{self.DATABASE_NAME}"
        )

    @computed_field
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENV == "production"

    @computed_field
    @property
    def is_staging(self) -> bool:
        """Check if running in staging"""
        return self.ENV == "staging"

    @computed_field
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENV == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get cached settings instance (singleton).

    Caching ensures settings are loaded once and reused throughout app lifecycle.

    For testing: Use get_settings.cache_clear() to reset cache between tests.

    Example in tests:
        from app.core.config import get_settings

        @pytest.fixture
        def clear_settings_cache():
            get_settings.cache_clear()
            yield
            get_settings.cache_clear()
    """
    return Settings()


__all__ = ["get_settings"]
