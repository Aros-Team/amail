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
    
    timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    
    parts = [f"[{timestamp}]"]
    
    level_icons = {"info": "INFO ", "warning": "WARNING ", "error": "ERROR ", "success": "SUCCESS "}
    parts.append(level_icons.get(level, "•").upper())
    
    if event == "email_send_success":
        msg = f"Email sent successfully to {to}"
        if resend_id:
            msg += f" (resend_id: {resend_id})"
        if duration_ms:
            msg += f" in {duration_ms}ms"
        parts.append(msg)
        
    elif event == "email_send_failure":
        msg = f"Failed to send email to {to}"
        if error_type:
            msg += f" - {error_type}"
        if error_message:
            msg += f": {error_message}"
        if status_code:
            msg += f" (HTTP {status_code})"
        parts.append(msg)
        
    elif event == "email_send_with_retry_start":
        parts.append(f"Starting email send to {to} with {event_dict.get('max_attempts', 3)} attempts")
        
    elif event == "email_send_with_retry_success":
        parts.append(f"Email sent to {to} after retry attempt")
        
    elif event == "email_send_with_retry_failure":
        msg = f"Failed to send email to {to} after all retry attempts"
        if error_message:
            msg += f": {error_message}"
        parts.append(msg)
        
    elif event == "email_health_check_failure":
        msg = "Health check failed"
        if error_message:
            msg += f": {error_message}"
        if status_code:
            msg += f" (HTTP {status_code})"
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
