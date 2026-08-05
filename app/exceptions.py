"""Domain-specific exceptions for email operations."""


class EmailError(Exception):
    """Base error raised when an email operation fails."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class EmailAuthError(EmailError):
    """Raised when email provider authentication fails."""


class EmailRateLimitError(EmailError):
    """Raised when the email provider rate limit is exceeded."""

    def __init__(self, message: str, reset_at: int | None = None) -> None:
        self.reset_at = reset_at
        super().__init__(message, status_code=429)


class EmailServerError(EmailError):
    """Raised when the email provider returns a server error."""


class EmailConnectionError(EmailError):
    """Raised when the email provider cannot be reached."""


class EmailValidationError(EmailError):
    """Raised when an email payload fails validation."""
