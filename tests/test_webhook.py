import pytest
from unittest.mock import MagicMock, patch

from app.config import Settings
from app.providers.resend.receiver import ResendReceiver


@pytest.fixture
def mock_settings():
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
def mock_sender():
    sender = MagicMock()
    sender.send = MagicMock(return_value={"id": "sent_123"})
    return sender


@pytest.fixture
def receiver(mock_settings, mock_sender):
    with patch(
        "app.providers.resend.receiver.get_settings", return_value=mock_settings
    ):
        with patch(
            "app.providers.resend.receiver.ResendSender", return_value=mock_sender
        ):
            r = ResendReceiver()
            r.settings = mock_settings
            r.sender = mock_sender
            return r


def test_resend_receiver_handles_email_received_event(
    receiver, mock_settings, mock_sender
):
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
    assert "FWD:" in call_args.kwargs["subject"]


def test_resend_receiver_ignores_non_email_received_events(receiver, mock_sender):
    payload = {
        "type": "email.sent",
        "data": {},
    }

    result = receiver.receive(payload)

    assert result["status"] == "ignored"
    assert result["reason"] == "event type not supported"
    mock_sender.send.assert_not_called()


def test_resend_receiver_ignores_emails_to_non_allowed_addresses(receiver, mock_sender):
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
    receiver, mock_settings, mock_sender
):
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


def test_forward_to_email_set_forward_without_email_does_not_crash(
    receiver, mock_settings, mock_sender
):
    payload = {
        "type": "email.received",
        "data": {
            "email_id": "em_123",
            "from": "admin@example.com",
            "to": ["support@test.example.com"],
            "subject": "SET_FORWARD:",
        },
    }

    result = receiver.receive(payload)

    assert result["status"] == "forwarded"
    mock_settings.set_forward_to_email.assert_not_called()


def test_resend_receiver_uses_forward_to_email_property(
    receiver, mock_settings, mock_sender
):
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
