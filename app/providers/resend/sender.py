import time
import uuid
from typing import Any

import resend
from tenacity import retry
from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential

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


class ResendConnectionError(ResendAPIError):
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
            elif error_type == "connection_error":
                raise ResendConnectionError(**error_kwargs)
            else:
                raise ResendAPIError(**error_kwargs)

    def _parse_error(self, e: Exception) -> dict[str, Any]:
        error_msg = str(e)
        error_type = type(e).__name__
        status_code = getattr(e, "status_code", None)

        log.warning(
            "resend_error_parsing",
            error_type=error_type,
            error_msg=error_msg,
            status_code=status_code,
            error_repr=repr(e),
        )

        if status_code is None:
            error_lower = error_msg.lower()
            if "401" in error_msg or "unauthorized" in error_lower or "api key" in error_lower:
                status_code = 401
                error_type = "authentication_error"
            elif "429" in error_msg or "rate limit" in error_lower:
                status_code = 429
                error_type = "rate_limit"
            elif any(x in error_lower for x in ["connection", "timeout", "network", "dns", "refused", "ssl", "tls"]):
                status_code = None
                error_type = "connection_error"
            elif "attributeerror" in error_lower or "'dict' object" in error_lower or "'NoneType'" in error_lower:
                status_code = None
                error_type = "sdk_error"
            else:
                error_type = "unknown_error"

        reset_at = getattr(e, "reset_at", None)

        if status_code == 429:
            return {
                "message": error_msg,
                "status_code": status_code,
                "error_type": "rate_limit",
                "reset_at": reset_at,
            }

        if status_code in self.NON_RETRYABLE_ERRORS:
            if status_code == 401:
                return {"message": error_msg, "status_code": status_code, "error_type": "authentication_error"}
            if status_code == 400:
                return {"message": error_msg, "status_code": status_code, "error_type": "validation_error"}
            return {"message": error_msg, "status_code": status_code, "error_type": "client_error"}

        if status_code in self.RETRYABLE_ERRORS:
            return {"message": error_msg, "status_code": status_code, "error_type": "server_error"}

        if error_type == "connection_error":
            return {"message": error_msg, "status_code": None, "error_type": "connection_error"}

        if error_type == "sdk_error":
            return {"message": error_msg, "status_code": None, "error_type": "sdk_error"}

        return {"message": error_msg, "status_code": status_code, "error_type": error_type}

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

        attempt_counter = {"count": 0}

        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type((ResendRateLimitError, ResendServerError, ResendConnectionError)),
            before_sleep=lambda retry_state: log.warning(
                "email_send_retry",
                request_id=request_id,
                to=to,
                attempt=retry_state.attempt_number,
                max_attempts=max_attempts,
                wait_seconds=retry_state.next_action.sleep if retry_state.next_action else None,
            ),
        )
        def _send_with_retry() -> dict[str, Any]:
            attempt_counter["count"] += 1
            log.info("email_send_attempt", request_id=request_id, to=to, attempt=attempt_counter["count"])
            return self.send(to, subject, html, request_id=request_id)

        try:
            result = _send_with_retry()
            log.info(
                "email_send_with_retry_success",
                request_id=request_id,
                to=to,
            )
            return result
        except ResendRateLimitError as e:
            log.error(
                "email_send_rate_limited",
                request_id=request_id,
                to=to,
                status_code=e.status_code,
                reset_at=e.reset_at,
            )
            raise
        except ResendConnectionError as e:
            log.error(
                "email_send_connection_failed",
                request_id=request_id,
                to=to,
                error_message=e.message,
            )
            raise
        except Exception as e:
            error_info = self._parse_error(e)
            log.error(
                "email_send_with_retry_failure",
                request_id=request_id,
                to=to,
                error_type=error_info["error_type"],
                error_message=error_info["message"],
                status_code=error_info.get("status_code"),
            )
            raise


def get_resend_sender() -> ResendSender:
    return ResendSender()
