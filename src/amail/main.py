"""Set up the Amail FastAPI application and register its routes."""

import os

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from amail.logging_config import configure_logging
from amail.providers.mock import MockProvider  # noqa: F401 - register provider
from amail.providers.resend import ResendProvider  # noqa: F401 - register provider
from amail.routes import health, messages

MAX_BODY_BYTES = 1 * 1024 * 1024  # 1 MB


class BodyLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests with a body larger than MAX_BODY_BYTES."""

    async def dispatch(
        self,
        request: Request,
        call_next: object,
    ) -> JSONResponse:
        """Check content-length before passing to the next handler."""
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_BODY_BYTES:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large"},
            )
        return await call_next(request)  # type: ignore[misc]


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    configure_logging()

    environment = os.environ.get("ENVIRONMENT", "development")
    api_key = os.environ.get("AMAIL_API_KEY", "")
    if environment != "development" and not api_key:
        raise RuntimeError(
            "AMAIL_API_KEY must be set in production. Generate with: "
            'python -c "import secrets; print(secrets.token_urlsafe(32))"'
        )

    application = FastAPI(
        title="Amail",
        description=(
            "Email microservice with FastAPI and Resend. "
            "Send, receive, and forward emails."
        ),
        version="1.1.0",  # x-release-please-version
    )

    application.add_middleware(BodyLimitMiddleware)
    application.include_router(health.router)
    application.include_router(messages.router)

    return application


app = create_app()
