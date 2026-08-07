from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.config.routing import RoutingConfig
from main import app

client = TestClient(app)


def test_list_templates_returns_exact_set() -> None:
    """Verify the templates endpoint lists the expected template names."""
    resp = client.get("/api/v1/templates")
    assert resp.status_code == 200
    names = {t["name"] for t in resp.json()["templates"]}
    assert names == {"action", "notification", "verification", "custom"}


def test_render_template_ok() -> None:
    """Verify rendering a valid template returns the expected HTML."""
    resp = client.post(
        "/api/v1/templates/render",
        json={"template": "verification", "data": {"code": "123456", "lang": "en"}},
    )
    assert resp.status_code == 200
    html = resp.json()["html"]
    assert html.count("123456") == 1
    assert ">123456</span>" in html


def test_render_template_not_found() -> None:
    """Verify rendering an unknown template returns 404."""
    resp = client.post(
        "/api/v1/templates/render",
        json={"template": "does_not_exist", "data": {}},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Template 'does_not_exist' not found"


def test_render_invalid_payload_missing_template() -> None:
    """Verify a render payload without a template returns 422."""
    resp = client.post("/api/v1/templates/render", json={"data": {}})
    assert resp.status_code == 422


def test_health_email_missing_domain_is_unhealthy() -> None:
    """Verify /health/email alerts when no domain is in the routing contract."""
    settings = MagicMock()
    settings.resend_api_key = "re_test_key"

    with (
        patch("app.routes.health.get_settings", return_value=settings),
        patch("app.routes.health.load_routing_config", return_value=None),
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
        patch("app.routes.health.get_settings", return_value=settings),
        patch(
            "app.routes.health.load_routing_config",
            return_value=RoutingConfig(domain="example.com"),
        ),
        patch(
            "app.routes.health.resend.Emails.send",
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
        patch("app.routes.health.get_settings", return_value=settings),
        patch(
            "app.routes.health.load_routing_config",
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
        patch("app.routes.health.get_settings", return_value=settings),
        patch("app.routes.health.load_routing_config", return_value=None),
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
        patch("app.routes.health.get_settings", return_value=settings),
        patch(
            "app.routes.health.load_routing_config",
            return_value=RoutingConfig(domain="example.com"),
        ),
    ):
        resp = client.get("/health/webhook")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "missing_secret"
    assert body["webhook_secret_configured"] is False
    assert body["routes_loaded"] is True
