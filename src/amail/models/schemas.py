"""Pydantic request and response schemas for the email API."""

from typing import Any

from pydantic import BaseModel, EmailStr


class EmailRequest(BaseModel):
    """Payload for sending a single plain-text email."""

    to: EmailStr | list[EmailStr]
    subject: str
    body: str
    cc: list[EmailStr] | None = None
    bcc: list[EmailStr] | None = None
    reply_to: EmailStr | None = None
    from_email: EmailStr | None = None


class EmailResponse(BaseModel):
    """Result of a single email send attempt."""

    success: bool
    message: str
    email_id: str | None = None
    request_id: str | None = None
    to: str | None = None


class BatchEmailRequest(BaseModel):
    """Payload for sending multiple emails in one request."""

    emails: list[EmailRequest]
    parallel: bool = True
    continue_on_error: bool = True


class BatchReport(BaseModel):
    """Aggregated results of a batch email send."""

    total: int
    succeeded: int
    failed: int
    results: list[EmailResponse]
    forwarded_to_admin: bool = False
    admin_email: str | None = None


class WebhookPayload(BaseModel):
    """Payload delivered by the email provider webhook."""

    type: str
    data: dict[str, Any] = {}


class HealthResponse(BaseModel):
    """Service health check response."""

    status: str
    timestamp: str


class EmailHealthResponse(BaseModel):
    """Email provider health check response."""

    status: str
    latency_ms: float | None = None
    status_code: int | None = None
    resend_id: str | None = None
    test_email: str | None = None
    message: str | None = None
    timestamp: str


class WebhookHealthResponse(BaseModel):
    """Webhook configuration health check response."""

    status: str
    webhook_secret_configured: bool
    routes_loaded: bool
    timestamp: str
