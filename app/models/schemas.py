from pydantic import BaseModel, EmailStr, Field
from typing import Any


class TemplateVariable(BaseModel):
    name: str
    type: str
    description: str
    required: bool


class TemplateInfo(BaseModel):
    name: str
    description: str
    variables: list[TemplateVariable]


class TemplatesResponse(BaseModel):
    templates: list[TemplateInfo]


class EmailRequest(BaseModel):
    to: EmailStr | list[EmailStr]
    subject: str
    template: str
    data: dict[str, Any] = {}
    cc: list[EmailStr] | None = None
    bcc: list[EmailStr] | None = None
    reply_to: EmailStr | None = None
    from_email: EmailStr | None = None
    lang: str = Field(default="es", pattern="^(es|en)$")


class EmailResponse(BaseModel):
    success: bool
    message: str
    email_id: str | None = None
    request_id: str | None = None
    to: str | None = None


class BatchEmailRequest(BaseModel):
    emails: list[EmailRequest]
    parallel: bool = True
    continue_on_error: bool = True


class BatchReport(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: list[EmailResponse]
    forwarded_to_admin: bool = False
    admin_email: str | None = None


class RenderRequest(BaseModel):
    template: str
    data: dict[str, Any] = {}


class RenderResponse(BaseModel):
    html: str


class WebhookPayload(BaseModel):
    type: str
    data: dict[str, Any] = {}


class HealthResponse(BaseModel):
    status: str
    timestamp: str


class EmailHealthResponse(BaseModel):
    status: str
    latency_ms: float | None = None
    status_code: int | None = None
    resend_id: str | None = None
    test_email: str | None = None
    timestamp: str


class WebhookHealthResponse(BaseModel):
    status: str
    webhook_secret_configured: bool
    timestamp: str
