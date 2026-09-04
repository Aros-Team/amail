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
        """Check body size via Content-Length header or actual body read."""
        content_length = request.headers.get("content-length")

        # Case 1: Valid Content-Length — check it
        if content_length is not None:
            try:
                cl = int(content_length)
            except ValueError:
                cl = -1  # invalid = treat as too large
            if cl < 0 or cl > MAX_BODY_BYTES:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Request body too large"},
                )
            return await call_next(request)  # type: ignore[misc]

        # Case 2: No Content-Length — read body and check actual size
        body = await request.body()
        if len(body) > MAX_BODY_BYTES:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large"},
            )
        # Cache the consumed body so downstream handlers can re-read it
        request._body = body
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

    is_production = environment == "production"

    application = FastAPI(
        title="Amail",
        description=(
            "Email microservice with FastAPI and Resend. "
            "Send, receive, and forward emails."
        ),
        version="1.3.2",  # x-release-please-version
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
    )

    application.add_middleware(BodyLimitMiddleware)
    application.include_router(health.router)
    application.include_router(messages.router)

    return application


app = create_app()
