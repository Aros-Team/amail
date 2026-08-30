"""Tests for API key authentication on protected endpoints."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from amail.main import app

# Test API key value — must match the env var set in each test.
TEST_API_KEY = "test-secret-api-key-12345"

client = TestClient(app)


# ---------------------------------------------------------------------------
# POST /api/v1/send — protected endpoints
# ---------------------------------------------------------------------------


def test_send_no_api_key_returns_401() -> None:
    """Request to /send without X-API-Key header must be rejected with 401."""
    # Arrange — no header at all
    # Act
    resp = client.post(
        "/api/v1/send",
        json={"to": "user@example.com", "subject": "Hi", "body": "Hello"},
    )
    # Assert
    assert resp.status_code == 401
    detail = resp.json().get("detail", "")
    assert "api key" in detail.lower() or "unauthorized" in detail.lower()


def test_send_wrong_api_key_returns_401() -> None:
    """Request to /send with an incorrect X-API-Key must be rejected with 401."""
    # Arrange — wrong key
    # Act
    resp = client.post(
        "/api/v1/send",
        json={"to": "user@example.com", "subject": "Hi", "body": "Hello"},
        headers={"X-API-Key": "wrong-key-abcdef"},
    )
    # Assert
    assert resp.status_code == 401
    detail = resp.json().get("detail", "")
    assert "api key" in detail.lower() or "unauthorized" in detail.lower()


def test_send_valid_api_key_passes_auth() -> None:
    """Verify /send with correct X-API-Key passes auth (not 401)."""
    # May fail downstream (500) if no provider, but must NOT return 401.
    # Arrange — mock provider to avoid real calls
    sender = MagicMock()
    sender.send_with_retry.return_value = {"id": "mock_1", "request_id": "r1"}
    provider = MagicMock()
    provider.sender = sender

    with (
        patch("amail.services.email_service.get_provider", return_value=provider),
        patch.dict("os.environ", {"AMAIL_API_KEY": TEST_API_KEY}),
    ):
        # Act
        resp = client.post(
            "/api/v1/send",
            json={"to": "user@example.com", "subject": "Hi", "body": "Hello"},
            headers={"X-API-Key": TEST_API_KEY},
        )

    # Assert — must NOT be 401 (auth passed); expect 200 with mock provider
    assert resp.status_code != 401
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# POST /api/v1/send/batch — protected endpoints
# ---------------------------------------------------------------------------


def test_batch_no_api_key_returns_401() -> None:
    """Request to /send/batch without X-API-Key header must be rejected with 401."""
    # Arrange — no header
    # Act
    resp = client.post(
        "/api/v1/send/batch",
        json={
            "emails": [
                {"to": "a@example.com", "subject": "Hi", "body": "Hello"},
            ],
        },
    )
    # Assert
    assert resp.status_code == 401
    detail = resp.json().get("detail", "")
    assert "api key" in detail.lower() or "unauthorized" in detail.lower()


def test_batch_wrong_api_key_returns_401() -> None:
    """Request to /send/batch with an incorrect X-API-Key must be rejected with 401."""
    # Arrange — wrong key
    # Act
    resp = client.post(
        "/api/v1/send/batch",
        json={
            "emails": [
                {"to": "a@example.com", "subject": "Hi", "body": "Hello"},
            ],
        },
        headers={"X-API-Key": "wrong-key-abcdef"},
    )
    # Assert
    assert resp.status_code == 401
    detail = resp.json().get("detail", "")
    assert "api key" in detail.lower() or "unauthorized" in detail.lower()


def test_batch_valid_api_key_passes_auth() -> None:
    """Verify /send/batch with correct X-API-Key passes auth (not 401)."""
    # May fail downstream if no provider, but must NOT return 401.
    # Arrange — mock provider
    sender = MagicMock()
    sender.send_with_retry.return_value = {"id": "mock_1", "request_id": "r1"}
    provider = MagicMock()
    provider.sender = sender

    with (
        patch("amail.services.email_service.get_provider", return_value=provider),
        patch.dict("os.environ", {"AMAIL_API_KEY": TEST_API_KEY}),
    ):
        # Act
        resp = client.post(
            "/api/v1/send/batch",
            json={
                "emails": [
                    {"to": "a@example.com", "subject": "Hi", "body": "Hello"},
                ],
            },
            headers={"X-API-Key": TEST_API_KEY},
        )

    # Assert — must NOT be 401
    assert resp.status_code != 401


# ---------------------------------------------------------------------------
# Public endpoints — must NOT require auth
# ---------------------------------------------------------------------------


def test_health_no_key_still_works() -> None:
    """GET /health without any API key must still return 200."""
    # Arrange — no header
    # Act
    resp = client.get("/health")
    # Assert
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_receive_no_key_still_works() -> None:
    """Verify /receive without API key does not return 401 (public endpoint)."""
    # Returns 400 due to missing Svix headers — that's expected.
    # The point: it must not be rejected at the auth layer.
    # Arrange — no Svix headers, no API key
    # Act
    resp = client.post("/api/v1/receive", json={"type": "email.received", "data": {}})
    # Assert — must NOT be 401 (public endpoint); expect 400 (missing Svix headers)
    assert resp.status_code != 401
    assert resp.status_code == 400
