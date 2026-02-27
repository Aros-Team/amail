from os import getenv
from functools import lru_cache


@lru_cache
def get_settings():
    return Settings()


class Settings:
    RESEND_API_KEY: str = getenv("RESEND_API_KEY", "")
    DOMAIN: str = getenv("DOMAIN", "aros.services")
    FORWARD_TO_EMAIL: str = getenv("FORWARD_TO_EMAIL", "jorgity345@gmail.com")
    WEBHOOK_EMAILS: list = ["support", "noreply", "team"]

    JWT_SECRET_KEY: str = getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_MINUTES: int = int(getenv("JWT_EXPIRATION_MINUTES", "60"))

    @property
    def webhook_allowed_emails(self) -> list[str]:
        return [f"{email}@{self.DOMAIN}" for email in self.WEBHOOK_EMAILS]
