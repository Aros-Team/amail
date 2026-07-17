import uuid
from typing import Any

from app.providers.base import EmailProvider
from app.logging_config import get_logger

log = get_logger(__name__)


class MockSender:
    def send(
        self,
        to: list[str],
        subject: str,
        html: str,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        email_id = f"mock_{uuid.uuid4().hex[:12]}"
        log.info(
            "mock_send",
            to=to,
            subject=subject[:80],
            email_id=email_id,
            options=options,
        )
        return {"id": email_id, "request_id": str(uuid.uuid4())}


class MockReceiver:
    def receive(self, payload: dict[str, Any]) -> dict[str, Any]:
        event_type = payload.get("type")
        log.info("mock_receive", event_type=event_type)
        if event_type == "email.received":
            return {"status": "forwarded", "mock": True}
        return {"status": "ignored", "reason": "event type not supported", "mock": True}


class MockProvider(EmailProvider):
    name = "mock"
    sender = MockSender()
    receiver = MockReceiver()
