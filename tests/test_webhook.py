from unittest.mock import MagicMock, patch

import pytest

from amail.config.routing import Fallback, InboundRule, RoutingConfig
from amail.providers.resend.receiver import ResendReceiver


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


@pytest.fixture
def receiver(mock_settings: MagicMock, mock_sender: MagicMock) -> ResendReceiver:
    """Build a ResendReceiver with patched settings and sender."""
    with (
        patch(
            "amail.providers.resend.receiver.get_settings",
            return_value=mock_settings,
        ),
        patch(
            "amail.providers.resend.receiver.ResendSender",
            return_value=mock_sender,
        ),
    ):
        r = ResendReceiver()
        r.settings = mock_settings
        r.sender = mock_sender
        return r


def test_resend_receiver_forwards_to_all_matched_targets(
    receiver: ResendReceiver, mock_sender: MagicMock
) -> None:
    """Verify an accepted email is forwarded to all rule targets."""
    routing = RoutingConfig(
        domain="test.example.com",
        inbound=[
            InboundRule(
                to="support@test.example.com",
                forwards=["one@example.com", "two@example.com"],
            )
        ],
    )
    payload = {
        "type": "email.received",
        "data": {
            "email_id": "em_123",
            "from": "sender@example.com",
            "to": ["support@test.example.com"],
            "subject": "Test Email",
        },
    }

    with (
        patch(
            "amail.providers.resend.receiver.load_routing_config", return_value=routing
        ),
        patch.object(
            receiver, "_get_email_content", return_value="<p>Test content</p>"
        ),
    ):
        result = receiver.receive(payload)

    assert result["status"] == "forwarded"
    assert result["forwarded_to"] == ["one@example.com", "two@example.com"]
    call = mock_sender.send.call_args
    assert call.kwargs["to"] == ["one@example.com", "two@example.com"]
    assert call.kwargs["subject"] == "FWD: Test Email (from: sender@example.com)"


def test_resend_receiver_forwards_fallback_targets_for_non_accepted_address(
    receiver: ResendReceiver, mock_sender: MagicMock
) -> None:
    """Verify email to an un-routed address hits fallback forwards."""
    routing = RoutingConfig(
        domain="test.example.com",
        inbound=[
            InboundRule(to="support@test.example.com", forwards=["a@example.com"])
        ],
        fallback=Fallback(forwards=["ops@example.com", "backup@example.com"]),
    )
    payload = {
        "type": "email.received",
        "data": {
            "email_id": "em_123",
            "from": "sender@example.com",
            "to": ["random@test.example.com"],
            "subject": "Test Email",
        },
    }

    with (
        patch(
            "amail.providers.resend.receiver.load_routing_config", return_value=routing
        ),
        patch.object(
            receiver, "_get_email_content", return_value="<p>Test content</p>"
        ),
    ):
        result = receiver.receive(payload)

    assert result["status"] == "forwarded"
    assert result["forwarded_to"] == ["ops@example.com", "backup@example.com"]
    call = mock_sender.send.call_args
    assert call.kwargs["to"] == ["ops@example.com", "backup@example.com"]
    assert call.kwargs["subject"] == "FWD: Test Email (from: sender@example.com)"


def test_resend_receiver_ignores_non_email_received_events(
    receiver: ResendReceiver, mock_sender: MagicMock
) -> None:
    """Verify unsupported event types are ignored."""
    payload = {"type": "email.sent", "data": {}}

    result = receiver.receive(payload)

    assert result["status"] == "ignored"
    assert result["reason"] == "event type not supported"
    mock_sender.send.assert_not_called()


def test_resend_receiver_ignores_email_to_non_accepted_address_with_empty_fallback(
    receiver: ResendReceiver, mock_sender: MagicMock
) -> None:
    """Verify emails to un-routed addresses with an empty fallback are ignored."""
    routing = RoutingConfig(
        domain="test.example.com",
        inbound=[
            InboundRule(to="support@test.example.com", forwards=["a@example.com"])
        ],
    )
    payload = {
        "type": "email.received",
        "data": {
            "email_id": "em_123",
            "from": "sender@example.com",
            "to": ["random@test.example.com"],
            "subject": "Test Email",
        },
    }

    with patch(
        "amail.providers.resend.receiver.load_routing_config", return_value=routing
    ):
        result = receiver.receive(payload)

    assert result["status"] == "ignored"
    assert result["reason"] == "no forward targets"
    mock_sender.send.assert_not_called()


def test_resend_receiver_ignored_when_no_forward_targets(
    receiver: ResendReceiver, mock_sender: MagicMock
) -> None:
    """Verify an accepted email with no resolved forwards is ignored."""
    routing = RoutingConfig(
        domain="test.example.com",
        inbound=[InboundRule(to="support@test.example.com", forwards=[])],
    )
    payload = {
        "type": "email.received",
        "data": {
            "email_id": "em_123",
            "from": "sender@example.com",
            "to": ["support@test.example.com"],
            "subject": "Test Email",
        },
    }

    with patch(
        "amail.providers.resend.receiver.load_routing_config", return_value=routing
    ):
        result = receiver.receive(payload)

    assert result["status"] == "ignored"
    assert result["reason"] == "no forward targets"
    mock_sender.send.assert_not_called()


def test_resend_receiver_returns_error_when_routing_missing(
    receiver: ResendReceiver, mock_sender: MagicMock
) -> None:
    """Verify the receiver reports an error when the routing contract is absent."""
    payload = {
        "type": "email.received",
        "data": {
            "email_id": "em_123",
            "from": "sender@example.com",
            "to": ["support@test.example.com"],
            "subject": "Test Email",
        },
    }

    with patch(
        "amail.providers.resend.receiver.load_routing_config", return_value=None
    ):
        result = receiver.receive(payload)

    assert result["status"] == "error"
    assert result["reason"] == "routing config missing"
    mock_sender.send.assert_not_called()
