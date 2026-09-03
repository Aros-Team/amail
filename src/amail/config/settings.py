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
    version: str = "1.3.2"  # x-release-please-version
    log_level: str = "INFO"
    max_batch_size: int = 25

    # Rate limiting (per-instance, in-memory)
    rate_limit_send_per_sec: int = 10
    rate_limit_send_per_min: int = 60
    rate_limit_receive_per_sec: int = 10
    rate_limit_receive_per_min: int = 60
    rate_limit_health_per_min: int = 300

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    return Settings()
