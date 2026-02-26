from os import getenv
from functools import lru_cache


@lru_cache
def get_settings():
    return Settings()


class Settings:
    RESEND_API_KEY: str = getenv("RESEND_API_KEY", "")
    DOMINIO: str = getenv("DOMINIO", "aros.services")
    FORWARD_TO_EMAIL: str = getenv("FORWARD_TO_EMAIL", "jorgity345@gmail.com")
    WEBHOOK_EMAILS: list = ["support", "noreply", "team"]

    @property
    def webhook_allowed_emails(self) -> list[str]:
        return [f"{email}@{self.DOMINIO}" for email in self.WEBHOOK_EMAILS]
