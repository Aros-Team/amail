import resend
from app.config import get_settings
from app.models.schemas import EmailRequest


class ResendClient:
    def __init__(self):
        settings = get_settings()
        resend.api_key = settings.RESEND_API_KEY
        self.settings = settings

    def send_email(self, email_request: EmailRequest, html_content: str) -> dict:
        from_email = f"noreply@{self.settings.DOMINIO}"
        
        params = {
            "from": from_email,
            "to": [email_request.to],
            "subject": email_request.subject,
            "html": html_content,
        }
        
        response = resend.emails.send(params)
        return response

    def forward_email(self, to_email: str, subject: str, html_content: str) -> dict:
        from_email = f"forward@{self.settings.DOMINIO}"
        
        params = {
            "from": from_email,
            "to": [to_email],
            "subject": f"FWD: {subject}",
            "html": html_content,
        }
        
        response = resend.emails.send(params)
        return response


resend_client = ResendClient()
