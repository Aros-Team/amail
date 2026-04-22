import time
from datetime import datetime, timezone
from typing import Any

import resend
from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.logging_config import get_logger

router = APIRouter(prefix="", tags=["health"])
log = get_logger(__name__)

TEST_EMAIL = "test@resend.dev"


@router.get("/health/email")
def email_health_check() -> dict[str, Any]:
    settings = get_settings()
    resend.api_key = settings.RESEND_API_KEY

    log.info(
        "email_health_check_start",
        domain=settings.DOMAIN,
        test_email=TEST_EMAIL,
    )

    start_time = time.perf_counter()

    try:
        params: dict[str, Any] = {
            "from": f"test@{settings.DOMAIN}",
            "to": [TEST_EMAIL],
            "subject": "Health Check - Amail",
            "html": "<p>Health check email</p>",
        }

        log.debug("email_health_check_sending", params_keys=list(params.keys()))
        response = resend.Emails.send(params)
        duration_ms = (time.perf_counter() - start_time) * 1000

        resend_id = response.get("id", "")
        log.info(
            "email_health_check_success",
            resend_id=resend_id,
            duration_ms=round(duration_ms, 2),
        )

        return {
            "status": "healthy",
            "latency_ms": round(duration_ms, 2),
            "status_code": 200,
            "resend_id": resend_id,
            "test_email": TEST_EMAIL,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        error_msg = str(e)
        error_repr = repr(e)
        status_code = getattr(e, "status_code", 503)

        log.error(
            "email_health_check_failure",
            duration_ms=round(duration_ms, 2),
            error_message=error_msg,
            error_repr=error_repr,
            error_type=type(e).__name__,
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
