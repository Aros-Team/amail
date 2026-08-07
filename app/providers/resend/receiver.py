"""Inbound email handling for the Resend provider."""

import time
from typing import Any

import resend

from app.config import get_settings
from app.config.routing import load_routing_config
from app.logging_config import get_logger
from app.providers.resend.sender import ResendSender

log = get_logger(__name__)


class ResendReceiver:
    """Receive Resend webhooks and forward matching emails."""

    def __init__(self, sender: ResendSender | None = None) -> None:
        self.settings = get_settings()
        self.sender = sender or ResendSender()

    def receive(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Process an inbound webhook payload and return the outcome."""
        event_type = payload.get("type")

        if event_type != "email.received":
            return {"status": "ignored", "reason": "event type not supported"}

        email_data = payload.get("data", {})
        from_email = email_data.get("from", "")
        subject = email_data.get("subject", "No subject")
        to_emails = email_data.get("to", [])
        email_id = email_data.get("email_id", "")

        routing = load_routing_config()
        if routing is None:
            return {"status": "error", "reason": "routing config missing"}

        forwards = routing.resolve(to_emails)
        if not forwards:
            return {"status": "ignored", "reason": "no forward targets"}

        log.info("email_content_fetch_start", email_id=email_id)
        html = self._get_email_content(email_id)

        if not html:
            log.warning("email_content_empty", email_id=email_id)
            html = f"<p>Forwarded email from: {from_email}</p><p>Subject: {subject}</p>"

        self.sender.send(
            to=forwards,
            subject=f"FWD: {subject} (from: {from_email})",
            html=html,
        )
        return {"status": "forwarded", "forwarded_to": forwards}

    def _get_email_content(self, email_id: str) -> str | None:
        for attempt in range(3):
            try:
                log.info(
                    "email_content_fetch_retry", attempt=attempt + 1, email_id=email_id
                )
                resend.api_key = self.settings.resend_api_key
                response = resend.Emails.Receiving.get(email_id=email_id)
                log.debug("email_content_response", has_response=response is not None)

                if isinstance(response, dict):
                    email_info = response.get("data") or response
                    content = email_info.get("html") or email_info.get("text")
                    if content:
                        log.info(
                            "email_content_fetched",
                            content_length=len(content),
                            email_id=email_id,
                        )
                        return content
                    log.warning(
                        "email_content_missing_fields",
                        available_keys=list(email_info.keys()) if email_info else [],
                    )
            except Exception as e:
                log.error(
                    "email_content_fetch_exception", error=str(e), email_id=email_id
                )

            if attempt < 2:
                log.info("email_content_retry_wait", attempt=attempt + 1)
                time.sleep(2)

        return None
