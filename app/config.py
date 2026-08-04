from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
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
        return [f"{e}@{self.domain}" for e in self.webhook_emails]

    @property
    def effective_forward_to_email(self) -> str:
        return self._forward_to_email_override or self.forward_to_email

    def set_forward_to_email(self, email: str) -> None:
        self._forward_to_email_override = email


@lru_cache
def get_settings() -> Settings:
    return Settings()
