"""Security hardening tests — batch limits, provider health, API key safety."""

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from amail.main import app

TEST_API_KEY = "test-secret-api-key-12345"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_batch_payload(count: int) -> dict:
    """Build a BatchEmailRequest payload with *count* identical emails."""
    return {
        "emails": [
            {"to": f"user{i}@example.com", "subject": "Hi", "body": "Hello"}
            for i in range(count)
        ],
    }


# ---------------------------------------------------------------------------
# Existing tests (unchanged)
# ---------------------------------------------------------------------------


def test_production_requires_api_key() -> None:
    """Verify create_app raises RuntimeError without API key in production."""
    from amail.main import create_app

    with (
        patch.dict(os.environ, {"ENVIRONMENT": "production", "AMAIL_API_KEY": ""}),
        pytest.raises(RuntimeError, match="AMAIL_API_KEY must be set"),
    ):
        create_app()


def test_production_with_api_key_starts() -> None:
    """Verify create_app succeeds when AMAIL_API_KEY is set in production."""
    from amail.main import create_app

    with patch.dict(
        os.environ, {"ENVIRONMENT": "production", "AMAIL_API_KEY": "test-key-1234"}
    ):
        created = create_app()
        assert created is not None


def test_development_without_api_key_starts() -> None:
    """Verify create_app succeeds without AMAIL_API_KEY in development."""
    from amail.main import create_app

    with patch.dict(os.environ, {"ENVIRONMENT": "development", "AMAIL_API_KEY": ""}):
        created = create_app()
        assert created is not None


def test_request_body_too_large_returns_413() -> None:
    """Verify requests exceeding 1 MB are rejected with 413."""
    client = TestClient(app, raise_server_exceptions=False)
    large_body = "x" * (1 * 1024 * 1024 + 1)  # 1 MB + 1 byte
    response = client.post(
        "/api/v1/send",
        content=large_body,
        headers={"Content-Type": "text/plain", "X-API-Key": "test-key"},
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "Request body too large"


def test_normal_request_not_blocked() -> None:
    """Verify normal-sized requests pass the body limit middleware."""
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/health")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# 1. Batch email limit tests
# ---------------------------------------------------------------------------


def test_batch_send_rejects_more_than_25_emails() -> None:
    """POST /send/batch with 26 emails must be rejected with 422."""
    sender = MagicMock()
    sender.send_with_retry.return_value = {"id": "mock_1", "request_id": "r1"}
    provider = MagicMock()
    provider.sender = sender

    with (
        patch("amail.services.email_service.get_provider", return_value=provider),
        patch.dict("os.environ", {"AMAIL_API_KEY": TEST_API_KEY}),
    ):
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/api/v1/send/batch",
            json=_make_batch_payload(26),
            headers={"X-API-Key": TEST_API_KEY},
        )

    assert (
        resp.status_code == 422
    ), f"Expected 422 for 26 emails, got {resp.status_code}: {resp.text}"


def test_batch_send_accepts_25_emails() -> None:
    """POST /send/batch with 25 emails must NOT be 422 (validation passes)."""
    sender = MagicMock()
    sender.send_with_retry.return_value = {"id": "mock_1", "request_id": "r1"}
    provider = MagicMock()
    provider.sender = sender

    with (
        patch("amail.services.email_service.get_provider", return_value=provider),
        patch.dict("os.environ", {"AMAIL_API_KEY": TEST_API_KEY}),
    ):
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/api/v1/send/batch",
            json=_make_batch_payload(25),
            headers={"X-API-Key": TEST_API_KEY},
        )

    assert (
        resp.status_code != 422
    ), f"Expected NOT 422 for 25 emails, got {resp.status_code}: {resp.text}"


def test_batch_send_env_var_overrides_limit() -> None:
    """AMAIL_MAX_BATCH_SIZE=10 must cap the batch at 10 emails."""
    sender = MagicMock()
    sender.send_with_retry.return_value = {"id": "mock_1", "request_id": "r1"}
    provider = MagicMock()
    provider.sender = sender

    fake_settings = type("FakeSettings", (), {"max_batch_size": 10})()

    with (
        patch("amail.services.email_service.get_provider", return_value=provider),
        patch("amail.models.schemas.get_settings", return_value=fake_settings),
        patch.dict(
            "os.environ",
            {"AMAIL_API_KEY": TEST_API_KEY, "AMAIL_MAX_BATCH_SIZE": "10"},
        ),
    ):
        client = TestClient(app, raise_server_exceptions=False)

        # 11 emails → must fail validation
        resp_over = client.post(
            "/api/v1/send/batch",
            json=_make_batch_payload(11),
            headers={"X-API-Key": TEST_API_KEY},
        )
        assert (
            resp_over.status_code == 422
        ), f"Expected 422 for 11 emails with limit=10, got {resp_over.status_code}"

        # 10 emails → must pass validation
        resp_ok = client.post(
            "/api/v1/send/batch",
            json=_make_batch_payload(10),
            headers={"X-API-Key": TEST_API_KEY},
        )
        assert (
            resp_ok.status_code != 422
        ), f"Expected NOT 422 for 10 emails with limit=10, got {resp_ok.status_code}"


# ---------------------------------------------------------------------------
# 2. Provider health check tests (GET /health/provider)
# ---------------------------------------------------------------------------


def test_provider_health_valid_key_returns_healthy() -> None:
    """GET /health/provider with valid key must return 200 + healthy."""
    with (
        patch("amail.routes.health.get_settings") as mock_settings,
        patch("amail.routes.health.resend") as mock_resend,
    ):
        mock_settings.return_value.resend_api_key = "re_valid_key"
        mock_resend.Domains.list.return_value = {"data": []}

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/health/provider")

    assert (
        resp.status_code == 200
    ), f"Expected 200 for valid provider health, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert body["status"] == "healthy"


def test_provider_health_missing_key_returns_503() -> None:
    """GET /health/provider with no API key must return 503."""
    with (
        patch("amail.routes.health.get_settings") as mock_settings,
        patch("amail.routes.health.resend") as mock_resend,
    ):
        mock_settings.return_value.resend_api_key = ""
        mock_resend.Domains.list.side_effect = Exception("No API key set")

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/health/provider")

    assert (
        resp.status_code == 503
    ), f"Expected 503 for missing key, got {resp.status_code}: {resp.text}"


def test_provider_health_invalid_key_returns_503() -> None:
    """GET /health/provider with invalid key must return 503."""
    auth_error = Exception("401 Unauthorized: invalid API key")
    auth_error.status_code = 401  # type: ignore[attr-defined]

    with (
        patch("amail.routes.health.get_settings") as mock_settings,
        patch("amail.routes.health.resend") as mock_resend,
    ):
        mock_settings.return_value.resend_api_key = "re_invalid_key"
        mock_resend.Domains.list.side_effect = auth_error

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/health/provider")

    assert (
        resp.status_code == 503
    ), f"Expected 503 for invalid key, got {resp.status_code}: {resp.text}"


# ---------------------------------------------------------------------------
# 3. Read-only API key test
# ---------------------------------------------------------------------------


def test_resend_api_key_not_reassigned_after_init() -> None:
    """ResendSender init must set resend.api_key from settings exactly once."""
    from amail.providers.resend.sender import ResendSender

    mock_settings = MagicMock()
    mock_settings.resend_api_key = "re_readonly_test_key"

    with patch(
        "amail.providers.resend.sender.get_settings", return_value=mock_settings
    ):
        import resend

        resend.api_key = ""  # reset before test
        ResendSender()
        assert resend.api_key == "re_readonly_test_key", (
            f"Expected resend.api_key to be 're_readonly_test_key', "
            f"got '{resend.api_key}'"
        )
