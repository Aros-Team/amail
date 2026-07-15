from os import getenv
from functools import lru_cache
from dotenv import load_dotenv
import logging

load_dotenv()

# Stdlib logger for config validation errors
logger = logging.getLogger(__name__)


@lru_cache
def get_settings():
    return Settings()


class Settings:
    RESEND_API_KEY: str = getenv("RESEND_API_KEY", "")
    RESEND_WEBHOOK_SECRET: str = getenv("RESEND_WEBHOOK_SECRET", "")
    DOMAIN: str = getenv("DOMAIN")
    FORWARD_TO_EMAIL: str = getenv("FORWARD_TO_EMAIL", "jorgity345@gmail.com")
    WEBHOOK_EMAILS: list = ["support", "noreply", "team"]
    ENVIRONMENT: str = getenv("ENVIRONMENT", "development")
    VERSION: str = getenv("VERSION", "1.0.0")
    LOG_LEVEL: str = getenv("LOG_LEVEL", "INFO")

    _forward_to_email_override: str | None = None

    def __init__(self) -> None:
        self._validate_required_env_vars()

    def _validate_required_env_vars(self) -> None:
        missing = []
        if not self.RESEND_API_KEY:
            missing.append("RESEND_API_KEY")
        if not self.DOMAIN:
            missing.append("DOMAIN")
        if not self.RESEND_WEBHOOK_SECRET:
            missing.append("RESEND_WEBHOOK_SECRET")
        for var in missing:
            logger.error(f"Missing required environment variable: {var}")

    @property
    def webhook_allowed_emails(self) -> list[str]:
        return [f"{email}@{self.DOMAIN}" for email in self.WEBHOOK_EMAILS]

    @property
    def forward_to_email(self) -> str:
        return self._forward_to_email_override or self.FORWARD_TO_EMAIL

    def set_forward_to_email(self, email: str) -> None:
        self._forward_to_email_override = email
        logger.info("forward_to_email_updated", new_email=email)
