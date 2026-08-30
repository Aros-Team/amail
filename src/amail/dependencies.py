"""FastAPI dependencies for request authentication and validation."""

import hmac
import os

from fastapi import HTTPException, Request


def require_api_key(request: Request) -> None:
    """Validate the X-API-Key header against the configured API key."""
    api_key = os.environ.get("AMAIL_API_KEY", "")
    header_key = request.headers.get("X-API-Key")
    if not header_key or not api_key or not hmac.compare_digest(header_key, api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
