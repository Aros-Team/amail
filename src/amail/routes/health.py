"""Health check endpoints for the Amail API."""

import time
from datetime import UTC, datetime

import resend
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from amail.config import get_settings
from amail.config.routing import load_routing_config
from amail.logging_config import get_logger
from amail.models.schemas import (
    EmailHealthResponse,
    HealthResponse,
    WebhookHealthResponse,
)

router = APIRouter(tags=["health"])
log = get_logger(__name__)


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


def _classify_error(e: Exception) -> tuple[str, str, int | None]:
    """Classify an exception into a category with sanitized message."""
    error_msg = str(e).lower()
    status_code = getattr(e, "status_code", None)

    # Auth errors
    if (
        status_code == 401
        or "unauthorized" in error_msg
        or "api key" in error_msg
        or "401" in str(e)
    ):
        return "auth_error", "Authentication failed — check API key", status_code or 401

    # Connection errors
    if any(
        x in error_msg
        for x in ["connection", "timeout", "network", "dns", "refused", "ssl", "tls"]
    ):
        return "connection_error", "Connection to provider failed", None

    # Server/client errors with status code
    if status_code is not None:
        if status_code >= 500:
            return (
                "api_error",
                f"Provider returned server error ({status_code})",
                status_code,
            )
        if status_code >= 400:
            return (
                "api_error",
                f"Provider returned client error ({status_code})",
                status_code,
            )

    return "unknown", "Provider health check failed", status_code


@router.get(
    "/health/provider",
    response_model=EmailHealthResponse,
    summary="Provider connection health",
    description="Verifies API key and connection to the email provider.",
)
def provider_health_check() -> EmailHealthResponse:
    """Check provider connectivity by listing domains."""
    settings = get_settings()
    if not settings.resend_api_key:
        raise HTTPException(
            status_code=503,
            detail=EmailHealthResponse(
                status="unhealthy",
                status_code=503,
                message="No API key configured",
                timestamp=datetime.now(UTC).isoformat(),
            ).model_dump(),
        )

    from amail.providers.resend.sender import ResendSender

    ResendSender()

    start_time = time.perf_counter()
    try:
        resend.Domains.list()
        duration_ms = (time.perf_counter() - start_time) * 1000

        log.info("provider_health_check_success", duration_ms=round(duration_ms, 2))

        return EmailHealthResponse(
            status="healthy",
            latency_ms=round(duration_ms, 2),
            status_code=200,
            timestamp=datetime.now(UTC).isoformat(),
        )

    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        category, message, status_code = _classify_error(e)

        log.error(
            "provider_health_check_failure",
            duration_ms=round(duration_ms, 2),
            error=str(e),
            error_category=category,
        )

        return JSONResponse(
            status_code=503,
            content=EmailHealthResponse(
                status="unhealthy",
                latency_ms=round(duration_ms, 2),
                status_code=status_code,
                message=message,
                error_category=category,
                timestamp=datetime.now(UTC).isoformat(),
            ).model_dump(),
        )


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
    routes_loaded = load_routing_config() is not None

    if webhook_configured and routes_loaded:
        status = "configured"
    elif not webhook_configured:
        status = "missing_secret"
    else:
        status = "missing_routes"

    log.info(
        "webhook_health_check",
        webhook_configured=webhook_configured,
        routes_loaded=routes_loaded,
    )

    return WebhookHealthResponse(
        status=status,
        webhook_secret_configured=webhook_configured,
        routes_loaded=routes_loaded,
        timestamp=datetime.now(UTC).isoformat(),
    )
