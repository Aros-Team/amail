from fastapi import FastAPI
from app.routes import email, webhook

app = FastAPI(
    title="Email Service",
    description="API de correo electrónico con FastAPI y Resend",
    version="1.0.0"
)

app.include_router(email.router)
app.include_router(webhook.router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}
