from app.config import get_settings
from app.providers.resend.sender import ResendSender


class ResendReceiver:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.sender = ResendSender()

    def receive(self, payload: dict) -> dict:
        event_type = payload.get("type")

        if event_type != "email.received":
            return {"status": "ignored", "reason": "event type not supported"}

        email_data = payload.get("data", {})
        from_email = email_data.get("from", "")
        subject = email_data.get("subject", "No subject")
        html = email_data.get("html", "")

        allowed_emails = [
            f"{email}@{self.settings.DOMAIN}"
            for email in self.settings.WEBHOOK_EMAILS
        ]

        if from_email not in allowed_emails:
            return {"status": "ignored", "reason": "email not in allowed list"}

        self.sender.send(
            to=self.settings.FORWARD_TO_EMAIL,
            subject=f"FWD: {subject}",
            html=html,
        )
        return {"status": "forwarded"}


def get_resend_receiver() -> ResendReceiver:
    return ResendReceiver()
