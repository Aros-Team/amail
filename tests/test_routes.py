from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from amail.config.routing import RoutingConfig
from amail.main import app

client = TestClient(app)


def test_send_plain_text_body_reaches_sender() -> None:
    """Verify POST /send forwards the plain-text body to the sender as text."""
    sender = MagicMock()
    sender.send_with_retry.return_value = {"id": "mock_id", "request_id": "req_1"}
    provider = MagicMock()
    provider.sender = sender

    with (
        patch("amail.services.email_service.get_provider", return_value=provider),
        patch.dict("os.environ", {"AMAIL_API_KEY": "test-key"}),
    ):
        resp = client.post(
            "/api/v1/send",
            json={"to": "user@example.com", "subject": "Hello", "body": "Plain body"},
            headers={"X-API-Key": "test-key"},
        )

    assert resp.status_code == 200
    sender.send_with_retry.assert_called_once_with(
        to=["user@example.com"],
        subject="Hello",
        text="Plain body",
        options={},
    )


def test_send_failure_returns_500() -> None:
    """Verify POST /send translates a sender failure into a 500."""
    sender = MagicMock()
    sender.send_with_retry.side_effect = Exception("provider down")
    provider = MagicMock()
    provider.sender = sender

    with (
        patch("amail.services.email_service.get_provider", return_value=provider),
        patch.dict("os.environ", {"AMAIL_API_KEY": "test-key"}),
    ):
        resp = client.post(
            "/api/v1/send",
            json={"to": "user@example.com", "subject": "Hello", "body": "Plain body"},
            headers={"X-API-Key": "test-key"},
        )

    assert resp.status_code == 500
    assert resp.json()["detail"] == "provider down"


def test_health_email_missing_domain_is_unhealthy() -> None:
    """Verify /health/email alerts when no domain is in the routing contract."""
    settings = MagicMock()
    settings.resend_api_key = "re_test_key"

    with (
        patch("amail.routes.health.get_settings", return_value=settings),
        patch("amail.routes.health.load_routing_config", return_value=None),
    ):
        resp = client.get("/health/email")

    assert resp.status_code == 503
    body = resp.json()["detail"]
    assert body["status"] == "unhealthy"
    assert "AMAIL_ROUTES" in body["message"]


def test_health_email_with_domain_reaches_provider() -> None:
    """Verify /health/email proceeds and reports healthy when the domain is set."""
    settings = MagicMock()
    settings.resend_api_key = "re_test_key"

    with (
        patch("amail.routes.health.get_settings", return_value=settings),
        patch(
            "amail.routes.health.load_routing_config",
            return_value=RoutingConfig(domain="example.com"),
        ),
        patch(
            "amail.routes.health.resend.Emails.send",
            return_value={"id": "test_id_123"},
        ),
    ):
        resp = client.get("/health/email")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["resend_id"] == "test_id_123"


def test_health_webhook_configured_with_secret_and_routes() -> None:
    """Verify /health/webhook reports configured when secret and routes exist."""
    settings = MagicMock()
    settings.resend_webhook_secret = "whsec_test"

    with (
        patch("amail.routes.health.get_settings", return_value=settings),
        patch(
            "amail.routes.health.load_routing_config",
            return_value=RoutingConfig(domain="example.com"),
        ),
    ):
        resp = client.get("/health/webhook")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "configured"
    assert body["webhook_secret_configured"] is True
    assert body["routes_loaded"] is True


def test_health_webhook_missing_routes() -> None:
    """Verify /health/webhook reports missing_routes when no contract exists."""
    settings = MagicMock()
    settings.resend_webhook_secret = "whsec_test"

    with (
        patch("amail.routes.health.get_settings", return_value=settings),
        patch("amail.routes.health.load_routing_config", return_value=None),
    ):
        resp = client.get("/health/webhook")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "missing_routes"
    assert body["webhook_secret_configured"] is True
    assert body["routes_loaded"] is False


def test_health_webhook_missing_secret() -> None:
    """Verify /health/webhook reports missing_secret when the secret is absent."""
    settings = MagicMock()
    settings.resend_webhook_secret = ""

    with (
        patch("amail.routes.health.get_settings", return_value=settings),
        patch(
            "amail.routes.health.load_routing_config",
            return_value=RoutingConfig(domain="example.com"),
        ),
    ):
        resp = client.get("/health/webhook")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "missing_secret"
    assert body["webhook_secret_configured"] is False
    assert body["routes_loaded"] is True
