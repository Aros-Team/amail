import time
import uuid
from typing import Any

import resend
from tenacity import retry
from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential

from app import metrics
from app.config import get_settings
from app.logging_config import get_logger

log = get_logger(__name__)


class ResendAPIError(Exception):
    def __init__(self, message: str, status_code: int | None = None, error_type: str = "unknown"):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        super().__init__(message)


class ResendRateLimitError(ResendAPIError):
    def __init__(self, message: str, status_code: int | None = None, reset_at: int | None = None):
        super().__init__(message, status_code, "rate_limit")
        self.reset_at = reset_at


class ResendServerError(ResendAPIError):
    pass


class ResendSender:
    RETRYABLE_ERRORS = (429, 500, 502, 503, 504)
    NON_RETRYABLE_ERRORS = (400, 401, 403, 404)

    def __init__(self) -> None:
        settings = get_settings()
        resend.api_key = settings.RESEND_API_KEY
        self.settings = settings

    def send(self, to: str, subject: str, html: str, request_id: str | None = None) -> dict[str, Any]:
        from_email = f"noreply@{self.settings.DOMAIN}"
        req_id = request_id or str(uuid.uuid4())

        log.info(
            "email_send_start",
            request_id=req_id,
            to=to,
            subject=subject[:100] if subject else "",
        )

        start_time = time.perf_counter()

        try:
            params: dict[str, Any] = {
                "from": from_email,
                "to": [to],
                "subject": subject,
                "html": html,
            }

            response = resend.Emails.send(params)
            duration_ms = (time.perf_counter() - start_time) * 1000

            email_id = response.get("id", "")

            log.info(
                "email_send_success",
                request_id=req_id,
                to=to,
                duration_ms=round(duration_ms, 2),
                resend_id=email_id,
            )

            metrics.email_send_total.labels(status="success").inc()
            metrics.email_send_duration_seconds.observe(duration_ms / 1000)

            return {"id": email_id, "request_id": req_id}

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            error_info = self._parse_error(e)

            log.error(
                "email_send_failure",
                request_id=req_id,
                to=to,
                duration_ms=round(duration_ms, 2),
                error_type=error_info["error_type"],
                error_message=error_info["message"],
                status_code=error_info.get("status_code"),
            )

            metrics.email_send_total.labels(status="failure").inc()
            metrics.email_send_by_error_type.labels(error_type=error_info["error_type"]).inc()
            metrics.email_send_duration_seconds.observe(duration_ms / 1000)

            error_type = error_info["error_type"]
            error_kwargs = {
                "message": error_info["message"],
                "status_code": error_info.get("status_code"),
                "error_type": error_type,
            }
            
            if error_type == "rate_limit":
                raise ResendRateLimitError(**error_kwargs)
            elif error_type == "server_error":
                raise ResendServerError(**error_kwargs)
            else:
                raise ResendAPIError(**error_kwargs)

    def _parse_error(self, e: Exception) -> dict[str, Any]:
        error_msg = str(e)
        status_code = getattr(e, "status_code", None)
        
        if status_code is None:
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                status_code = 401
            elif "429" in error_msg or "rate limit" in error_msg.lower():
                status_code = 429

        if status_code == 429:
            reset_at = getattr(e, "reset_at", None)
            if reset_at:
                metrics.resend_rate_limit_remaining.set(0)
                metrics.resend_rate_limit_reset.set(reset_at)
            return {
                "message": error_msg,
                "status_code": status_code,
                "error_type": "rate_limit",
            }

        if status_code in self.RETRYABLE_ERRORS:
            return {"message": error_msg, "status_code": status_code, "error_type": "server_error"}

        if status_code == 401:
            return {"message": error_msg, "status_code": status_code, "error_type": "authentication_error"}

        if status_code == 400:
            return {"message": error_msg, "status_code": status_code, "error_type": "validation_error"}

        return {"message": error_msg, "status_code": status_code, "error_type": type(e).__name__}

    def send_with_retry(
        self,
        to: str,
        subject: str,
        html: str,
        max_attempts: int = 3,
    ) -> dict[str, Any]:
        request_id = str(uuid.uuid4())

        log.info(
            "email_send_with_retry_start",
            request_id=request_id,
            to=to,
            max_attempts=max_attempts,
        )

        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type((ResendRateLimitError, ResendServerError)),
        )
        def _send_with_retry() -> dict[str, Any]:
            return self.send(to, subject, html, request_id=request_id)

        try:
            result = _send_with_retry()
            log.info(
                "email_send_with_retry_success",
                request_id=request_id,
                to=to,
            )
            return result
        except Exception as e:
            log.error(
                "email_send_with_retry_failure",
                request_id=request_id,
                to=to,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            raise


def get_resend_sender() -> ResendSender:
    return ResendSender()
