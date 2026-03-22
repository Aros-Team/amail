from os import getenv
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


@lru_cache
def get_settings():
    return Settings()


class Settings:
    RESEND_API_KEY: str = getenv("RESEND_API_KEY", "")
    DOMAIN: str = getenv("DOMAIN", "aros.services")
    FORWARD_TO_EMAIL: str = getenv("FORWARD_TO_EMAIL", "jorgity345@gmail.com")
    WEBHOOK_EMAILS: list = ["support", "noreply", "team"]
    ENVIRONMENT: str = getenv("ENVIRONMENT", "development")
    VERSION: str = getenv("VERSION", "1.0.0")
    LOG_LEVEL: str = getenv("LOG_LEVEL", "INFO")

    @property
    def webhook_allowed_emails(self) -> list[str]:
        return [f"{email}@{self.DOMAIN}" for email in self.WEBHOOK_EMAILS]
