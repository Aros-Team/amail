"""Tests for BodyLimitMiddleware hardening."""

from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from amail.main import MAX_BODY_BYTES, BodyLimitMiddleware

# ---------------------------------------------------------------------------
# Minimal test app — one POST endpoint that reads the body and returns 200
# ---------------------------------------------------------------------------


def _create_app() -> FastAPI:
    """Create a minimal FastAPI app with the BodyLimitMiddleware."""
    application = FastAPI()
    application.add_middleware(BodyLimitMiddleware)

    @application.post("/echo")
    async def echo(request: Request) -> JSONResponse:
        """Read the body and return its length."""
        body = await request.body()
        return JSONResponse(content={"length": len(body)})

    return application


app = _create_app()

# ---------------------------------------------------------------------------
# Helpers — raw ASGI dispatch to control headers precisely
# ---------------------------------------------------------------------------


async def _dispatch_raw(
    headers: list[tuple[bytes, bytes]],
    body: bytes,
) -> tuple[int, dict[str, Any]]:
    """
    Dispatch a raw ASGI request through the middleware stack.

    Returns (status_code, response_json).
    """
    received = False

    async def _receive() -> dict[str, Any]:
        """Return the body as a single ASGI message."""
        nonlocal received
        if not received:
            received = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    sent: list[dict[str, Any]] = []

    async def _send(message: dict[str, Any]) -> None:
        """Collect sent messages (response headers + body)."""
        sent.append(message)

    scope: dict[str, Any] = {
        "type": "http",
        "method": "POST",
        "path": "/echo",
        "query_string": b"",
        "headers": headers,
        "server": ("testserver", 80),
        "client": ("testclient", 12345),
        "app": app,
    }

    # Build the ASGI app with middleware
    from starlette.routing import Route, Router

    async def _endpoint(request: Request) -> JSONResponse:
        """Inner handler: read body and return its length."""
        body_bytes = await request.body()
        return JSONResponse(content={"length": len(body_bytes)})

    route = Route("/echo", _endpoint, methods=["POST"])
    inner_app = Router(routes=[route])

    # Wrap with middleware
    middleware = BodyLimitMiddleware(app=inner_app)  # type: ignore[arg-type]
    await middleware(scope, _receive, _send)

    # Extract status code and body from ASGI messages
    status = 200
    body_chunks: list[bytes] = []
    for msg in sent:
        if msg["type"] == "http.response.start":
            status = msg["status"]
        elif msg["type"] == "http.response.body":
            body_chunks.append(msg.get("body", b""))

    return status, json.loads(b"".join(body_chunks))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_body_limit_small_body_passes() -> None:
    """POST with valid Content-Length under limit should return 200."""
    body = b"x" * 100
    status, data = await _dispatch_raw(
        headers=[
            (b"host", b"testserver"),
            (b"content-length", str(len(body)).encode()),
        ],
        body=body,
    )
    assert status == 200
    assert data["length"] == 100


@pytest.mark.anyio
async def test_body_limit_oversized_content_length_rejected() -> None:
    """POST with Content-Length above MAX_BODY_BYTES should return 413."""
    status, data = await _dispatch_raw(
        headers=[
            (b"host", b"testserver"),
            (b"content-length", str(MAX_BODY_BYTES + 1).encode()),
        ],
        body=b"x",
    )
    assert status == 413
    assert data["detail"] == "Request body too large"


@pytest.mark.anyio
async def test_body_limit_invalid_content_length_rejected() -> None:
    """POST with non-numeric Content-Length should return 413, not 500."""
    status, data = await _dispatch_raw(
        headers=[
            (b"host", b"testserver"),
            (b"content-length", b"not-a-number"),
        ],
        body=b"x",
    )
    assert status == 413
    assert data["detail"] == "Request body too large"


@pytest.mark.anyio
async def test_body_limit_missing_content_length_small_body_passes() -> None:
    """POST without Content-Length header but small body should pass."""
    status, data = await _dispatch_raw(
        headers=[
            (b"host", b"testserver"),
            (b"content-type", b"application/octet-stream"),
            # No Content-Length header
        ],
        body=b"small",
    )
    assert status == 200
    assert data["length"] == 5


@pytest.mark.anyio
async def test_body_limit_missing_content_length_oversized_body_rejected() -> None:
    """POST without Content-Length but oversized body should return 413."""
    large_body = b"x" * (MAX_BODY_BYTES + 1)
    status, data = await _dispatch_raw(
        headers=[
            (b"host", b"testserver"),
            (b"content-type", b"application/octet-stream"),
            # No Content-Length header — must still enforce limit
        ],
        body=large_body,
    )
    assert status == 413
    assert data["detail"] == "Request body too large"


@pytest.mark.anyio
async def test_body_limit_chunked_oversized_body_rejected() -> None:
    """POST with Transfer-Encoding: chunked and oversized body should 413."""
    large_body = b"x" * (MAX_BODY_BYTES + 1)
    status, data = await _dispatch_raw(
        headers=[
            (b"host", b"testserver"),
            (b"transfer-encoding", b"chunked"),
            (b"content-type", b"application/octet-stream"),
            # No Content-Length — chunked transfer
        ],
        body=large_body,
    )
    assert status == 413
    assert data["detail"] == "Request body too large"
