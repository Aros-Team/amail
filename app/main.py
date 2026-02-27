from fastapi import FastAPI
from fastapi.security import HTTPBearer

from app.routes import messages
from app.security import create_access_token

security = HTTPBearer()

app = FastAPI(
    title="Amail",
    description="Email service with FastAPI and Resend",
    version="1.0.0",
)

app.include_router(messages.router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/api/token")
def get_token():
    token = create_access_token({"sub": "service"})
    return {"access_token": token, "token_type": "bearer"}
