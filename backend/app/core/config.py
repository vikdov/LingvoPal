from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os


ENV = os.getenv("ENV", "development")


class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "LingvoPal"
    DEBUG: bool = False
    ENV: str = "development"

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(
        # LOAD ORDER: .env (base) -> .env.{ENV} (overrides base)
        env_file=(".env", f".env.{ENV}"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
