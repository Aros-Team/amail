from app.providers.base import EmailProvider
from app.providers.resend.sender import ResendSender
from app.providers.resend.receiver import ResendReceiver


class ResendProvider(EmailProvider):
    name = "resend"

    def __init__(self) -> None:
        self.sender = ResendSender()
        self.receiver = ResendReceiver(sender=self.sender)
