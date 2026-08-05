from app.config import Settings


def test_settings_defaults() -> None:
    """Verify Settings applies the documented default values."""
    s = Settings()
    assert s.domain == "aros.services"
    assert s.email_provider == "resend"
    assert s.webhook_emails == ["support", "noreply", "team"]


def test_webhook_allowed_emails() -> None:
    """Verify webhook allowed emails are derived from the domain."""
    s = Settings(domain="test.com", webhook_emails=["support", "noreply"])
    expected = ["support@test.com", "noreply@test.com"]
    assert s.webhook_allowed_emails == expected


def test_effective_forward_to_email_default() -> None:
    """Verify the effective forward email falls back to the default."""
    s = Settings(forward_to_email="default@example.com")
    assert s.effective_forward_to_email == "default@example.com"


def test_effective_forward_to_email_override() -> None:
    """Verify set_forward_to_email overrides the effective forward email."""
    s = Settings(forward_to_email="default@example.com")
    s.set_forward_to_email("override@example.com")
    assert s.effective_forward_to_email == "override@example.com"


def test_forward_override_is_isolated_per_instance() -> None:
    """Verify forward overrides stay isolated between Settings instances."""
    s = Settings(forward_to_email="default@example.com")
    other = Settings(forward_to_email="default@example.com")
    s.set_forward_to_email("override@example.com")
    assert s.effective_forward_to_email == "override@example.com"
    assert other.effective_forward_to_email == "default@example.com"
