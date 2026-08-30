"""Email messaging API routes for the Amail service."""

import asyncio
import json
from typing import Any

import resend
from fastapi import APIRouter, Depends, HTTPException, Request

from amail.config import get_settings
from amail.dependencies import require_api_key
from amail.logging_config import get_logger
from amail.models.errors import ErrorDetail
from amail.models.schemas import (
    BatchEmailRequest,
    BatchReport,
    EmailRequest,
    EmailResponse,
)
from amail.providers import get_receiver
from amail.services.email_service import EmailService

log = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["messages"])


@router.post(
    "/send",
    response_model=EmailResponse,
    summary="Send a single email",
    description=("Send a plain-text email. Accepts a single recipient " "or a list."),
    responses={
        200: {"description": "Email sent"},
        400: {"model": ErrorDetail, "description": "Validation error"},
        500: {"model": ErrorDetail, "description": "Internal error"},
    },
    dependencies=[Depends(require_api_key)],
)
def send_email(request: EmailRequest) -> EmailResponse:
    """Send a single plain-text email."""
    service = EmailService()

    to_list = [request.to] if isinstance(request.to, str) else request.to
    log.info("send_request", to=to_list)

    result = service.send(request)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.message)
    return result


@router.post(
    "/send/batch",
    response_model=BatchReport,
    summary="Send multiple emails (batch)",
    description=(
        "Send multiple emails with best-effort semantics. If any fail and "
        "ADMIN_EMAIL is configured, a failure report is forwarded."
    ),
    responses={
        200: {"description": "Batch complete with per-email results"},
    },
    dependencies=[Depends(require_api_key)],
)
def send_batch(request: BatchEmailRequest) -> BatchReport:
    """Send multiple emails and return a per-email batch report."""
    service = EmailService()
    log.info("batch_send_request", count=len(request.emails), parallel=request.parallel)
    return service.send_batch(request)


@router.post(
    "/receive",
    summary="Receive email webhook from Resend",
    description=(
        "Resend webhook receiver. Verifies Svix signature, processes "
        "email.received events, forwards to configured target."
    ),
    responses={
        200: {"description": "Webhook processed"},
        400: {"description": "Missing headers or invalid payload"},
    },
)
async def receive_email(request: Request) -> dict[str, Any]:
    """Process an incoming Resend webhook with signature verification."""
    settings = get_settings()

    svix_id = request.headers.get("svix-id")
    svix_timestamp = request.headers.get("svix-timestamp")
    svix_signature = request.headers.get("svix-signature")

    if not all([svix_id, svix_timestamp, svix_signature]):
        raise HTTPException(status_code=400, detail="Missing Svix webhook headers")

    raw_body = await request.body()

    try:
        resend.Webhooks.verify(
            {
                "payload": raw_body.decode("utf-8"),
                "headers": {
                    "id": svix_id,
                    "timestamp": svix_timestamp,
                    "signature": svix_signature,
                },
                "webhook_secret": settings.resend_webhook_secret,
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Webhook signature verification failed"
        ) from e

    try:
        payload_dict = json.loads(raw_body)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid webhook payload") from e

    receiver = get_receiver()
    if receiver is None:
        raise HTTPException(
            status_code=500, detail="No receiver configured for active provider"
        )

    result = await asyncio.to_thread(receiver.receive, payload_dict)

    if result.get("status") == "error":
        raise HTTPException(
            status_code=500, detail=result.get("reason", "receive failed")
        )

    return result
