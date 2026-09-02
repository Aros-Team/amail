"""Tests for production hardening: docs disable, batch validation via get_settings."""

from unittest.mock import patch

import pytest

from amail.main import create_app
from amail.models.schemas import BatchEmailRequest


def _make_email(n: int = 1) -> list[dict[str, str]]:
    """Return a list of valid email payloads."""
    return [
        {"to": f"user{n}@example.com", "subject": "Hi", "body": "Hello"}
        for n in range(1, n + 1)
    ]


# --- Test 1: docs disabled in production ---


def test_create_app_docs_disabled_in_production() -> None:
    """FastAPI must hide /docs and /redoc when ENVIRONMENT=production."""
    with (
        patch.dict(
            "os.environ",
            {"ENVIRONMENT": "production", "AMAIL_API_KEY": "test-key"},
        ),
        patch("amail.main.configure_logging"),
    ):
        app = create_app()
        assert app.docs_url is None
        assert app.redoc_url is None


# --- Test 2: docs enabled in development (default) ---


def test_create_app_docs_enabled_in_development() -> None:
    """FastAPI must expose /docs and /redoc in development mode."""
    with (
        patch.dict("os.environ", {"ENVIRONMENT": "development"}, clear=False),
        patch("amail.main.configure_logging"),
    ):
        app = create_app()
        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"


# --- Test 3: batch validation uses get_settings ---


def test_batch_validation_uses_get_settings_rejects_over_limit() -> None:
    """BatchEmailRequest must read max_batch_size from get_settings, not os.environ."""
    fake_settings = type("FakeSettings", (), {"max_batch_size": 10})()

    with patch("amail.models.schemas.get_settings", return_value=fake_settings):
        emails = _make_email(11)
        with pytest.raises(ValueError, match="exceeds maximum of 10"):
            BatchEmailRequest(emails=emails)


# --- Test 4: batch validation respects settings value ---


def test_batch_validation_respects_settings_value_accepts_at_limit() -> None:
    """BatchEmailRequest must accept emails up to the configured max."""
    fake_settings = type("FakeSettings", (), {"max_batch_size": 10})()

    with patch("amail.models.schemas.get_settings", return_value=fake_settings):
        emails = _make_email(10)
        batch = BatchEmailRequest(emails=emails)
        assert len(batch.emails) == 10
