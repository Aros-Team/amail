# AGENTS.md - Email Service

This document provides guidelines for agentic coding agents working on this codebase.

## Project Overview

- **Type**: Python/FastAPI REST API
- **Purpose**: Email service with templates using Resend API
- **Python Version**: 3.12+
- **Framework**: FastAPI

## Build & Development Commands

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Development Server
```bash
uvicorn app.main:app --reload --port 8000
```

### Run with Docker
```bash
docker build -t email-service .
docker run -p 8000:8000 --env-file .env email-service
```

### Run Tests
No test framework is currently configured. If tests are added:
```bash
pytest                    # Run all tests
pytest path/to/test.py    # Run specific test file
pytest -k test_name       # Run tests matching pattern
pytest -v                # Verbose output
pytest --cov=app         # With coverage
```

### Linting & Type Checking
If ruff is added (recommended):
```bash
ruff check .              # Lint all files
ruff check app/main.py    # Lint specific file
ruff format .             # Format all files
```

If mypy is added:
```bash
mypy app/                # Type check app directory
```

## Code Style Guidelines

### Imports
- Standard library imports first, then third-party, then local
- Use absolute imports with `app.` prefix: `from app.routes import email`
- Group imports by type with blank lines between groups
- Sort imports alphabetically within groups

```python
# Correct
from functools import lru_cache
from os import getenv

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import get_settings
from app.models.schemas import EmailRequest
```

### Formatting
- Line length: 88 characters (Black default)
- Use 4 spaces for indentation
- Use trailing commas where practical
- Use f-strings for string formatting

### Types
- Use Python 3.12+ native type hints: `list[str]` instead of `List[str]`
- Use `| None` instead of `Optional[]` for simple cases
- Use Pydantic for request/response validation models
- Add type hints to all function parameters and return values

```python
# Good
def render_template(template_name: str, data: dict[str, Any]) -> str:
    ...

# Avoid
def render_template(template_name, data):  # No type hints
```

### Naming Conventions
- **Classes**: `PascalCase` (e.g., `EmailRequest`, `ResendClient`)
- **Functions/variables**: `snake_case` (e.g., `send_email`, `html_content`)
- **Constants**: `SCREAMING_SNAKE_CASE` (e.g., `TEMPLATES_DIR`)
- **Modules**: `snake_case` (e.g., `resend_client.py`)
- **Routes**: Use descriptive names, plural for collections (`/api/templates`)

### Error Handling
- Use FastAPI's `HTTPException` for HTTP-level errors
- Include descriptive error messages in exceptions
- Catch specific exceptions rather than bare `except:`
- Return appropriate HTTP status codes (400 for bad request, 500 for server errors)

```python
# Good
if request.template not in templates:
    raise HTTPException(status_code=400, detail=f"Template '{request.template}' no encontrado")

try:
    html_content = render_template(request.template, request.data)
except TemplateNotFoundError as e:
    raise HTTPException(status_code=404, detail=str(e))
```

### Project Structure

```
app/
├── main.py              # FastAPI app initialization
├── config.py            # Settings/configuration (use @lru_cache for singleton)
├── models/
│   ├── __init__.py
│   └── schemas.py       # Pydantic models
├── routes/
│   ├── __init__.py
│   ├── email.py         # Email endpoints
│   └── webhook.py       # Webhook endpoint
├── services/
│   ├── __init__.py
│   ├── resend_client.py # Resend API client
│   └── templates.py     # Jinja2 template handling
templates/                # HTML templates
```

### REST API Conventions
- Use `/api` prefix for all API routes
- Use plural nouns for resources: `/templates`, not `/template`
- Use proper HTTP methods: GET (retrieve), POST (create), PUT (update), DELETE (remove)
- Return consistent response structures using Pydantic models
- Include health check endpoint at `/health`

### Configuration
- Use environment variables via `os.getenv()` or `python-dotenv`
- Provide sensible defaults in config classes
- Use a settings singleton pattern with `@lru_cache`

```python
@lru_cache
def get_settings():
    return Settings()
```

### Async Patterns
- Use `async def` for route handlers that perform I/O operations
- Keep route handlers thin; delegate to service functions
- Use `httpx` for async HTTP clients

### Testing Guidelines (when added)
- Place tests in `tests/` directory mirroring app structure
- Use `pytest` with fixtures for common setup
- Use `pytest.mark.parametrize` for testing multiple inputs
- Mock external services (Resend API) in unit tests
- Test error cases, not just happy paths

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| RESEND_API_KEY | Resend API key | Yes |
| DOMINIO | Email domain (default: aros.services) | No |
| FORWARD_TO_EMAIL | Forward webhook emails here | No |

## API Examples

### Health Check

```bash
curl -X GET http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy"
}
```

### List Templates

```bash
curl -X GET http://localhost:8000/api/templates
```

**Response:**
```json
{
  "templates": [
    {
      "name": "welcome",
      "description": "Welcome email"
    },
    {
      "name": "notification",
      "description": "General notification"
    }
  ]
}
```

### Send Email

```bash
curl -X POST http://localhost:8000/api/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "recipient@example.com",
    "template": "welcome",
    "subject": "Welcome to our service",
    "data": {
      "name": "John",
      "message": "Thanks for signing up"
    }
  }'
```

**Request Body:**
| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `to` | string (EmailStr) | Email recipient | Yes |
| `template` | string | Template name (e.g., "welcome", "notification") | Yes |
| `subject` | string | Email subject | Yes |
| `data` | object | Data to render the template | No |

**Response (success):**
```json
{
  "success": true,
  "message": "Email sent successfully",
  "email_id": "abc123..."
}
```

**Response (error - template not found):**
```json
{
  "detail": "Template 'invalid_template' not found"
}
```

**Response (error - invalid email):**
```json
{
  "detail": [
    {
      "type": "email_parsing",
      "loc": ["body", "to"],
      "msg": "value is not a valid email address",
      "input": "not-an-email"
    }
  ]
}
```

### Webhook (Resend)

```bash
curl -X POST http://localhost:8000/api/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "type": "email.received",
    "data": {
      "from": "support@aros.services",
      "subject": "Help with my account",
      "html": "<html><body><p>Hello, I need help...</p></body></html>"
    }
  }'
```

**Request Body (WebhookPayload):**
| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `type` | string | Event type (e.g., "email.received") | Yes |
| `data` | object | Received email data | Yes |
| `data.from` | string | Sender email | Yes |
| `data.subject` | string | Email subject | Yes |
| `data.html` | string | Email HTML content | Yes |

**Response (forwarded):**
```json
{
  "status": "forwarded"
}
```

**Response (ignored - email not allowed):**
```json
{
  "status": "ignored",
  "reason": "email not in allowed list"
}
```

**Response (ignored - event type not supported):**
```json
{
  "status": "ignored",
  "reason": "event type not supported"
}
```

## Common Tasks

### Adding a New Endpoint
1. Create route in appropriate file under `app/routes/`
2. Add Pydantic schemas in `app/models/schemas.py` if needed
3. Import and include router in `app/main.py`

### Adding a New Template
1. Create HTML file in `templates/` directory
2. Add entry to `AVAILABLE_TEMPLATES` dict in `app/services/templates.py`

### Adding a New Service
1. Create file in `app/services/`
2. Use dependency injection pattern if needed
3. Export singleton instance at module level
