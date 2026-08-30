import re
import tomllib
from pathlib import Path

from amail.config import Settings


def test_settings_defaults() -> None:
    """Verify Settings applies the documented default values."""
    s = Settings(_env_file=None)
    assert s.resend_api_key == ""
    assert s.resend_webhook_secret == ""
    assert s.email_provider == "resend"
    assert s.environment == "development"
    assert s.log_level == "INFO"
    assert not hasattr(s, "domain")
    assert not hasattr(s, "webhook_emails")
    assert not hasattr(s, "forward_to_email")


def test_settings_version_matches_project() -> None:
    """
    Settings.version must stay in sync with pyproject.toml.

    Release-please bumps both files together (settings.py carries the
    x-release-please-version marker), so this asserts the single source of
    truth instead of pinning a hardcoded literal that goes stale on every
    release.
    """
    project_version = tomllib.loads(Path("pyproject.toml").read_text())["project"][
        "version"
    ]
    s = Settings(_env_file=None)
    assert s.version == project_version
    assert re.fullmatch(
        r"\d+\.\d+\.\d+", s.version
    ), f"expected semver, got {s.version!r}"
