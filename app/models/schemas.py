from pydantic import BaseModel, EmailStr
from typing import Any


class EmailRequest(BaseModel):
    to: EmailStr
    template: str
    subject: str
    data: dict[str, Any] = {}


class EmailResponse(BaseModel):
    success: bool
    message: str
    email_id: str | None = None


class TemplateInfo(BaseModel):
    name: str
    description: str


class TemplatesResponse(BaseModel):
    templates: list[TemplateInfo]


class WebhookPayload(BaseModel):
    type: str
    data: dict[str, Any] = {}
