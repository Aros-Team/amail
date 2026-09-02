"""Tests for HTML sanitization in batch reports and webhook forwards."""

from unittest.mock import MagicMock, patch

import pytest

from amail.models.schemas import EmailResponse

# --- Batch report escaping ---


def test_batch_report_escapes_html_in_error_message() -> None:
    """Verify build_failure_report escapes script tags in error messages."""
    from amail.services.batch_reporter import build_failure_report

    response = EmailResponse(
        success=False,
        message="<script>alert('xss')</script>",
        to="user@example.com",
    )
    html = build_failure_report([response])

    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_batch_report_escapes_html_in_recipient() -> None:
    """Verify build_failure_report escapes HTML in recipient address."""
    from amail.services.batch_reporter import build_failure_report

    response = EmailResponse(
        success=False,
        message="Error",
        to="<img src=x onerror=alert(1)>@example.com",
    )
    html = build_failure_report([response])

    assert "<img" not in html
    assert "&lt;img" in html


def test_batch_report_with_none_recipient() -> None:
    """Verify build_failure_report renders N/A when recipient is None."""
    from amail.services.batch_reporter import build_failure_report

    response = EmailResponse(success=False, message="Error", to=None)
    html = build_failure_report([response])

    assert "N/A" in html
    assert "<script>" not in html


# --- Webhook forward escaping ---


@pytest.fixture
def mock_settings() -> MagicMock:
    """Create a mocked Settings object with known values."""
    settings = MagicMock()
    settings.resend_api_key = "re_test_key"
    settings.resend_webhook_secret = "whsec_test"
    settings.admin_email = "admin@test.example.com"
    settings.email_provider = "resend"
    settings.environment = "test"
    settings.version = "1.0.0"
    settings.log_level = "INFO"
    return settings


@pytest.fixture
def mock_sender() -> MagicMock:
    """Create a mocked sender whose send returns a fixed id."""
    sender = MagicMock()
    sender.send = MagicMock(return_value={"id": "sent_123"})
    return sender


def test_webhook_forward_escapes_from_email(
    mock_settings: MagicMock, mock_sender: MagicMock
) -> None:
    """Verify receive() escapes HTML in from_email within the forwarded subject."""
    from amail.config.routing import InboundRule, RoutingConfig
    from amail.providers.resend.receiver import ResendReceiver

    routing = RoutingConfig(
        domain="test.example.com",
        inbound=[InboundRule(to="support", forwards=["ops@example.com"])],
    )
    payload = {
        "type": "email.received",
        "data": {
            "email_id": "em_123",
            "from": "<script>alert(1)</script>@evil.com",
            "to": ["support@test.example.com"],
            "subject": "Normal Subject",
        },
    }

    with (
        patch(
            "amail.providers.resend.receiver.get_settings",
            return_value=mock_settings,
        ),
        patch(
            "amail.providers.resend.receiver.ResendSender",
            return_value=mock_sender,
        ),
        patch(
            "amail.providers.resend.receiver.load_routing_config",
            return_value=routing,
        ),
    ):
        receiver = ResendReceiver()
        receiver.receive(payload)

    call = mock_sender.send.call_args
    forwarded_subject = call.kwargs["subject"]
    assert "<script>" not in forwarded_subject
    assert "&lt;script&gt;" in forwarded_subject


def test_webhook_forward_escapes_subject(
    mock_settings: MagicMock, mock_sender: MagicMock
) -> None:
    """Verify receive() escapes HTML in subject within the forwarded subject."""
    from amail.config.routing import InboundRule, RoutingConfig
    from amail.providers.resend.receiver import ResendReceiver

    routing = RoutingConfig(
        domain="test.example.com",
        inbound=[InboundRule(to="support", forwards=["ops@example.com"])],
    )
    payload = {
        "type": "email.received",
        "data": {
            "email_id": "em_123",
            "from": "sender@example.com",
            "to": ["support@test.example.com"],
            "subject": "<img src=x onerror=alert(1)>",
        },
    }

    with (
        patch(
            "amail.providers.resend.receiver.get_settings",
            return_value=mock_settings,
        ),
        patch(
            "amail.providers.resend.receiver.ResendSender",
            return_value=mock_sender,
        ),
        patch(
            "amail.providers.resend.receiver.load_routing_config",
            return_value=routing,
        ),
    ):
        receiver = ResendReceiver()
        receiver.receive(payload)

    call = mock_sender.send.call_args
    forwarded_subject = call.kwargs["subject"]
    assert "<img" not in forwarded_subject
    assert "&lt;img" in forwarded_subject
