class EmailError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class EmailAuthError(EmailError):
    pass


class EmailRateLimitError(EmailError):
    def __init__(self, message: str, reset_at: int | None = None):
        self.reset_at = reset_at
        super().__init__(message, status_code=429)


class EmailServerError(EmailError):
    pass


class EmailConnectionError(EmailError):
    pass


class EmailValidationError(EmailError):
    pass
