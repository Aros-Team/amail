"""Application environment-driven settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven application settings."""

    resend_api_key: str = ""
    resend_webhook_secret: str = ""
    admin_email: str = ""
    api_key: str = ""
    email_provider: str = "resend"
    environment: str = "development"
    version: str = "1.1.0"  # x-release-please-version
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    return Settings()
