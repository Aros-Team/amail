"""In-memory mock email provider for development and tests."""

import uuid
from typing import Any

from amail.logging_config import get_logger
from amail.providers.base import EmailProvider

log = get_logger(__name__)


class MockSender:
    """Mock email sender that never performs a network call."""

    def send(
        self,
        to: list[str],
        subject: str,
        html: str | None = None,
        text: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Simulate sending an email and return a mock result."""
        email_id = f"mock_{uuid.uuid4().hex[:12]}"
        body = text if text is not None else html
        log.info(
            "mock_send",
            to=to,
            subject=subject[:80],
            email_id=email_id,
            body=body[:80] if body else "",
            options=options,
        )
        return {"id": email_id, "request_id": str(uuid.uuid4())}


class MockReceiver:
    """Mock email receiver that answers without external services."""

    def receive(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Simulate processing an inbound email event."""
        event_type = payload.get("type")
        log.info("mock_receive", event_type=event_type)
        if event_type == "email.received":
            return {"status": "forwarded", "mock": True}
        return {"status": "ignored", "reason": "event type not supported", "mock": True}


class MockProvider(EmailProvider):
    """Provider wiring the mock sender and receiver together."""

    name = "mock"
    sender = MockSender()
    receiver = MockReceiver()
