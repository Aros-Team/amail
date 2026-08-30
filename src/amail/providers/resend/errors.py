"""Typed errors raised by the Resend provider."""

from amail.exceptions import EmailError


class ResendAPIError(EmailError):
    """Base error for failures returned by the Resend API."""

    def __init__(
        self, message: str, status_code: int | None = None, error_type: str = "unknown"
    ) -> None:
        self.error_type = error_type
        super().__init__(message, status_code)


class ResendRateLimitError(ResendAPIError):
    """Error raised when Resend rate limits the request."""

    def __init__(
        self, message: str, status_code: int | None = None, reset_at: int | None = None
    ) -> None:
        self.reset_at = reset_at
        super().__init__(message, status_code, "rate_limit")


class ResendServerError(ResendAPIError):
    """Error raised when Resend reports a server-side failure."""


class ResendConnectionError(ResendAPIError):
    """Error raised when the connection to Resend fails."""
