"""Integration tests for POST /api/v1/receive (the Resend webhook endpoint)."""

import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

WEBHOOK_BODY = {
    "type": "email.received",
    "data": {
        "email_id": "em_123",
        "from": "sender@example.com",
        "to": ["support@test.example.com"],
        "subject": "Test Email",
    },
}

VALID_HEADERS = {
    "svix-id": "msg_testid",
    "svix-timestamp": "1700000000",
    "svix-signature": "v1,deadbeef",
}


def _mock_settings() -> MagicMock:
    """Return settings with a fixed webhook signing secret."""
    settings = MagicMock()
    settings.resend_webhook_secret = "whsec_testsecret"
    return settings


def test_receive_webhook_valid_payload_is_processed() -> None:
    """Verify a signature-valid webhook is forwarded to the receiver."""
    verify = MagicMock()
    receiver = MagicMock()
    receiver.receive.return_value = {"status": "forwarded"}

    with (
        patch("app.routes.messages.resend.Webhooks.verify", new=verify),
        patch("app.routes.messages.get_receiver", return_value=receiver),
        patch("app.routes.messages.get_settings", return_value=_mock_settings()),
    ):
        resp = client.post(
            "/api/v1/receive",
            content=json.dumps(WEBHOOK_BODY),
            headers=VALID_HEADERS,
        )

    assert resp.status_code == 200
    assert resp.json() == {"status": "forwarded"}
    receiver.receive.assert_called_once_with(WEBHOOK_BODY)
    verify.assert_called_once_with(
        {
            "payload": json.dumps(WEBHOOK_BODY),
            "headers": {
                "id": "msg_testid",
                "timestamp": "1700000000",
                "signature": "v1,deadbeef",
            },
            "webhook_secret": "whsec_testsecret",
        }
    )


def test_receive_webhook_missing_headers_returns_400() -> None:
    """Verify a webhook without the Svix headers is rejected."""
    resp = client.post(
        "/api/v1/receive",
        content=json.dumps(WEBHOOK_BODY),
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Missing Svix webhook headers"


def test_receive_webhook_invalid_signature_returns_400() -> None:
    """A failed signature verification is rejected and never reaches the receiver."""
    receiver = MagicMock()

    with (
        patch(
            "app.routes.messages.resend.Webhooks.verify",
            side_effect=ValueError("no matching signature found"),
        ),
        patch("app.routes.messages.get_receiver", return_value=receiver),
        patch("app.routes.messages.get_settings", return_value=_mock_settings()),
    ):
        resp = client.post(
            "/api/v1/receive",
            content=json.dumps(WEBHOOK_BODY),
            headers=VALID_HEADERS,
        )

    assert resp.status_code == 400
    assert resp.json()["detail"] == "Webhook signature verification failed"
    receiver.receive.assert_not_called()


def test_receive_webhook_invalid_payload_returns_400() -> None:
    """A body that verifies but is not valid JSON is rejected as invalid payload."""
    with (
        patch("app.routes.messages.resend.Webhooks.verify", new=MagicMock()),
        patch("app.routes.messages.get_settings", return_value=_mock_settings()),
    ):
        resp = client.post(
            "/api/v1/receive",
            content="not-json",
            headers=VALID_HEADERS,
        )

    assert resp.status_code == 400
    assert resp.json()["detail"] == "Invalid webhook payload"


def test_receive_webhook_non_email_received_event_is_ignored() -> None:
    """A non email.received event is passed through and reported as ignored."""
    receiver = MagicMock()
    receiver.receive.return_value = {
        "status": "ignored",
        "reason": "event type not supported",
    }

    body = {"type": "email.sent", "data": {}}

    with (
        patch("app.routes.messages.resend.Webhooks.verify", new=MagicMock()),
        patch("app.routes.messages.get_receiver", return_value=receiver),
        patch("app.routes.messages.get_settings", return_value=_mock_settings()),
    ):
        resp = client.post(
            "/api/v1/receive",
            content=json.dumps(body),
            headers=VALID_HEADERS,
        )

    assert resp.status_code == 200
    assert resp.json() == {
        "status": "ignored",
        "reason": "event type not supported",
    }
    receiver.receive.assert_called_once_with(body)
