from unittest.mock import MagicMock

import pytest

import amail.providers.mock  # noqa: F401 — ensure mock provider is registered


@pytest.fixture
def mock_settings() -> MagicMock:
    """Create a mocked Settings object with known test values."""
    settings = MagicMock()
    settings.resend_api_key = "re_test_key"
    settings.resend_webhook_secret = "whsec_test"
    settings.admin_email = "admin@test.example.com"
    settings.email_provider = "mock"
    settings.environment = "test"
    settings.version = "1.0.0"
    settings.log_level = "INFO"
    return settings
