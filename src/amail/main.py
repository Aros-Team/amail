"""Set up the Amail FastAPI application and register its routes."""

from fastapi import FastAPI

from amail.logging_config import configure_logging
from amail.providers.mock import MockProvider  # noqa: F401 - register provider
from amail.providers.resend import ResendProvider  # noqa: F401 - register provider
from amail.routes import health, messages


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    configure_logging()

    application = FastAPI(
        title="Amail",
        description=(
            "Email microservice with FastAPI and Resend. "
            "Send, receive, and forward emails."
        ),
        version="1.1.0",  # x-release-please-version
    )

    application.include_router(health.router)
    application.include_router(messages.router)

    return application


app = create_app()
