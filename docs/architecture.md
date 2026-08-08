# Architecture

> What "good work" means in this project.

---

## 1. Project Overview

Amail is a lightweight, self-hosted email microservice built with Python and
FastAPI, using Resend as the default provider. It sends, receives, forwards,
and templates emails through a simple REST API. Serverless-first: no databases,
no storage, no vendor lock-in.

---

## 2. Layering (one-way dependency)

Dependencies point one way only: **routes → services → providers**.

| Layer | Responsibility | Imports from |
|-------|---------------|--------------|
| `routes/` | HTTP surface, request validation, response models | services, models |
| `render/` | Template rendering seam: single swap point between engines | services/templates, models |
| `services/` | Business logic: orchestration, rendering, reporting | providers, models |
| `providers/` | External integrations (Resend/Mock), error mapping | contracts, config |
| `contracts/` | Protocol definitions — what a provider must implement | typing only |

Pattern rules:
- Routes never talk to Resend directly (exception: webhook signature
  verification in `messages.py`, which is pure crypto checking).
- Services never import HTTP-layer concerns.
- Providers never import routes or services (the receiver takes its sender via
  dependency injection, not by instantiating it).

---

## 3. Provider Registry Pattern

Providers are swappable via a small registry. This is the core extensibility
pattern of the project.

- A provider is a class implementing the `EmailProvider` ABC with `name`,
  `sender`, and optionally `receiver`.
- `EmailSender` and `EmailReceiver` are `typing.Protocol`s: any class with a
  matching method signature satisfies the contract — no inheritance required.
- Each provider self-registers in its package `__init__.py`:

```python
# app/providers/<name>/__init__.py
from app.providers import register
register("<name>", <Name>Provider)
```

- `main.py` imports every provider package so registration happens at startup.
- The active provider is resolved at runtime from `EMAIL_PROVIDER`:

```python
from app.providers import get_provider, get_sender, get_receiver

provider = get_provider()        # instance of the active provider
sender = provider.sender         # EmailSender
receiver = provider.receiver     # EmailReceiver | None
```

### Adding a new provider

1. Create `app/providers/<name>/` with a `sender` (and optionally a `receiver`)
   implementing the Protocols.
2. Define a `provider.py` subclassing `EmailProvider`.
3. Register it in the provider's `__init__.py`.
4. Keep the Mock provider in place so the app runs without credentials.

---

## 4. Error Handling Pattern

A typed error hierarchy rooted at `app.exceptions.EmailError`
(`message` + optional `status_code`).

- Provider-specific errors live beside the provider (`providers/resend/errors.py`)
  and subclass `EmailError`.
- The Resend sender classifies failures into:
  - **Retryable**: 429, 500, 502, 503, 504 → `ResendServerError` / `ResendRateLimitError`
  - **Non-retryable**: 400, 401, 403, 404 → `ResendAPIError` subclasses
  - **Connection / SDK / unknown** → `ResendConnectionError` and friends
- Retryable errors are retried with `tenacity` (exponential backoff, max 3
  attempts, `request_id` shared across attempts for traceability).

Boundary rules:
- `EmailService.send` never raises to the caller — it returns
  `EmailResponse(success=False, message=...)`; callers decide what to do.
- Routes translate failures into `HTTPException` with `ErrorDetail`-shaped bodies.
- Webhook signature failures → 400; missing receiver → 500.

---

## 5. Configuration Pattern

Configuration lives in the `app/config/` package and has two distinct layers:

1. **Environment settings** — a single Pydantic `Settings(BaseSettings)` class
   (`app/config/settings.py`), driven by env vars / `.env`, accessed through a
   cached accessor. Holds provider keys, provider selector, log level, etc.

   ```python
   from app.config import get_settings

   settings = get_settings()
   settings.resend_api_key, settings.email_provider, ...
   ```

2. **Routing contract** — a declarative YAML contract (`app/config/routing.py`)
   describing the email `domain`, accepted inbound addresses, and their forward
   targets, plus an optional fallback. Loaded and validated once per process
   (cached), with source precedence:

   - `AMAIL_ROUTES` — the YAML content as an env var / secret.
   - `AMAIL_ROUTES_FILE` — path to a YAML file.
   - `app/config/routes.yaml` — local development file (gitignored).

   ```python
   from app.config.routing import load_routing_config

   routing = load_routing_config()          # RoutingConfig | None
   routing.domain, routing.accepted_recipients, routing.resolve(recipients)
   ```

Rules:
- No `os.getenv` scattered through the code — values come from `Settings` or the
  routing contract loader.
- The `domain` lives in the routing contract (not an env var); it drives the
  default sender (`noreply@{domain}`) and `/health/email`.
- If the contract is absent or invalid, the loader logs an error at startup and
  returns `None`; health exposes this as "unhealthy" without crashing the app.
- Behavioral overrides (previously the `SET_FORWARD:` command) have been removed;
  forwarding is now fully declarative via the contract.

---

## 6. Template Rendering Pattern

Email markup is produced through a rendering seam `render/` that isolates the
engine behind one abstraction:

- `render/__init__.py` exposes `get_renderer()` — the **single swap point**. It
  currently returns `JinjaRenderer`, but any engine implementing the `Renderer`
  ABC (`render(name, data) -> html`, `get_templates()`) can be returned here
  without touching routes or services. Built to host a future Markdown engine.
- `render/jinja.py` (`JinjaRenderer`) wraps the Jinja2 engine via
  `services/templates.py` and maps `jinja2.TemplateNotFound` to the project
  `TemplateNotFoundError`, so the engine's internal error never leaks past the
  seam.
- `services/templates.py` is the Jinja2 implementation detail (still consumed
  by the seam and tests):
  - `render_template(name, data)` → rendered HTML
  - `build_base_context(data)` → extracts brand defaults (`brand_name`,
    `brand_color`, `logo_url`, `support_email`, `lang`) before passing user data
  - `get_templates()` → per-template metadata (description + variables)
- Every template has an entry in `TEMPLATE_METADATA` so
  `GET /api/v1/templates` stays accurate and the preview tool can auto-generate
  forms from it.
- Autoescaping is on for `html`/`xml`; the `custom` template opts in to raw HTML
  via `| safe`.
- No hardcoded branding — text/colors/images come from variables with defaults.
- Bilingual via `lang` (`es`/`en`, default `es`); inline CSS only.

---

## 7. Service Facade Pattern

`EmailService` is the single entry point for sending:

- Normalizes single-vs-list recipients (`to` accepts one or many).
- Merges template context (adds `lang`) and renders before calling the provider.
- Builds the provider `options` dict (`cc`, `bcc`, `reply_to`, `from_email`)
  only from present fields.
- Returns typed `EmailResponse` — never raises for send failures.

Batch sending (`send_batch`) is best-effort: it collects per-email results, and
if any failed and `ADMIN_EMAIL` is configured, it forwards an HTML failure
report via the active provider's sender.

---

## 8. HTTP / Webhook Pattern

- Every route sets `response_model`, `summary`, `description`, and `responses`
  so OpenAPI is complete.
- Incoming webhook: verify the Svix signature over the raw body first, then
  process the event; reject with 400 on any verification/parse failure.
- The receiver handles `email.received` events: filters by the accepted
  recipients from the routing contract, fetches content (with bounded retry),
  and forwards to the resolved the contract (rule match or fallback).
- Health endpoints never require provider credentials:
  - `/health` — liveness
  - `/health/email` — provider connectivity (sends to `test@resend.dev`);
    503 if no `domain` in the routing contract
  - `/health/webhook` — webhook secret configured; `routes_loaded: false` /
    `missing_routes` when no routing contract is present

---

## 9. Logging Pattern

Structured logging via structlog (`app/logging_config.get_logger(__name__)`).

```python
log = get_logger(__name__)
log.info("send_request", to=to_list, template=request.template)
```

- Event name first (snake_case), then `key=value` context.
- Send paths carry a shared `request_id` end-to-end; external calls log
  `duration_ms`.
- Never log secrets or full message bodies.

---

## 10. Testing Pattern

- `pytest` + `pytest-asyncio`, fixtures in `tests/conftest.py`.
- Provider boundaries are mocked (`MagicMock`, `patch(...)` on `get_settings`
  / sender classes) — no real network calls in tests.
- The harness (`scripts/harness.py`) is the quality gate: env, base files,
  activities.json, ruff, compile, pytest.

---

## 11. Project Goals

Every decision must contribute to building:

> **"A lightweight, self-hosted email microservice that is reliable, observable,
> and easy to extend with new providers and templates."**

This means:
- **Reliable**: retries, error classification, best-effort batches with admin reports
- **Observable**: structured logging with request ids and durations
- **Extensible**: provider registry, Protocol contracts, generic templates
- **Simple**: no databases, no storage, minimal surface area
