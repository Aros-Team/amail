from app.providers import register
from app.providers.resend.provider import ResendProvider

register("resend", ResendProvider)

__all__ = ["ResendProvider"]
