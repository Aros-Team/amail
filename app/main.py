from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.logging_config import configure_logging
from app.routes import messages
from app.routes.health import router as health_router

configure_logging()

app = FastAPI(
    title="Amail",
    description="Email service with FastAPI and Resend",
    version="1.0.0",
)

app.include_router(messages.router)
app.include_router(health_router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
