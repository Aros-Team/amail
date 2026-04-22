import logging
import sys
from datetime import datetime, timezone
from uuid import uuid4

import structlog
from structlog.typing import EventDict, WrappedLogger

from app.config import get_settings


def add_request_id(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    if "request_id" not in event_dict:
        event_dict["request_id"] = str(uuid4())
    return event_dict


def add_timestamp(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    event_dict["timestamp"] = datetime.now(timezone.utc).isoformat()
    return event_dict


def add_app_context(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    settings = get_settings()
    event_dict["environment"] = settings.ENVIRONMENT
    event_dict["service_version"] = settings.VERSION
    event_dict["service_name"] = "amail"
    return event_dict


def HumanReadableRenderer(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> str:
    event = event_dict.get("event", "")
    level = event_dict.get("level", "info")

    to = event_dict.get("to", "")
    duration_ms = event_dict.get("duration_ms")
    resend_id = event_dict.get("resend_id", "")
    error_message = event_dict.get("error_message", "")
    error_type = event_dict.get("error_type", "")
    status_code = event_dict.get("status_code")
    error_repr = event_dict.get("error_repr", "")
    request_id = event_dict.get("request_id", "")

    timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")

    parts = [f"[{timestamp}]"]

    level_icons = {"info": "INFO ", "warning": "WARN ", "error": "ERROR", "success": "OK    "}
    parts.append(level_icons.get(level, "•").upper())

    if event == "email_send_start":
        msg = f"Sending email to {to}"
        if request_id:
            msg += f" [req: {request_id[:8]}...]"
        parts.append(msg)

    elif event == "email_send_success":
        msg = f"Email sent to {to}"
        if resend_id:
            msg += f" (resend_id: {resend_id})"
        if duration_ms:
            msg += f" in {duration_ms}ms"
        parts.append(msg)

    elif event == "email_send_failure":
        msg = f"Failed to send email to {to}"
        if error_type:
            msg += f" | {error_type}"
        if error_message:
            msg += f" | {error_message}"
        if status_code:
            msg += f" | HTTP {status_code}"
        if error_repr and error_type in ("connection_error", "sdk_error", "unknown_error"):
            msg += f" | ex: {error_repr[:100]}"
        parts.append(msg)

    elif event == "email_send_with_retry_start":
        parts.append(f"Starting email send to {to} with {event_dict.get('max_attempts', 3)} attempts [req: {request_id[:8]}...]" if request_id else f"Starting email send to {to} with {event_dict.get('max_attempts', 3)} attempts")

    elif event == "email_send_attempt":
        parts.append(f"Email send attempt {event_dict.get('attempt', 0)} to {to}")

    elif event == "email_send_retry":
        parts.append(f"Retrying email to {to} (attempt {event_dict.get('attempt', 0)}/{event_dict.get('max_attempts', 3)}) after {event_dict.get('wait_seconds', 0):.1f}s")

    elif event == "email_send_with_retry_success":
        parts.append(f"Email sent to {to} after retry")

    elif event == "email_send_with_retry_failure":
        msg = f"Email failed to {to} after all retries"
        if error_type:
            msg += f" | {error_type}"
        if error_message:
            msg += f" | {error_message}"
        parts.append(msg)

    elif event in ("email_send_rate_limited", "email_send_connection_failed"):
        msg = f"Email send failed to {to} | {error_type}"
        if error_message:
            msg += f" | {error_message}"
        if event == "email_send_rate_limited" and event_dict.get("reset_at"):
            parts.append(msg + f" | retry after {event_dict['reset_at']}")
        else:
            parts.append(msg)

    elif event == "email_health_check_failure":
        msg = "Health check failed"
        if error_type:
            msg += f" | {error_type}"
        if error_message:
            msg += f" | {error_message}"
        if status_code:
            msg += f" | HTTP {status_code}"
        if error_repr:
            msg += f" | ex: {error_repr[:80]}"
        parts.append(msg)

    elif event == "resend_error_parsing":
        msg = f"Parsing Resend error: {error_type}"
        if error_repr:
            msg += f" | {error_repr[:80]}"
        parts.append(msg)

    else:
        msg = event.replace("_", " ").title()
        if to:
            msg += f" to {to}"
        parts.append(msg)

    return " ".join(parts)


def configure_logging() -> None:
    settings = get_settings()

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            add_request_id,
            add_timestamp,
            add_app_context,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            HumanReadableRenderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)
