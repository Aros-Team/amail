"""Tests for health provider error mapping — no raw exception leakage."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from amail.main import app

client = TestClient(app)


def _patch_settings_with_key() -> "patch":
    """Return a context-manager that provides a valid API key in settings."""
    return patch(
        "amail.routes.health.get_settings",
        return_value=type(
            "Settings",
            (),
            {"resend_api_key": "re_test_key", "resend_webhook_secret": None},
        )(),
    )


# --- Test 1: auth error maps to auth_error category ---


def test_provider_health_auth_error_returns_auth_error_category() -> None:
    """Auth-related exceptions map to error_category 'auth_error'."""
    exc = Exception("Unauthorized: invalid api key")
    exc.status_code = 401  # type: ignore[attr-defined]

    with (
        _patch_settings_with_key(),
        patch("amail.providers.resend.sender.ResendSender"),
        patch("resend.Domains.list", side_effect=exc),
    ):
        resp = client.get("/health/provider")

    assert resp.status_code == 503
    body = resp.json()
    assert body["error_category"] == "auth_error"


# --- Test 2: connection error maps to connection_error category ---


def test_provider_health_connection_error_returns_connection_error_category() -> None:
    """Connection failures map to error_category 'connection_error'."""
    with (
        _patch_settings_with_key(),
        patch("amail.providers.resend.sender.ResendSender"),
        patch("resend.Domains.list", side_effect=ConnectionError("Connection refused")),
    ):
        resp = client.get("/health/provider")

    assert resp.status_code == 503
    body = resp.json()
    assert body["error_category"] == "connection_error"


# --- Test 3: server error maps to api_error category ---


def test_provider_health_server_error_returns_api_error_category() -> None:
    """Server-side exceptions (status 5xx) map to error_category 'api_error'."""
    exc = Exception("Internal Server Error")
    exc.status_code = 500  # type: ignore[attr-defined]

    with (
        _patch_settings_with_key(),
        patch("amail.providers.resend.sender.ResendSender"),
        patch("resend.Domains.list", side_effect=exc),
    ):
        resp = client.get("/health/provider")

    assert resp.status_code == 503
    body = resp.json()
    assert body["error_category"] == "api_error"


# --- Test 4: unknown error maps to unknown category ---


def test_provider_health_unknown_error_returns_unknown_category() -> None:
    """Unrecognized exceptions map to error_category 'unknown'."""
    with (
        _patch_settings_with_key(),
        patch("amail.providers.resend.sender.ResendSender"),
        patch("resend.Domains.list", side_effect=RuntimeError("Something broke")),
    ):
        resp = client.get("/health/provider")

    assert resp.status_code == 503
    body = resp.json()
    assert body["error_category"] == "unknown"


# --- Test 5: error response must NOT contain raw exception text ---


def test_provider_health_error_response_hides_raw_exception_details() -> None:
    """Raw SDK internals (API keys, stack details) must never leak."""
    with (
        _patch_settings_with_key(),
        patch("amail.providers.resend.sender.ResendSender"),
        patch(
            "resend.Domains.list",
            side_effect=Exception("Internal SDK details: key=sk-abc123"),
        ),
    ):
        resp = client.get("/health/provider")

    assert resp.status_code == 503
    raw = resp.text
    assert "sk-abc123" not in raw
    assert "Internal SDK details" not in raw
