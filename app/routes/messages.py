import asyncio
import json

import resend
from fastapi import APIRouter, HTTPException, Request
from jinja2 import TemplateNotFound

from app.config import get_settings
from app.logging_config import get_logger
from app.models.errors import ErrorDetail
from app.models.schemas import (
    BatchEmailRequest,
    BatchReport,
    EmailRequest,
    EmailResponse,
    RenderRequest,
    RenderResponse,
    TemplateInfo,
    TemplatesResponse,
)
from app.providers import get_receiver
from app.services.email_service import EmailService
from app.services.templates import get_templates, render_template

log = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["messages"])


@router.get(
    "/templates",
    response_model=TemplatesResponse,
    summary="List email templates",
    description="Returns available templates with their variable metadata.",
    responses={200: {"description": "Templates list"}},
)
def list_templates():
    templates = get_templates()
    return TemplatesResponse(
        templates=[
            TemplateInfo(
                name=name, description=info["description"], variables=info["variables"]
            )
            for name, info in templates.items()
        ]
    )


@router.post(
    "/templates/render",
    response_model=RenderResponse,
    summary="Render a template",
    description="Renders a template with the given data and returns the HTML. Useful for the template preview tool.",
    responses={
        200: {"description": "Rendered HTML"},
        404: {"model": ErrorDetail, "description": "Template not found"},
    },
)
def render_template_endpoint(request: RenderRequest):
    try:
        html = render_template(request.template, request.data)
        return RenderResponse(html=html)
    except TemplateNotFound:
        raise HTTPException(
            status_code=404, detail=f"Template '{request.template}' not found"
        )


@router.post(
    "/send",
    response_model=EmailResponse,
    summary="Send a single email",
    description="Send an email using a named template. Accepts a single recipient or a list.",
    responses={
        200: {"description": "Email sent"},
        400: {
            "model": ErrorDetail,
            "description": "Template not found or validation error",
        },
        500: {"model": ErrorDetail, "description": "Internal error"},
    },
)
def send_email(request: EmailRequest):
    service = EmailService()

    to_list = [request.to] if isinstance(request.to, str) else request.to
    log.info("send_request", to=to_list, template=request.template)

    result = service.send(request)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.message)
    return result


@router.post(
    "/send/batch",
    response_model=BatchReport,
    summary="Send multiple emails (batch)",
    description="Send multiple emails with best-effort semantics. If any fail and ADMIN_EMAIL is configured, a failure report is forwarded.",
    responses={
        200: {"description": "Batch complete with per-email results"},
    },
)
def send_batch(request: BatchEmailRequest):
    service = EmailService()
    log.info("batch_send_request", count=len(request.emails), parallel=request.parallel)
    return service.send_batch(request)


@router.post(
    "/receive",
    summary="Receive email webhook from Resend",
    description="Resend webhook receiver. Verifies Svix signature, processes email.received events, forwards to configured target.",
    responses={
        200: {"description": "Webhook processed"},
        400: {"description": "Missing headers or invalid payload"},
    },
)
async def receive_email(request: Request):
    settings = get_settings()

    svix_id = request.headers.get("svix-id")
    svix_timestamp = request.headers.get("svix-timestamp")
    svix_signature = request.headers.get("svix-signature")

    if not all([svix_id, svix_timestamp, svix_signature]):
        raise HTTPException(status_code=400, detail="Missing Svix webhook headers")

    raw_body = await request.body()

    try:
        verified = resend.webhooks.verify(
            payload=raw_body,
            headers={
                "id": svix_id,
                "timestamp": svix_timestamp,
                "signature": svix_signature,
            },
            secret=settings.resend_webhook_secret,
        )
    except Exception:
        raise HTTPException(
            status_code=400, detail="Webhook signature verification failed"
        )

    try:
        payload_dict = json.loads(verified) if isinstance(verified, str) else verified
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    receiver = get_receiver()
    if receiver is None:
        raise HTTPException(
            status_code=500, detail="No receiver configured for active provider"
        )

    return await asyncio.to_thread(receiver.receive, payload_dict)
