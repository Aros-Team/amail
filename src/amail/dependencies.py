"""FastAPI dependencies for request authentication and validation."""

import hmac
import os

from fastapi import HTTPException, Request

from amail.middleware.rate_limit import SlidingWindowRateLimiter


def require_api_key(request: Request) -> None:
    """Validate the X-API-Key header against the configured API key."""
    api_key = os.environ.get("AMAIL_API_KEY", "")
    header_key = request.headers.get("X-API-Key")
    if not header_key or not api_key or not hmac.compare_digest(header_key, api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def _env_int(name: str, default: int) -> int:
    """Read an integer from the environment, falling back to default."""
    try:
        return int(os.environ.get(name, str(default)))
    except (ValueError, TypeError):
        return default


def rate_limit_dependency(
    limiter: SlidingWindowRateLimiter,
    group: str,
    per_sec_env: str,
    per_sec_default: int,
    per_min_env: str,
    per_min_default: int,
) -> callable:
    """
    Create a dependency that enforces rate limits.

    Reads limits from env vars at request time so tests can patch them.
    """

    def _check(request: Request) -> None:
        per_sec = _env_int(per_sec_env, per_sec_default)
        per_min = _env_int(per_min_env, per_min_default)

        key_sec = f"{group}:sec"
        key_min = f"{group}:min"

        if not limiter.is_allowed(key_sec, per_sec, 1):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded (per second)",
                headers={"Retry-After": "1"},
            )
        if not limiter.is_allowed(key_min, per_min, 60):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded (per minute)",
                headers={"Retry-After": "60"},
            )

    return _check
