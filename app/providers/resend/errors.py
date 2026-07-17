from app.exceptions import EmailError


class ResendAPIError(EmailError):
    def __init__(self, message: str, status_code: int | None = None, error_type: str = "unknown"):
        self.error_type = error_type
        super().__init__(message, status_code)


class ResendRateLimitError(ResendAPIError):
    def __init__(self, message: str, status_code: int | None = None, reset_at: int | None = None):
        self.reset_at = reset_at
        super().__init__(message, status_code, "rate_limit")


class ResendServerError(ResendAPIError):
    pass


class ResendConnectionError(ResendAPIError):
    pass
