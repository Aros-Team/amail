"""Set up the Amail FastAPI application and register its routes."""

from fastapi import FastAPI

from app.logging_config import configure_logging
from app.providers.mock import MockProvider  # noqa: F401 - register provider
from app.providers.resend import ResendProvider  # noqa: F401 - register provider
from app.routes import health, messages

configure_logging()

app = FastAPI(
    title="Amail",
    description=(
        "Email microservice with FastAPI and Resend. "
        "Send, receive, forward, and template emails."
    ),
    version="1.1.0",  # x-release-please-version
)

app.include_router(health.router)
app.include_router(messages.router)
