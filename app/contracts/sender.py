"""Email sending contract."""

from typing import Any, Protocol


class EmailSender(Protocol):
    """Protocol for email sending implementations."""

    def send(
        self,
        to: list[str],
        subject: str,
        html: str,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send an email and return its id and request id."""
        ...

    def send_with_retry(
        self,
        to: list[str],
        subject: str,
        html: str,
        options: dict[str, Any] | None = None,
        max_attempts: int = 3,
    ) -> dict[str, Any]:
        """Send an email, retrying transient failures."""
        ...
