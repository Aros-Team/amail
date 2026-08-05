"""Resend provider wiring sender and receiver together."""

from app.providers.base import EmailProvider
from app.providers.resend.receiver import ResendReceiver
from app.providers.resend.sender import ResendSender


class ResendProvider(EmailProvider):
    """Concrete email provider backed by the Resend API."""

    name = "resend"

    def __init__(self) -> None:
        self.sender = ResendSender()
        self.receiver = ResendReceiver(sender=self.sender)
