"""Application configuration settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven application settings."""

    resend_api_key: str = ""
    resend_webhook_secret: str = ""
    domain: str = "aros.services"
    forward_to_email: str = ""
    admin_email: str = ""
    webhook_emails: list[str] = ["support", "noreply", "team"]
    email_provider: str = "resend"
    environment: str = "development"
    version: str = "1.0.0"  # x-release-please-version
    log_level: str = "INFO"

    _forward_to_email_override: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def webhook_allowed_emails(self) -> list[str]:
        """Return the fully-qualified webhook sender email addresses."""
        return [f"{e}@{self.domain}" for e in self.webhook_emails]

    @property
    def effective_forward_to_email(self) -> str:
        """Return the override email if set, else the configured forward address."""
        return self._forward_to_email_override or self.forward_to_email

    def set_forward_to_email(self, email: str) -> None:
        """Override the address that forwards email to the admin."""
        self._forward_to_email_override = email


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    return Settings()
