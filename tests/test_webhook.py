from unittest.mock import MagicMock, patch

import pytest

from app.config import Settings
from app.providers.resend.receiver import ResendReceiver


@pytest.fixture
def mock_settings() -> MagicMock:
    """Create a mocked Settings object with known values."""
    settings = MagicMock(spec=Settings)
    settings.resend_api_key = "re_test_key"
    settings.domain = "test.example.com"
    settings.forward_to_email = "default@example.com"
    settings.webhook_emails = ["support", "noreply", "team"]
    settings.webhook_allowed_emails = [
        "support@test.example.com",
        "noreply@test.example.com",
        "team@test.example.com",
    ]
    settings.effective_forward_to_email = "default@example.com"
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
        patch("app.providers.resend.receiver.get_settings", return_value=mock_settings),
        patch("app.providers.resend.receiver.ResendSender", return_value=mock_sender),
    ):
        r = ResendReceiver()
        r.settings = mock_settings
        r.sender = mock_sender
        return r


def test_resend_receiver_handles_email_received_event(
    receiver: ResendReceiver, mock_settings: MagicMock, mock_sender: MagicMock
) -> None:
    """Verify a received email is forwarded with the expected subject."""
    payload = {
        "type": "email.received",
        "data": {
            "email_id": "em_123",
            "from": "sender@example.com",
            "to": ["support@test.example.com"],
            "subject": "Test Email",
        },
    }

    with patch.object(
        receiver, "_get_email_content", return_value="<p>Test content</p>"
    ):
        result = receiver.receive(payload)

    assert result["status"] == "forwarded"
    mock_sender.send.assert_called_once()
    call_args = mock_sender.send.call_args
    assert call_args.kwargs["to"] == [mock_settings.forward_to_email]
    assert call_args.kwargs["subject"] == "FWD: Test Email (from: sender@example.com)"


def test_resend_receiver_ignores_non_email_received_events(
    receiver: ResendReceiver, mock_sender: MagicMock
) -> None:
    """Verify unsupported event types are ignored."""
    payload = {
        "type": "email.sent",
        "data": {},
    }

    result = receiver.receive(payload)

    assert result["status"] == "ignored"
    assert result["reason"] == "event type not supported"
    mock_sender.send.assert_not_called()


def test_resend_receiver_ignores_emails_to_non_allowed_addresses(
    receiver: ResendReceiver, mock_sender: MagicMock
) -> None:
    """Verify emails to non-allowed addresses are ignored."""
    payload = {
        "type": "email.received",
        "data": {
            "email_id": "em_123",
            "from": "sender@example.com",
            "to": ["random@test.example.com"],
            "subject": "Test Email",
        },
    }

    result = receiver.receive(payload)

    assert result["status"] == "ignored"
    assert result["reason"] == "email not to allowed address"
    mock_sender.send.assert_not_called()


def test_forward_to_email_can_be_updated_via_email_command(
    receiver: ResendReceiver, mock_settings: MagicMock, mock_sender: MagicMock
) -> None:
    """Verify a SET_FORWARD command updates the forward target."""
    payload = {
        "type": "email.received",
        "data": {
            "email_id": "em_123",
            "from": "admin@example.com",
            "to": ["support@test.example.com"],
            "subject": "SET_FORWARD: newtarget@example.com",
        },
    }

    mock_settings.set_forward_to_email = MagicMock()

    result = receiver.receive(payload)

    assert result["status"] == "forward_target_updated"
    assert result["new_email"] == "newtarget@example.com"
    mock_settings.set_forward_to_email.assert_called_once_with("newtarget@example.com")
    mock_sender.send.assert_not_called()


def test_set_forward_without_email_is_forwarded_as_normal_email(
    receiver: ResendReceiver, mock_settings: MagicMock, mock_sender: MagicMock
) -> None:
    """Verify a SET_FORWARD without an address is forwarded as normal email."""
    payload = {
        "type": "email.received",
        "data": {
            "email_id": "em_123",
            "from": "admin@example.com",
            "to": ["support@test.example.com"],
            "subject": "SET_FORWARD:",
        },
    }

    with patch.object(receiver, "_get_email_content", return_value="<p>Content</p>"):
        result = receiver.receive(payload)

    assert result["status"] == "forwarded"
    mock_settings.set_forward_to_email.assert_not_called()
    subject = mock_sender.send.call_args.kwargs["subject"]
    assert subject == "FWD: SET_FORWARD: (from: admin@example.com)"


def test_resend_receiver_uses_forward_to_email_property(
    receiver: ResendReceiver, mock_settings: MagicMock, mock_sender: MagicMock
) -> None:
    """Verify forwarding uses the effective forward-to email property."""
    mock_settings.effective_forward_to_email = "override@example.com"

    payload = {
        "type": "email.received",
        "data": {
            "email_id": "em_123",
            "from": "sender@example.com",
            "to": ["support@test.example.com"],
            "subject": "Normal email",
        },
    }

    with patch.object(receiver, "_get_email_content", return_value="<p>Content</p>"):
        receiver.receive(payload)

    mock_sender.send.assert_called_with(
        to=["override@example.com"],
        subject="FWD: Normal email (from: sender@example.com)",
        html="<p>Content</p>",
    )
