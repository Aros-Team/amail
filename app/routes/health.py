import time
from datetime import datetime, timezone
from typing import Any

import resend
from fastapi import APIRouter, HTTPException

from app import metrics
from app.config import get_settings
from app.logging_config import get_logger

router = APIRouter(prefix="", tags=["health"])
log = get_logger(__name__)

TEST_EMAIL = "test@resend.dev"


@router.get("/health/email")
def email_health_check() -> dict[str, Any]:
    settings = get_settings()
    resend.api_key = settings.RESEND_API_KEY

    start_time = time.perf_counter()

    try:
        params: dict[str, Any] = {
            "from": f"test@{settings.DOMAIN}",
            "to": [TEST_EMAIL],
            "subject": "Health Check - Amail",
            "html": "<p>Health check email</p>",
        }

        response = resend.Emails.send(params)
        duration_ms = (time.perf_counter() - start_time) * 1000

        metrics.email_health_check_total.labels(status="healthy").inc()

        return {
            "status": "healthy",
            "latency_ms": round(duration_ms, 2),
            "status_code": 200,
            "resend_id": response.get("id", ""),
            "test_email": TEST_EMAIL,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        error_msg = str(e)
        status_code = getattr(e, "status_code", 503)

        metrics.email_health_check_total.labels(status="unhealthy").inc()

        log.error(
            "email_health_check_failure",
            duration_ms=round(duration_ms, 2),
            error_message=error_msg,
            status_code=status_code,
        )

        raise HTTPException(
            status_code=status_code,
            detail={
                "status": "unhealthy",
                "latency_ms": round(duration_ms, 2),
                "error": error_msg,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
