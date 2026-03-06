from fastapi import FastAPI

from app.routes import messages

app = FastAPI(
    title="Amail",
    description="Email service with FastAPI and Resend",
    version="1.0.0",
)

app.include_router(messages.router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}
