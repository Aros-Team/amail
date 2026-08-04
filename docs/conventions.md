# Conventions

> Style rules, naming, and structure. Follow exactly.

---

## 1. Python Style

- **Python 3.11+**, formatted and linted with `ruff`.
- Run `uv run ruff check .` — all checks must pass.
- Run `uv run ruff format .` before committing.
- Line length: 120 (ruff default `line-length` unless overridden).
- **Type hints on every function/method signature** (`from __future__ import annotations` where needed).
- No `print()` for debugging — use the structured logger (`get_logger(__name__)`).
- No TODOs without context.
- No dead code, unused imports, or unused parameters.

---

## 2. File & Module Naming

| Element | Convention | Example |
|---------|-----------|---------|
| Module | `snake_case.py` | `email_service.py`, `batch_reporter.py` |
| Package dir | `snake_case/` | `app/providers/resend/` |
| Class | `PascalCase` | `EmailService`, `ResendSender`, `EmailProvider` |
| Function/method | `snake_case` | `send_with_retry`, `build_failure_report` |
| Constant | `UPPER_SNAKE_CASE` | `TEMPLATES_DIR`, `SET_FORWARD_PREFIX` |
| Pydantic model | `PascalCase` | `EmailRequest`, `BatchReport` |

No `Service`/`Manager`/`Provider` suffixes on class names unless they describe a
real role (provider classes keep the suffix by design: `ResendProvider`).

---

## 3. Project Layout Conventions

- **Routes** live in `app/routes/`, one file per domain (`health.py`, `messages.py`).
  Every router is `APIRouter(prefix=..., tags=[...])`.
- **Services** live in `app/services/` — orchestrators (`email_service.py`),
  renderers (`templates.py`), reporting (`batch_reporter.py`).
- **Providers** live in `app/providers/<name>/` with `sender.py`, `receiver.py`,
  `errors.py`, `provider.py`, and an `__init__.py` that self-registers.
- **Models** live in `app/models/` (`schemas.py` for request/response,
  `errors.py` for error bodies).
- **Contracts** (Protocols) live in `app/contracts/`.

---

## 4. Providers

### Registry pattern

```python
# app/providers/<name>/__init__.py
from app.providers import register
from app.providers.<name>.provider import <Name>Provider

register("<name>", <Name>Provider)

__all__ = ["<Name>Provider"]
```

### Contracts

`EmailSender` and `EmailReceiver` are `typing.Protocol`s. Implement them with
matching signatures — no inheritance required.

### Sender signature (must match the Protocol)

```python
def send(
    self,
    to: list[str],
    subject: str,
    html: str,
    options: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]: ...
```

### Error mapping

Provider-specific errors subclass `app.exceptions.EmailError`. Resend wraps
HTTP/SDK failures into typed errors; classify into retryable vs non-retryable
and retry retryable ones. Never leak raw SDK exceptions to callers of the
service facade.

---

## 5. Services

- `EmailService` is the facade over the active provider. It normalizes
  single-vs-list recipients, merges template context, and returns
  `EmailResponse` instead of raising for send failures.
- Keep one responsibility per service file.
- Batch sends use best-effort semantics; on failures and if `ADMIN_EMAIL` is
  configured, forward an HTML failure report.

---

## 6. Pydantic Models

- Requests/responses are Pydantic `BaseModel` in `app/models/schemas.py`.
- Use `EmailStr` for email fields, `Field(...)` for defaults/validation.
- Define `response_model` on every route so OpenAPI is complete.
- Never reuse a mutable default for `dict`/`list` across instances — use
  `= {}`/`= []` only at the schema level (Pydantic copies these); for runtime
  mutable state use `None` + `or {}`.

---

## 7. Logging

Use structlog via `app.logging_config.get_logger(__name__)`.

```python
log = get_logger(__name__)
log.info("send_request", to=to_list, template=request.template)
log.error("email_send_error", error=str(e), to=to_list)
```

Rules:
- Event name first (snake_case), then key=value context.
- Include a `request_id` for sends so a single email can be traced end-to-end.
- Log durations (`duration_ms`) for external calls.
- No sensitive data in logs (never log full API keys or message bodies unless required).

---

## 8. Templates

- Jinja2 templates in `templates/`, one `<name>.html` per template type, macros
  in `templates/components/`.
- All template context flows through `build_base_context` — never hardcode
  branding text/colors in templates.
- Register new templates in `TEMPLATE_METADATA` in `services/templates.py`
  (description + variables) so `GET /api/v1/templates` stays accurate.
- User-visible strings are bilingual via `lang` (`es`/`en`), default `es`.

---

## 9. Routes

```python
@router.post(
    "/send",
    response_model=EmailResponse,
    summary="Send a single email",
    description="...",
    responses={400: {"model": ErrorDetail}, 500: {"model": ErrorDetail}},
)
def send_email(request: EmailRequest): ...
```

- Include `summary`, `description`, and `responses` on every route.
- Raise `HTTPException` for HTTP-level errors; keep business validation in schemas.
- Don't catch bare `Exception` and swallow it — log and translate to a meaningful error.
- Webhook verification failures → 400; missing receiver → 500.

---

## 10. Tests

- Follow `docs/testing.md` (Testing Policy) — a test's value is its ability to
  fail when the code is wrong (**mutation mindset**).
- `pytest` + `pytest-asyncio`; fixtures in `tests/conftest.py`.
- Mock provider boundaries (`MagicMock`, `patch("app.providers.resend.receiver.get_settings")`).
- Never make real network calls in tests.
- Name test functions `test_<unit>_<behavior>_<condition>` in `tests/test_*.py`.
- New functionality must have tests (happy + error + edge paths); run
  `uv run pytest` before declaring done.

---

## 11. What is NOT Allowed

- `print()` for debugging
- TODOs without context
- Unused imports / dead code
- Swallowing exceptions with no log
- Hardcoded branding in templates
- Real credentials committed (`.env` is gitignored)
- Route-level logic that belongs in services
