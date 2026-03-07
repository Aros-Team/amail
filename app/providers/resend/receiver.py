from app.config import get_settings
from app.providers.resend.sender import ResendSender
import resend
import time


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
        to_emails = email_data.get("to", [])
        email_id = email_data.get("email_id", "")

        allowed_emails = self.settings.webhook_allowed_emails

        if not any(email in allowed_emails for email in to_emails):
            return {"status": "ignored", "reason": "email not to allowed address"}

        print(f"DEBUG: Getting content for email_id: {email_id}")
        html = self._get_email_content(email_id)

        if not html:
            print("DEBUG: No content found, sending default message")
            html = f"<p>Forwarded email from: {from_email}</p><p>Subject: {subject}</p>"

        self.sender.send(
            to=self.settings.FORWARD_TO_EMAIL,
            subject=f"FWD: {subject} (from: {from_email})",
            html=html,
        )
        return {"status": "forwarded"}

    def _get_email_content(self, email_id: str) -> str | None:
        for attempt in range(3):
            try:
                print(f"DEBUG: Attempt {attempt + 1} to get email content")
                resend.api_key = self.settings.RESEND_API_KEY
                response = resend.Emails.Receiving.get(email_id=email_id)
                print(f"DEBUG: Response keys: {response.keys() if isinstance(response, dict) else 'not dict'}")

                # La SDK de Python devuelve el contenido directamente, no en "data"
                if isinstance(response, dict):
                    email_info = response.get("data") or response
                    content = email_info.get("html") or email_info.get("text")
                    if content:
                        print(f"DEBUG: Got content, length: {len(content)}")
                        return content
                    else:
                        print(f"DEBUG: Response has no html or text field, keys: {email_info.keys()}")
            except Exception as e:
                print(f"DEBUG: Exception: {e}")

            if attempt < 2:
                print("DEBUG: Waiting 2 seconds before retry...")
                time.sleep(2)

        return None


def get_resend_receiver() -> ResendReceiver:
    return ResendReceiver()
