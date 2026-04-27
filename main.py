from fastapi import FastAPI


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
