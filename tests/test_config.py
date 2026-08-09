from app.config import Settings


def test_settings_defaults() -> None:
    """Verify Settings applies the documented default values."""
    s = Settings(_env_file=None)
    assert s.resend_api_key == ""
    assert s.resend_webhook_secret == ""
    assert s.email_provider == "resend"
    assert s.environment == "development"
    assert s.version == "1.1.0"
    assert s.log_level == "INFO"
    assert not hasattr(s, "domain")
    assert not hasattr(s, "webhook_emails")
    assert not hasattr(s, "forward_to_email")
