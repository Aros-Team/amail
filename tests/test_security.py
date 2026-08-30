import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


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
        app = create_app()
        assert app is not None


def test_development_without_api_key_starts() -> None:
    """Verify create_app succeeds without AMAIL_API_KEY in development."""
    from amail.main import create_app

    with patch.dict(os.environ, {"ENVIRONMENT": "development", "AMAIL_API_KEY": ""}):
        app = create_app()
        assert app is not None


def test_request_body_too_large_returns_413() -> None:
    """Verify requests exceeding 1 MB are rejected with 413."""
    from amail.main import app

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
    from amail.main import app

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/health")
    assert response.status_code == 200
