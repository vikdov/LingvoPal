# backend/app/core/config.py
# Application configuration with proper environment loading and security.
#
# Boot sequence:
# 1. _resolve_project_root() walks parents for docker-compose.yml (called once)
# 2. _get_env_files() reads ENV from .env, constructs ordered file tuple
# 3. Settings.settings_customise_sources() loads files at instantiation time,
#    NOT at module-import time — avoids filesystem work on bare import
# 4. model_validator runs AFTER all fields are resolved — no hidden field-order
#    dependencies for production constraint checks
# 5. DATABASE_URL is URL-encoded to handle special characters safely
import json
import logging
import os
import urllib.parse
from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import dotenv_values
from pydantic import Field, computed_field, field_validator, model_validator
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    SettingsConfigDict,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Boot-time helpers
# =============================================================================


def _resolve_project_root() -> Path:
    """
    Resolve the project root by walking up the directory tree.

    Uses a three-pass strategy with explicit priority:

    Pass 1 — look for docker-compose.yml.
        This is the canonical project root anchor. It lives in LingvoPal/,
        one level above backend/. Finding it means we have the true root where
        the .env file lives.

    Pass 2 — fall back to pyproject.toml only if docker-compose.yml is absent.
        This covers standalone runs (no Docker) or CI pipelines that build
        images directly. In this case pyproject.toml in backend/ is the best
        available anchor, and the .env file is expected there too.

    Pass 3 — fall back to requirements.txt (bare pip / pre-uv baseline).
        This covers the experiment/00-baseline state where neither Docker nor
        uv tooling is present. requirements.txt lives in backend/, which is
        the correct root for .env resolution in that context.

    The passes are intentionally separate — OR-ing the anchors in a single
    pass would stop at pyproject.toml in backend/ before reaching
    docker-compose.yml in the parent, returning the wrong root.

    Returns:
        Path pointing to the project root directory.

    Raises:
        RuntimeError: If no anchor is found anywhere in the tree.
    """
    current = Path(__file__).resolve()
    parents = list(current.parents)

    # Pass 1: prefer docker-compose.yml — true monorepo/project root
    for parent in parents:
        if (parent / "docker-compose.yml").exists():
            return parent

    # Pass 2: fall back to pyproject.toml — backend standalone root
    for parent in parents:
        if (parent / "pyproject.toml").exists():
            return parent

    # Pass 3: fall back to requirements.txt — bare pip / pre-uv baseline
    for parent in parents:
        if (parent / "requirements.txt").exists():
            return parent

    raise RuntimeError(
        f"Could not find project root from {current}. "
        f"Looked for docker-compose.yml, pyproject.toml, then requirements.txt "
        f"in all parent directories. This indicates a broken project structure."
    )


def _read_env_from_file(project_root: Path) -> str:
    """
    Read the ENV variable directly from the root .env file.

    Accepts the project root as a parameter so the caller controls the single
    root-resolution call — avoids redundant filesystem walks.

    Returns:
        Normalised ENV value (lowercase). Defaults to "development".
    """
    root_env_path = project_root / ".env"
    if root_env_path.exists():
        env_dict = dotenv_values(root_env_path)
        # Use 'or' to catch both None and empty string ""
        return (env_dict.get("ENV") or "development").lower()

    # Fallback: system environment (less reliable, works in some CI setups)
    return (os.getenv("ENV") or "development").lower()


def _get_env_files() -> tuple[str, ...]:
    """
    Construct the ordered env_file tuple for pydantic-settings.

    Files are loaded in priority order (later overrides earlier):
      1. .env              — base, canonical single source of truth
      2. .env.{ENV}        — environment-specific overrides
      3. .env.local        — personal machine overrides (git-ignored, highest priority)

    Only files that actually exist are included.

    Returns:
        Tuple of absolute file path strings.
    """
    try:
        project_root = _resolve_project_root()
        env_value = _read_env_from_file(project_root)
    except RuntimeError:
        logger.warning(
            "config: could not resolve project root; "
            "falling back to system environment variables only. "
            "Check that docker-compose.yml or pyproject.toml exists at the project root."
        )
        return tuple()

    candidates = [
        project_root / ".env",
        project_root / f".env.{env_value}",
        project_root / ".env.local",
    ]

    return tuple(str(p) for p in candidates if p.exists())


# =============================================================================
# Settings
# =============================================================================


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env files.

    Production constraints (CORS, SECRET_KEY entropy, DEBUG=False) are enforced
    by a single model_validator that runs after ALL fields are resolved — no
    hidden dependency on field declaration order.

    DATABASE_URL and DATABASE_URL_SYNC are computed properties; never set them
    directly in .env files.
    """

    # =========================================================================
    # Environment
    # =========================================================================

    ENV: Literal["development", "staging", "production"] = "development"

    # =========================================================================
    # Database
    # =========================================================================

    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str

    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # =========================================================================
    # Application
    # =========================================================================

    DEBUG: bool = False
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # =========================================================================
    # API
    # =========================================================================

    API_TITLE: str = "LingvoPal"
    API_VERSION: str = "1.0.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # =========================================================================
    # Security
    # min_length=32 enforces the HMAC-SHA256 minimum key length recommendation.
    # Entropy (unique-char count) is validated separately in production only —
    # see validate_production_constraints.
    # =========================================================================

    SECRET_KEY: str = Field(
        ...,
        min_length=32,
        description=(
            "Secret key for JWT signing. Minimum 32 characters. "
            'Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"'
        ),
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # =========================================================================
    # CORS
    # Accepts a comma-separated string or a JSON array string from .env:
    #   CORS_ORIGINS=http://localhost:5173,https://example.com
    #   CORS_ORIGINS=["http://localhost:5173","https://example.com"]
    # =========================================================================

    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"],
        description="Allowed CORS origins. Wildcard and localhost rejected in production.",
    )

    # =========================================================================
    # Redis
    # REDIS_HOST defaults to the Docker service name.
    # Override to 'localhost' when running the backend outside Docker.
    # =========================================================================

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    # =========================================================================
    # Email / SMTP
    # Dev: Mailpit on :1025 (catches all email, UI at :8025)
    # Prod: swap SMTP_HOST/PORT/USER/PASSWORD/TLS for SendGrid, SES, Resend, etc.
    # =========================================================================

    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@lingvopal.com"
    SMTP_TLS: bool = False

    # Browser-facing frontend URL — used to build verification links in emails.
    FRONTEND_URL: str = "http://localhost:5173"

    # =========================================================================
    # Object Storage (S3-compatible: MinIO locally, R2/S3 in prod)
    #
    # S3_HOST / S3_PORT drive server-to-server connections (backend → MinIO).
    # Override S3_HOST in docker-compose to the container name so the app
    # container can reach MinIO on the Docker network — same pattern as
    # DATABASE_HOST / REDIS_HOST.
    #
    # MEDIA_BASE_URL is the browser-facing URL (always localhost in dev).
    # =========================================================================

    S3_HOST: str = "localhost"
    S3_PORT: int = 9000
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET: str = "lingvopal"
    S3_REGION: str = "us-east-1"

    # Public base URL for media files (browser-accessible).
    # Dev:  http://localhost:9000/lingvopal
    # Prod: https://cdn.example.com  (CDN in front of bucket)
    MEDIA_BASE_URL: str = "http://localhost:9000/lingvopal"

    # =========================================================================
    # Content moderation thresholds — configurable without code change
    # =========================================================================

    # Number of community complaints before a COMMUNITY item is auto-pulled to DRAFT
    COMPLAINT_ESCALATION_THRESHOLD: int = 3

    # Max complaints a single user can file per calendar day (anti-gaming)
    MAX_COMPLAINTS_PER_DAY: int = 5

    # Minimum learner count for OFFICIAL promotion (soft gate, admin can override)
    OFFICIAL_MIN_LEARNERS: int = 20

    # Minimum global success rate for OFFICIAL promotion (soft gate)
    OFFICIAL_MIN_SUCCESS_RATE: float = 0.70

    # =========================================================================
    # AI / LLM (for item suggestions)
    # =========================================================================
    AI_PROVIDER: Literal["google", "groq"] = Field("groq", description="LLM provider: 'groq' or 'google'")
    AI_API_KEY: str = Field(..., description="API key for the selected AI provider")
    AI_MODEL: str = Field("llama-3.3-70b-versatile", description="Model ID (groq: llama-3.3-70b-versatile | google: gemini-2.0-flash-lite)")

    # =========================================================================
    # TTS (Text-to-Speech)
    #
    # google_cloud: set GOOGLE_APPLICATION_CREDENTIALS to the path of the
    #   service account JSON file downloaded from Google Cloud Console.
    #   TTS_API_KEY is ignored.
    #
    # elevenlabs: set TTS_API_KEY to your ElevenLabs API key.
    #   GOOGLE_APPLICATION_CREDENTIALS is ignored.
    # =========================================================================
    TTS_ENABLED: bool = Field(True, description="Set False to skip TTS credential validation and disable TTS features.")
    TTS_PROVIDER: Literal["google_cloud", "elevenlabs"] = "google_cloud"
    GOOGLE_APPLICATION_CREDENTIALS: str | None = Field(
        None,
        description="Path to Google Cloud service account JSON file (google_cloud provider only)",
    )
    TTS_API_KEY: str | None = Field(
        None,
        description="ElevenLabs API key (elevenlabs provider only)",
    )
    TTS_LANGUAGE_CODE: str = "en-US"  # Default; can be overridden per request

    # =========================================================================
    # Image Search
    # =========================================================================
    IMAGE_SEARCH_PROVIDER: Literal["unsplash", "pexels", "pixabay"] = "unsplash"
    IMAGE_SEARCH_API_KEY: str = Field(
        ..., description="API key for image search provider"
    )
    IMAGE_COUNT: int = 1

    @computed_field
    @property
    def S3_ENDPOINT_URL(self) -> str:
        return f"http://{self.S3_HOST}:{self.S3_PORT}"

    # =========================================================================
    # Pydantic configuration
    # env_file is intentionally empty here — file loading is handled by
    # settings_customise_sources() so it happens at instantiation time, not at
    # module-import time. This makes the module safe to import in tests without
    # triggering filesystem side-effects before fixtures run.
    # =========================================================================

    model_config = SettingsConfigDict(
        env_file=(),
        extra="ignore",
        case_sensitive=True,
    )

    # =========================================================================
    # Source customisation — called at Settings() instantiation, not import
    # =========================================================================

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        **kwargs,
    ):
        """
        Load env files in priority order, then layer system env on top.

        Uses **kwargs instead of named parameters so this method is immune to
        pydantic-settings version differences (the parameter was named
        'secrets_settings' in some versions and 'file_secret_settings' in
        others — both are passed as keyword arguments by the framework).

        Priority (first source = highest priority in pydantic-settings):
          system env > .env.local > .env.{ENV} > .env
        """
        env_settings = kwargs["env_settings"]
        env_file_sources = tuple(
            DotEnvSettingsSource(settings_cls, env_file=path)
            for path in _get_env_files()
        )
        # First source wins. System env first, then local overrides, then base.
        return (env_settings, *reversed(env_file_sources))

    # =========================================================================
    # Field validators
    # =========================================================================

    @field_validator("ENV", mode="before")
    @classmethod
    def normalise_env(cls, v: str) -> str:
        return (v or "development").lower()

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def normalise_log_level(cls, v: str) -> str:
        return (v or "INFO").upper()

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """
        Parse CORS origins from:
          - A comma-separated string: "http://a.com,http://b.com"
          - A JSON array string:      '["http://a.com","http://b.com"]'
          - An already-parsed list (pydantic-settings native parsing)
        """
        if isinstance(v, str):
            stripped = v.strip()
            if stripped.startswith("["):
                # JSON array — e.g. from pydantic-settings passing raw env value
                return json.loads(stripped)
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return v

    # =========================================================================
    # Production constraint validation
    #
    # Uses model_validator (runs AFTER all fields are resolved) instead of
    # field_validator so there is no hidden dependency on field declaration
    # order. All production checks are co-located so the full constraint surface
    # is visible in one place.
    # =========================================================================

    @model_validator(mode="after")
    def validate_tts_credentials(self) -> "Settings":
        """Fail fast if TTS provider credentials are missing."""
        if not self.TTS_ENABLED:
            return self
        if self.TTS_PROVIDER == "google_cloud" and not self.GOOGLE_APPLICATION_CREDENTIALS:
            raise ValueError(
                "TTS_PROVIDER=google_cloud requires GOOGLE_APPLICATION_CREDENTIALS "
                "to be set to the path of your service account JSON file.\n"
                "Download it from: Google Cloud Console → IAM → Service Accounts → Keys\n"
                "Set TTS_ENABLED=false to disable TTS entirely."
            )
        if self.TTS_PROVIDER == "elevenlabs" and not self.TTS_API_KEY:
            raise ValueError(
                "TTS_PROVIDER=elevenlabs requires TTS_API_KEY to be set.\n"
                "Set TTS_ENABLED=false to disable TTS entirely."
            )
        return self

    @model_validator(mode="after")
    def validate_production_constraints(self) -> "Settings":
        if self.ENV != "production":
            return self

        # --- SECRET_KEY entropy ---
        unique_chars = len(set(self.SECRET_KEY))
        if unique_chars < 10:
            raise ValueError(
                f"SECRET_KEY in production must have sufficient entropy. "
                f"Found {unique_chars} unique characters, minimum is 10. "
                f'Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"'
            )

        # --- CORS origins ---
        if "*" in self.CORS_ORIGINS:
            raise ValueError(
                "Wildcard CORS origin '*' is not allowed in production. "
                "Specify exact domains: ['https://example.com']"
            )
        for origin in self.CORS_ORIGINS:
            if "localhost" in origin or "127.0.0.1" in origin:
                raise ValueError(
                    f"Localhost origin '{origin}' is not allowed in production. "
                    f"Use your production domain instead."
                )

        # --- DEBUG ---
        if self.DEBUG:
            raise ValueError(
                "DEBUG must be False in production. "
                "Debug mode exposes sensitive information."
            )

        return self

    # =========================================================================
    # Computed fields — database and cache URLs
    #
    # Passwords are URL-encoded to handle special characters (@, /, ?, #, %, …)
    # that would break SQLAlchemy's URL parser if embedded literally.
    # =========================================================================

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """
        Async PostgreSQL connection string (asyncpg driver).
        Used by SQLAlchemy async engine and the application at runtime.
        """
        return self._build_db_url(driver="postgresql+asyncpg")

    @computed_field
    @property
    def DATABASE_URL_SYNC(self) -> str:
        """
        Synchronous PostgreSQL connection string (psycopg2 driver).
        Used by Alembic for synchronous migrations.

        If you want async Alembic migrations, use DATABASE_URL (asyncpg)
        and configure alembic/env.py with an asyncio runner instead.
        """
        return self._build_db_url(driver="postgresql")

    @computed_field
    @property
    def REDIS_URL(self) -> str:
        """Redis connection string. Database index 0."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # =========================================================================
    # Convenience properties — plain @property, not @computed_field.
    #
    # @computed_field would include these in .model_dump() / JSON serialisation,
    # adding noise and leaking internal state to any settings endpoint/log.
    # =========================================================================

    @property
    def is_production(self) -> bool:
        return self.ENV == "production"

    @property
    def is_staging(self) -> bool:
        return self.ENV == "staging"

    @property
    def is_development(self) -> bool:
        return self.ENV == "development"

    # =========================================================================
    # Private helpers
    # =========================================================================

    def _build_db_url(self, *, driver: str) -> str:
        """
        Build a URL-encoded database connection string for the given driver.
        Centralises encoding logic so DATABASE_URL and DATABASE_URL_SYNC
        cannot diverge.
        """
        user = urllib.parse.quote_plus(self.DATABASE_USER)
        password = urllib.parse.quote_plus(self.DATABASE_PASSWORD)
        return (
            f"{driver}://{user}:{password}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}"
            f"/{self.DATABASE_NAME}"
        )


# =============================================================================
# Singleton accessor
# =============================================================================


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached Settings instance (singleton).

    Settings are validated once on first call and reused for the application
    lifetime. The lru_cache means environment variables are read exactly once.

    Testing:
        Call get_settings.cache_clear() before and after each test that needs
        a fresh Settings instance, or use dependency_overrides in FastAPI tests.

        Example pytest fixture:
            @pytest.fixture(autouse=True)
            def clear_settings_cache():
                get_settings.cache_clear()
                yield
                get_settings.cache_clear()
    """
    return Settings()


__all__ = ["get_settings", "Settings"]
