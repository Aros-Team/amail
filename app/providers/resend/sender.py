import resend
from app.config import get_settings


class ResendSender:
    def __init__(self) -> None:
        settings = get_settings()
        resend.api_key = settings.RESEND_API_KEY
        self.settings = settings

    def send(self, to: str, subject: str, html: str) -> str:
        from_email = f"noreply@{self.settings.DOMAIN}"

        params = {
            "from": from_email,
            "to": [to],
            "subject": subject,
            "html": html,
        }

        response = resend.emails.send(params)
        return response.get("id", "")


def get_resend_sender() -> ResendSender:
    return ResendSender()
