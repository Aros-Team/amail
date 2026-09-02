"""Tests for in-memory rate limiting on API endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from amail.main import app

TEST_API_KEY = "test-secret-api-key-12345"


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> None:
    """Reset in-memory rate limiter state between tests."""
    try:
        from amail.middleware.rate_limit import reset_rate_limits

        reset_rate_limits()
    except ImportError:
        pass  # Module does not exist yet — will be created with the implementation
    yield
    try:
        from amail.middleware.rate_limit import reset_rate_limits

        reset_rate_limits()
    except ImportError:
        pass


client = TestClient(app)


def _mock_provider() -> MagicMock:
    """Return a mocked provider with a working sender."""
    sender = MagicMock()
    sender.send_with_retry.return_value = {"id": "mock_1", "request_id": "r1"}
    provider = MagicMock()
    provider.sender = sender
    return provider


def _send_request() -> dict:
    """Build a valid POST /api/v1/send request body."""
    return {
        "to": "user@example.com",
        "subject": "Hi",
        "body": "Hello",
    }


# ---------------------------------------------------------------------------
# Test 1: Send endpoint within limit passes
# ---------------------------------------------------------------------------


def test_rate_limit_send_within_limit_passes() -> None:
    """5 requests under the per-second limit must all return 200."""
    with (
        patch(
            "amail.services.email_service.get_provider",
            return_value=_mock_provider(),
        ),
        patch.dict("os.environ", {"AMAIL_API_KEY": TEST_API_KEY}),
    ):
        for _ in range(5):
            resp = client.post(
                "/api/v1/send",
                json=_send_request(),
                headers={"X-API-Key": TEST_API_KEY},
            )
            assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Test 2: Send endpoint over per-second limit returns 429
# ---------------------------------------------------------------------------


def test_rate_limit_send_over_per_sec_returns_429() -> None:
    """11 requests should exceed the 10 req/s default — 11th must return 429."""
    with (
        patch(
            "amail.services.email_service.get_provider",
            return_value=_mock_provider(),
        ),
        patch.dict("os.environ", {"AMAIL_API_KEY": TEST_API_KEY}),
    ):
        for i in range(10):
            resp = client.post(
                "/api/v1/send",
                json=_send_request(),
                headers={"X-API-Key": TEST_API_KEY},
            )
            assert resp.status_code == 200, f"Request {i + 1} should pass"

        resp = client.post(
            "/api/v1/send",
            json=_send_request(),
            headers={"X-API-Key": TEST_API_KEY},
        )
        assert resp.status_code == 429, "11th request must be rate-limited"


# ---------------------------------------------------------------------------
# Test 3: Health endpoint within limit passes
# ---------------------------------------------------------------------------


def test_rate_limit_health_within_limit_passes() -> None:
    """100 requests under the 300 req/min limit must all return 200."""
    for _ in range(100):
        resp = client.get("/health")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Test 4: Health endpoint over limit returns 429
# ---------------------------------------------------------------------------


def test_rate_limit_health_over_limit_returns_429() -> None:
    """301 requests should exceed the 300 req/min default — 301st must return 429."""
    for i in range(300):
        resp = client.get("/health")
        assert resp.status_code == 200, f"Request {i + 1} should pass"

    resp = client.get("/health")
    assert resp.status_code == 429, "301st request must be rate-limited"


# ---------------------------------------------------------------------------
# Test 5: 429 response includes Retry-After header
# ---------------------------------------------------------------------------


def test_rate_limit_429_includes_retry_after_header() -> None:
    """A rate-limited response must include a Retry-After header."""
    with (
        patch(
            "amail.services.email_service.get_provider",
            return_value=_mock_provider(),
        ),
        patch.dict("os.environ", {"AMAIL_API_KEY": TEST_API_KEY}),
    ):
        # Exhaust the per-second limit
        for _ in range(10):
            client.post(
                "/api/v1/send",
                json=_send_request(),
                headers={"X-API-Key": TEST_API_KEY},
            )

        resp = client.post(
            "/api/v1/send",
            json=_send_request(),
            headers={"X-API-Key": TEST_API_KEY},
        )
        assert resp.status_code == 429
        assert "retry-after" in resp.headers
        retry_after = int(resp.headers["retry-after"])
        assert retry_after > 0


# ---------------------------------------------------------------------------
# Test 6: Env var override works
# ---------------------------------------------------------------------------


def test_rate_limit_env_var_override() -> None:
    """AMAIL_RATE_LIMIT_SEND_PER_SEC=3 should enforce a limit of 3 req/s."""
    with (
        patch(
            "amail.services.email_service.get_provider",
            return_value=_mock_provider(),
        ),
        patch.dict(
            "os.environ",
            {"AMAIL_API_KEY": TEST_API_KEY, "AMAIL_RATE_LIMIT_SEND_PER_SEC": "3"},
        ),
    ):
        for i in range(3):
            resp = client.post(
                "/api/v1/send",
                json=_send_request(),
                headers={"X-API-Key": TEST_API_KEY},
            )
            assert resp.status_code == 200, f"Request {i + 1} should pass"

        resp = client.post(
            "/api/v1/send",
            json=_send_request(),
            headers={"X-API-Key": TEST_API_KEY},
        )
        assert resp.status_code == 429, "4th request must be rate-limited with limit=3"


# ---------------------------------------------------------------------------
# Test 7: Receive endpoint rate limited
# ---------------------------------------------------------------------------


def test_rate_limit_receive_over_limit_returns_429() -> None:
    """POST /api/v1/receive should be rate-limited after 10 req/s."""
    valid_svx_headers = {
        "svix-id": "msg_test",
        "svix-timestamp": "1234567890",
        "svix-signature": "v1,test_signature",
    }

    with (
        patch("amail.providers.resend.receiver.ResendReceiver.receive") as mock_receive,
        patch("resend.Webhooks.verify"),
        patch.dict("os.environ", {"AMAIL_WEBHOOK_SECRET": "whsec_test"}),
    ):
        mock_receive.return_value = {"status": "ok"}
        for i in range(10):
            resp = client.post(
                "/api/v1/receive",
                json={"type": "email.received", "data": {}},
                headers=valid_svx_headers,
            )
            assert resp.status_code == 200, f"Request {i + 1} should pass"

        resp = client.post(
            "/api/v1/receive",
            json={"type": "email.received", "data": {}},
            headers=valid_svx_headers,
        )
        assert resp.status_code == 429, "11th request must be rate-limited"
