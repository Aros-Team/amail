from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_settings() -> MagicMock:
    """Create a mocked Settings object with known test values."""
    settings = MagicMock()
    settings.resend_api_key = "re_test_key"
    settings.resend_webhook_secret = "whsec_test"
    settings.domain = "test.example.com"
    settings.forward_to_email = "default@example.com"
    settings.admin_email = "admin@test.example.com"
    settings.webhook_emails = ["support", "noreply", "team"]
    settings.webhook_allowed_emails = [
        "support@test.example.com",
        "noreply@test.example.com",
        "team@test.example.com",
    ]
    settings.effective_forward_to_email = "default@example.com"
    settings.email_provider = "mock"
    settings.environment = "test"
    settings.version = "1.0.0"
    settings.log_level = "INFO"
    return settings
