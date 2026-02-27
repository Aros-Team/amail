import os
import pytest
from unittest.mock import patch

os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["RESEND_API_KEY"] = "test-resend-key"
os.environ["DOMAIN"] = "test.com"
os.environ["FORWARD_TO_EMAIL"] = "forward@test.com"
os.environ["WEBHOOK_EMAILS"] = "support,noreply"


@pytest.fixture
def mock_resend():
    with patch("resend.emails.send") as mock:
        mock.return_value = {"id": "test-email-id"}
        yield mock


@pytest.fixture
def settings():
    from app.config import get_settings
    return get_settings()
