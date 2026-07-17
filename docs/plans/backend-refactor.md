# Amail Backend Refactor

> Plan to restructure amail into a clean, extensible email microservice with provider swappability, generic templates, batch sending, and documented APIs.

---

## 1. Objective

- Replace hardcoded env config with Pydantic `BaseSettings`
- Fix broken contract abstraction (Protocols actually used)
- Add provider registry pattern (Resend, Mock, future providers)
- Modular generic email templates (Jinja2 + components)
- Batch sending with best-effort + admin failure report
- Proper async in receive endpoint
- `/api/v1/*` routes with full OpenAPI documentation
- Comprehensive test suite
- Clean file structure, no typos, no dead code

---

## 2. Target Directory Structure

```
amail/
├── main.py
├── pyproject.toml
├── Dockerfile
├── .env.example
│
├── app/
│   ├── __init__.py
│   ├── config.py                  # Pydantic BaseSettings
│   ├── exceptions.py              # Centralized errors
│   ├── logging_config.py          # Keep, minor cleanup
│   │
│   ├── contracts/
│   │   ├── __init__.py
│   │   ├── sender.py              # Updated Protocol + typed dicts
│   │   └── receiver.py            # Updated Protocol
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schemas.py             # Updated Pydantic models
│   │   └── errors.py              # Error response schemas
│   │
│   ├── providers/
│   │   ├── __init__.py            # Registry: register(), get_provider()
│   │   ├── base.py                # EmailProvider ABC
│   │   │
│   │   ├── mock/
│   │   │   ├── __init__.py
│   │   │   └── provider.py        # MockSender + MockReceiver
│   │   │
│   │   └── resend/
│   │       ├── __init__.py
│   │       ├── sender.py          # Refactored: list[to], options
│   │       ├── receiver.py        # Refactored: async retry
│   │       └── errors.py          # Resend-specific error wrappers
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health.py              # Cleaned, documented
│   │   └── messages.py            # /api/v1/* with full docs
│   │
│   └── services/
│       ├── __init__.py
│       ├── email_service.py       # Facade: send, send_batch, receive
│       ├── templates.py           # Renderer, metadata, base context
│       └── batch_reporter.py      # Failure HTML report builder
│
├── templates/
│   ├── base.html
│   ├── components/
│   │   ├── button.html
│   │   ├── code_block.html
│   │   ├── notice.html
│   │   └── footer.html
│   ├── action.html
│   ├── notification.html
│   ├── verification.html
│   └── custom.html
│
└── tests/
    ├── conftest.py
    ├── test_sender.py
    ├── test_receiver.py
    ├── test_routes.py
    ├── test_templates.py
    ├── test_config.py
    └── test_batch_reporter.py
```

---

## 3. Config Migration

**Current:** `os.getenv` + manual class + `lru_cache`

**Target:** Pydantic `BaseSettings`

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    resend_api_key: str = ""
    resend_webhook_secret: str = ""
    domain: str = "aros.services"
    forward_to_email: str = ""
    admin_email: str = ""
    webhook_emails: list[str] = ["support", "noreply", "team"]
    email_provider: str = "resend"
    environment: str = "development"
    version: str = "1.0.0"
    log_level: str = "INFO"
    mock_send: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
```

### New env vars (.env.example)

| Var | Default | Description |
|-----|---------|-------------|
| `RESEND_API_KEY` | — | Resend API key |
| `RESEND_WEBHOOK_SECRET` | — | Resend webhook secret |
| `DOMAIN` | `aros.services` | Verified domain |
| `FORWARD_TO_EMAIL` | — | Default forward target |
| `ADMIN_EMAIL` | — | Email for batch failure reports |
| `EMAIL_PROVIDER` | `resend` | Active provider (`resend` / `mock`) |
| `ENVIRONMENT` | `development` | Runtime env |
| `LOG_LEVEL` | `INFO` | Logging level |
| `VERSION` | `1.0.0` | Service version |

### Add dependency

```toml
pydantic-settings>=2.0
```

---

## 4. Contracts Layer

### `contracts/sender.py`

```python
from typing import Protocol, TypedDict, Literal

class SendOptions(TypedDict, total=False):
    cc: list[str]
    bcc: list[str]
    reply_to: str
    from_email: str

class EmailSender(Protocol):
    def send(self, to: list[str], subject: str, html: str,
             options: SendOptions | None = None) -> dict: ...
```

### `contracts/receiver.py`

```python
from typing import Protocol

class EmailReceiver(Protocol):
    def receive(self, payload: dict) -> dict: ...
```

---

## 5. Models

### `models/schemas.py`

```python
class EmailRequest(BaseModel):
    to: EmailStr | list[EmailStr]
    subject: str
    template: str
    data: dict[str, Any] = {}
    cc: list[EmailStr] | None = None
    bcc: list[EmailStr] | None = None
    reply_to: EmailStr | None = None
    from_email: EmailStr | None = None
    lang: str = Field(default="es", pattern="^(es|en)$")

class BatchEmailRequest(BaseModel):
    emails: list[EmailRequest]
    parallel: bool = True
    continue_on_error: bool = True

class EmailResponse(BaseModel):
    success: bool
    message: str
    email_id: str | None = None
    request_id: str | None = None
    to: str | None = None

class BatchReport(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: list[EmailResponse]
    forwarded_to_admin: bool
    admin_email: str | None = None

class TemplateVariable(BaseModel):
    name: str
    type: str
    description: str
    required: bool

class TemplateInfo(BaseModel):
    name: str
    description: str
    variables: list[TemplateVariable]

class TemplatesResponse(BaseModel):
    templates: list[TemplateInfo]

class WebhookPayload(BaseModel):
    type: str
    data: dict[str, Any] = {}
```

### App-level exceptions (`app/exceptions.py`)

```python
class EmailError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class EmailAuthError(EmailError): ...
class EmailRateLimitError(EmailError): ...
class EmailServerError(EmailError): ...
class EmailConnectionError(EmailError): ...
class EmailValidationError(EmailError): ...
```

---

## 6. Provider System

### Registry Pattern (`providers/__init__.py`)

```python
_registry: dict[str, type["EmailProvider"]] = {}

def register(name: str, cls: type["EmailProvider"]) -> None:
    _registry[name] = cls

def get_provider(name: str | None = None) -> "EmailProvider":
    from app.config import get_settings
    provider_name = name or get_settings().email_provider
    if provider_name not in _registry:
        raise ValueError(f"Unknown provider: {provider_name}")
    return _registry[provider_name]()

def get_sender() -> "EmailSender":
    return get_provider().sender

def get_receiver() -> "EmailReceiver | None":
    return get_provider().receiver
```

### Base ABC (`providers/base.py`)

```python
from abc import ABC, abstractmethod
from app.contracts.sender import EmailSender
from app.contracts.receiver import EmailReceiver

class EmailProvider(ABC):
    name: str
    sender: EmailSender
    receiver: EmailReceiver | None = None
```

### Registration

Each provider's `__init__.py` registers itself:

```python
# providers/resend/__init__.py
from app.providers import register
from app.providers.resend.provider import ResendProvider
register("resend", ResendProvider)

# providers/mock/__init__.py
from app.providers import register
from app.providers.mock.provider import MockProvider
register("mock", MockProvider)
```

### Mock Provider (`providers/mock/provider.py`)

- `MockSender`: logs every `send()` call, returns `{id: "mock_<uuid>", ...}`
- `MockReceiver`: returns `{status: "forwarded"}` for `email.received`, `{status: "ignored"}` for others
- No API calls, no credentials needed

---

## 7. Resend Provider Refactor

### `providers/resend/errors.py`

Move custom error classes here:
- `ResendAPIError`, `ResendRateLimitError`, `ResendServerError`, `ResendConnectionError`
- Inherit from `app.exceptions.EmailError`

### `providers/resend/sender.py`

Changes:
- `to` param becomes `list[str]` (caller normalizes single → list)
- `SendOptions` unpacked: `cc`, `bcc`, `reply_to`, `from_email`
- Error mapping simplified
- `send_with_retry()` stays (tenacity-based)

### `providers/resend/receiver.py`

Changes:
- `_get_email_content()` uses `httpx.AsyncClient` or properly async retry
- Remove `time.sleep(2)` — replace with `asyncio.sleep()` or tenacity async retry
- Keep `SET_FORWARD:` email command feature
- Receives sender via DI (from provider), not instantiates `ResendSender()` directly

### `providers/resend/provider.py`

```python
from app.providers.base import EmailProvider
from app.providers.resend.sender import ResendSender
from app.providers.resend.receiver import ResendReceiver

class ResendProvider(EmailProvider):
    name = "resend"
    sender = ResendSender()
    receiver = ResendReceiver()
```

---

## 8. Template System

### Template files

```
templates/
├── base.html                    # Shell: html/head/body, bilingual header/footer, inline CSS
├── components/
│   ├── button.html              # cta_button(text, url, color)
│   ├── code_block.html          # code_block(code)
│   ├── notice.html              # notice_box(message)
│   └── footer.html              # support_footer(email, lang)
├── action.html                  # CTA email (welcome, reset, invite)
├── notification.html            # Alert email
├── verification.html            # Code email (2FA)
└── custom.html                  # Passthrough: user supplies raw body
```

### Design principles

- No hardcoded branding — all text/colors/images via variables
- Neutral defaults: clean blue/gray palette
- Inline CSS only (email client compatibility)
- Bilingual via `lang` variable (`es` / `en`)
- Variables always have sensible defaults

### `templates/base.html`

```html
<!DOCTYPE html>
<html lang="{{ lang | default('es') }}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}{{ brand_name | default('') }}{% endblock %}</title>
  <style>
    /* Reset + base styles */
    body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;
           padding: 20px; background-color: #f4f4f5; }
    /* ... all inline-compatible CSS ... */
  </style>
</head>
<body>
  {% block header %}
  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px;">
    <h1 style="color:{{ brand_color | default('#1a73e8') }}; font-size:1.5rem;">
      {{ brand_name | default('') }}
    </h1>
    {% if logo_url %}
    <img src="{{ logo_url }}" alt="Logo" width="48" style="display:block;">
    {% endif %}
  </div>
  {% endblock %}

  {% block content %}{% endblock %}

  {% block footer %}
  <hr style="border:none; border-top:1px solid #e0e0e0; margin-top:32px;">
  {% if lang == "en" %}
  <p style="color:#666; font-size:12px; text-align:center;">
    Need help? <a href="mailto:{{ support_email | default('support@example.com') }}" style="color:{{ brand_color | default('#1a73e8') }};">{{ support_email | default('support@example.com') }}</a>
  </p>
  {% else %}
  <p style="color:#666; font-size:12px; text-align:center;">
    ¿Necesitas ayuda? <a href="mailto:{{ support_email | default('support@example.com') }}" style="color:{{ brand_color | default('#1a73e8') }};">{{ support_email | default('support@example.com') }}</a>
  </p>
  {% endif %}
  {% endblock %}
</body>
</html>
```

### Components (Jinja2 macros)

**`components/button.html`:**
```html
{% macro cta_button(text, url, color="#1a73e8") %}
<div style="text-align:center; margin:24px 0;">
  <a href="{{ url }}" style="display:inline-block; background-color:{{ color }};
    color:#fff; padding:14px 32px; border-radius:6px; text-decoration:none;
    font-weight:bold; font-size:16px;">{{ text }}</a>
</div>
{% endmacro %}
```

**`components/code_block.html`:**
```html
{% macro code_block(code) %}
<div style="background:#f0f0f0; padding:20px; border-radius:8px; text-align:center; margin:24px 0;">
  <span style="font-size:36px; font-weight:bold; color:#333; letter-spacing:8px; font-family:monospace;">
    {{ code }}
  </span>
</div>
{% endmacro %}
```

### Template-specific files

**`action.html`** — for welcome, password reset, employee invitation:
```html
{% extends "base.html" %}
{% from "components/button.html" import cta_button %}
{% from "components/notice.html" import notice_box %}

{% block content %}
<p style="color:#333; font-size:16px; line-height:1.5;">{{ message }}</p>

{% if cta_text and cta_url %}
  {{ cta_button(cta_text, cta_url, brand_color | default('#1a73e8')) }}
  {% if expiry %}
  <p style="color:#888; font-size:11px; text-align:center;">
    {% if lang == "en" %}This link expires in{% else %}Este enlace expira en{% endif %}
    <strong>{{ expiry }}</strong>
  </p>
  {% endif %}
{% endif %}

{% if notification %}
  {{ notice_box(notification.message if notification is mapping else notification) }}
{% endif %}
{% endblock %}
```

**`notification.html`:**
```html
{% extends "base.html" %}

{% block content %}
<h2 style="color:#333; font-size:18px;">{{ heading }}</h2>
<p style="color:#333; font-size:16px; border-left:4px solid {{ brand_color | default('#1a73e8') }}; padding-left:15px; line-height:1.5;">
  {{ message }}
</p>
{% if details %}
<ul style="color:#555; font-size:14px;">
  {% for key, value in details.items() %}
  <li><strong>{{ key }}:</strong> {{ value }}</li>
  {% endfor %}
</ul>
{% endif %}
{% endblock %}
```

**`verification.html`:**
```html
{% extends "base.html" %}
{% from "components/code_block.html" import code_block %}

{% block content %}
<p style="color:#333; font-size:16px; text-align:center;">
  {% if lang == "en" %}Use this code to complete your verification:{% else %}Usa este código para verificar tu identidad:{% endif %}
</p>
{{ code_block(code) }}
{% if expiry %}
<p style="color:#888; font-size:12px; text-align:center;">
  {% if lang == "en" %}Expires in{% else %}Expira en{% endif %} <strong>{{ expiry }}</strong>
</p>
{% endif %}
<p style="color:#888; font-size:12px; text-align:center;">
  {% if lang == "en" %}If you didn't request this, you can safely ignore it.{% else %}Si no solicitaste esto, puedes ignorarlo con seguridad.{% endif %}
</p>
{% endblock %}
```

**`custom.html`:**
```html
{% extends "base.html" %}
{% block content %}{{ content | safe }}{% endblock %}
```

### Template service (`services/templates.py`)

```python
from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"])
)

def render_template(template_name: str, data: dict) -> str:
    template = env.get_template(f"{template_name}.html")
    context = build_base_context(data)
    return template.render(**context)

def build_base_context(data: dict) -> dict:
    return {
        "brand_name": data.pop("brand_name", ""),
        "brand_color": data.pop("brand_color", "#1a73e8"),
        "logo_url": data.pop("logo_url", None),
        "support_email": data.pop("support_email", "support@example.com"),
        "lang": data.pop("lang", "es"),
        **data,
    }

TEMPLATE_METADATA = {
    "action": {
        "description": "Call-to-action email (welcome, password reset, invitation)",
        "variables": [
            TemplateVariable("message", "string", "Main message body", True),
            TemplateVariable("cta_text", "string", "Button label", False),
            TemplateVariable("cta_url", "string", "Button URL", False),
            TemplateVariable("expiry", "string", "Expiration time", False),
            TemplateVariable("notification", "object", "Additional notice", False),
        ],
    },
    "notification": {
        "description": "General notification or alert",
        "variables": [
            TemplateVariable("heading", "string", "Notification heading", False),
            TemplateVariable("message", "string", "Content body", True),
            TemplateVariable("details", "object", "Key-value detail list", False),
        ],
    },
    "verification": {
        "description": "Verification or one-time code",
        "variables": [
            TemplateVariable("code", "string", "Verification code", True),
            TemplateVariable("expiry", "string", "Expiration time", False),
        ],
    },
    "custom": {
        "description": "Custom raw HTML content wrapped in base layout",
        "variables": [
            TemplateVariable("content", "string", "Raw HTML body content", True),
        ],
    },
}
```

---

## 9. Email Service Facade

### `services/email_service.py`

```python
class EmailService:
    def __init__(self, provider: EmailProvider | None = None):
        from app.providers import get_provider
        self._provider = provider or get_provider()
        self.sender = self._provider.sender
        self.receiver = self._provider.receiver

    def send(self, req: EmailRequest) -> EmailResponse: ...
    def send_batch(self, req: BatchEmailRequest) -> BatchReport: ...
    def receive_webhook(self, payload: dict) -> dict: ...
```

### Batch sending flow

```
send_batch(req):
  1. results = []
  2. For each email in req.emails:
     - try send(email)
     - append EmailResponse(success=True, ...) or EmailResponse(success=False, ...)
     - if not req.continue_on_error: break
  3. report = BatchReport(total=..., succeeded=..., failed=..., results=..., ...)
  4. If report.failed > 0 and ADMIN_EMAIL is set:
     - build_failure_report(report)  → HTML
     - send to ADMIN_EMAIL via self.sender
     - report.forwarded_to_admin = True
  5. Return report
```

---

## 10. Batch Reporter

### `services/batch_reporter.py`

```python
def build_failure_report(results: list[EmailResponse]) -> str:
    """Build HTML table of failed sends."""
    failed = [r for r in results if not r.success]
    if not failed:
        return ""
    # Build HTML table with: recipient, template, error, timestamp
    rows = "".join(
        f"<tr><td>{r.to}</td><td>{r.message}</td></tr>"
        for r in failed
    )
    return f"""<!DOCTYPE html><html><body>
    <h2>Batch Send Failure Report</h2>
    <table border="1" cellpadding="8"><tr><th>To</th><th>Error</th></tr>{rows}</table>
    </body></html>"""

def send_failure_report(report_html: str, admin_email: str, sender) -> None:
    """Send failure report to ADMIN_EMAIL via the provider's sender."""
    sender.send(
        to=[admin_email],
        subject="[Amail] Batch Send Failure Report",
        html=report_html,
    )
```

---

## 11. Routes

### `routes/messages.py`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/send` | Send a single email (accepts `list[to]` internally) |
| `POST` | `/api/v1/send/batch` | Send multiple emails, best-effort, admin report on failure |
| `GET` | `/api/v1/templates` | List available templates with variable metadata |
| `POST` | `/api/v1/receive` | Resend webhook receiver (forward + SET_FORWARD command) |

Each endpoint includes:
- `summary`, `description`, `response_description`
- `response_model` with proper Pydantic schema
- `responses` dict with error schemas (400, 401, 500)
- FastAPI tags `["messages"]`

### `routes/health.py`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Simple alive check |
| `GET` | `/health/email` | Email provider connectivity test |
| `GET` | `/health/webhook` | Webhook secret configured check |

### `main.py`

```python
from fastapi import FastAPI
from app.logging_config import configure_logging
from app.routes import messages, health

configure_logging()

app = FastAPI(
    title="Amail",
    description="Email microservice with FastAPI and Resend. Send, receive, forward, and template emails.",
    version="1.0.0",
)

app.include_router(health.router)
app.include_router(messages.router)
```

No duplicate `/health` — all routes via routers.

---

## 12. Test Plan

| File | Tests |
|------|-------|
| `conftest.py` | Shared fixtures: `mock_settings`, `mock_sender`, `mock_receiver`, `test_client` |
| `test_config.py` | Settings from env, validation, defaults, override |
| `test_sender.py` | `ResendSender.send()`, `send_with_retry()`, error parsing, rate limit, connection error |
| `test_receiver.py` | Existing + expand: `SET_FORWARD`, no content fallback, ignored events, allowed emails |
| `test_routes.py` | All endpoints via `TestClient`: 200, 400, 500 responses, webhook verification |
| `test_templates.py` | Render each template type, variable substitution, base context defaults, bilingual |
| `test_batch_reporter.py` | Report building, empty report, admin forward trigger |

---

## 13. File Cleanup

- Remove duplicate `TemplateVariable` class from `services/templates.py` (keep Pydantic version)
- Remove `providers/__init__.py` re-exports of contracts (import from `contracts` directly where needed)
- Fix any typos in comments and variable names
- Remove unused imports throughout
- Consistent formatting (already using `ruff`, run full pass)

---

## 14. Execution Order

```
Step 1:  Pydantic BaseSettings + exceptions module
Step 2:  Contracts (updated Protocols)
Step 3:  Models (updated schemas, remove duplicate)
Step 4:  Provider registry + base ABC
Step 5:  Mock provider
Step 6:  Resend provider refactor + errors split
Step 7:  Template system (base.html, components, 4 templates)
Step 8:  Template service (renderer, metadata, context builder)
Step 9:  Email service facade + batch reporter
Step 10: Routes (v1 prefix, docs) + main.py cleanup
Step 11: Tests
Step 12: Dockerfile simplification
```
