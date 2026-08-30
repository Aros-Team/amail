# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Builder stage: materialize a `.venv` with all runtime dependencies via uv.
# uv is a build-only tool, pulled from its official image (not installed via
# pip), and is NOT carried into the runtime stage.
#
# Based on python:3.13-alpine (musl). Every C/Rust dependency ships a
# musllinux wheel, so no build toolchain (gcc/musl-dev) is needed — and if any
# ever did, a compiler would live in this stage only and never reach runtime.
# The runtime stage uses the SAME base so the `.venv` copied here is ABI
# compatible (musl system interpreter).
# ---------------------------------------------------------------------------
FROM python:3.13-alpine AS builder

# uv best practices: byte-compile wheels for faster cold starts, copy (not
# hardlink) into the venv so layers stay build-host-independent, and wipe the
# cache so no uv cache inflates later layers.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1

WORKDIR /app

# uv from its official image, pinned to the version that generated uv.lock (see
# `uv --version`) for reproducible builds — removes a full pip layer and keeps
# uv build-only.
COPY --from=ghcr.io/astral-sh/uv:0.11.6 /uv /uvx /bin/

# Install dependencies pinned to the frozen lockfile. The project itself is not
# installed (source is copied separately) and the dev group is excluded.
# --no-editable avoids editable-install symlinks inside the copied venv.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-group dev --no-editable

# ---------------------------------------------------------------------------
# Runtime stage: minimal, non-root, Alpine (musl) Python-only image. Same base
# as the builder for ABI compatibility.
# ---------------------------------------------------------------------------
FROM python:3.13-alpine AS runtime

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=src
ENV PATH="/app/.venv/bin:$PATH"
ENV HOME="/app"

WORKDIR /app

# Alpine's adduser flag for the shell is `-s`; nologin path is /sbin/nologin.
RUN addgroup --system --gid 10001 appuser \
    && adduser --system --uid 10001 --ingroup appuser --shell /sbin/nologin \
        --home /app appuser

# Copy ONLY what the app needs from the builder: the materialized virtualenv
# plus the application source. No uv, no uvx, no lockfile artifacts.
COPY --from=builder /app/.venv ./.venv
COPY src/amail ./src/amail

# The app is read-only at runtime (templates and models are only read; email
# rendering writes nothing), so give the non-root user ownership of the tree.
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Liveness probe only. Deliberately targets /health (the liveness endpoint),
# NOT /health/email, which sends a real test email and returns 503 when no
# routing-contract domain is configured. A production image must boot with no
# provider credentials, so container health here must not depend on them.
# Alpine has no curl; we use the venv's python with urllib, and no apk extras
# are added to runtime.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4); sys.exit(0)" || exit 1

CMD ["uvicorn", "amail.main:app", "--host", "0.0.0.0", "--port", "8000"]