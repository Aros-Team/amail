"""Health check endpoints for the Amail API."""

import time
from datetime import UTC, datetime

import resend
from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.logging_config import get_logger
from app.models.schemas import (
    EmailHealthResponse,
    HealthResponse,
    WebhookHealthResponse,
)

router = APIRouter(tags=["health"])
log = get_logger(__name__)

TEST_EMAIL = "test@resend.dev"


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Simple liveness probe.",
)
def health_check() -> HealthResponse:
    """Return a simple liveness probe response."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(UTC).isoformat(),
    )


@router.get(
    "/health/email",
    response_model=EmailHealthResponse,
    summary="Email provider health",
    description=(
        "Tests connectivity to the email provider by sending a test email "
        "to resend.dev."
    ),
)
def email_health_check() -> EmailHealthResponse:
    """Check email provider connectivity by sending a test email."""
    settings = get_settings()
    resend.api_key = settings.resend_api_key

    log.info("email_health_check_start", domain=settings.domain, test_email=TEST_EMAIL)

    start_time = time.perf_counter()

    try:
        params = {
            "from": f"test@{settings.domain}",
            "to": [TEST_EMAIL],
            "subject": "Health Check - Amail",
            "html": "<p>Health check email</p>",
        }

        response = resend.Emails.send(params)
        duration_ms = (time.perf_counter() - start_time) * 1000

        resend_id = response.get("id", "")
        log.info(
            "email_health_check_success",
            resend_id=resend_id,
            duration_ms=round(duration_ms, 2),
        )

        return EmailHealthResponse(
            status="healthy",
            latency_ms=round(duration_ms, 2),
            status_code=200,
            resend_id=resend_id,
            test_email=TEST_EMAIL,
            timestamp=datetime.now(UTC).isoformat(),
        )

    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        status_code = getattr(e, "status_code", 503)

        log.error(
            "email_health_check_failure",
            duration_ms=round(duration_ms, 2),
            error=str(e),
        )

        raise HTTPException(
            status_code=status_code,
            detail=EmailHealthResponse(
                status="unhealthy",
                latency_ms=round(duration_ms, 2),
                status_code=status_code,
                timestamp=datetime.now(UTC).isoformat(),
            ).model_dump(),
        ) from e


@router.get(
    "/health/webhook",
    response_model=WebhookHealthResponse,
    summary="Webhook configuration health",
    description="Checks whether the webhook secret is configured.",
)
def webhook_health_check() -> WebhookHealthResponse:
    """Check whether the webhook secret is configured."""
    settings = get_settings()
    webhook_configured = bool(settings.resend_webhook_secret)

    log.info("webhook_health_check", webhook_configured=webhook_configured)

    return WebhookHealthResponse(
        status="configured" if webhook_configured else "missing_secret",
        webhook_secret_configured=webhook_configured,
        timestamp=datetime.now(UTC).isoformat(),
    )
