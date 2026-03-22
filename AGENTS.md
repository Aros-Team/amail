# AGENTS.md - Amail

This document provides guidelines for agentic coding agents working on this codebase.

## Project Overview

- **Type**: Python/FastAPI REST API
- **Purpose**: Email service with templates using Resend API (provider-agnostic)
- **Python Version**: 3.11
- **Framework**: FastAPI

## Build & Development Commands

### Install Dependencies
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Run Development Server
```bash
task run
```
For API documentation, see [http://localhost:8000/docs](http://localhost:8000/docs)

### Build Docker Image
```bash
task build
```

### Lint Code
```bash
task lint
```

### Run Tests
```bash
pytest                    # Run all tests
pytest -v                # Verbose output
pytest --cov=app         # With coverage
```

## Project Structure

```
app/
├── main.py              # FastAPI app
├── config.py            # Configuration
├── logging_config.py    # Structured logging setup (structlog)
├── metrics.py           # Prometheus metrics definitions
├── contracts/           # Provider interfaces
│   ├── sender.py       # EmailSender protocol
│   └── receiver.py     # EmailReceiver protocol
├── providers/          # Provider implementations
│   ├── __init__.py    # Factory functions
│   └── resend/        # Resend implementation
│       ├── sender.py   # With logging & retry logic
│       └── receiver.py
├── routes/
│   ├── messages.py     # API endpoints (/api/send, /api/receive)
│   └── health.py      # Health check endpoints
├── services/
│   └── templates.py   # Template management
└── models/
    └── schemas.py     # Pydantic models
templates/              # HTML templates
prometheus/             # Prometheus configuration
grafana/                # Grafana dashboards
alerts/                 # Alert definitions
docs/                   # Documentation
tests/                  # Test suite
requirements.txt
Taskfile.yml
Dockerfile
.env.example
AGENTS.md               # Developer guidelines
```

## Provider Abstraction

The API is designed to be provider-agnostic using dependency injection.

### Adding a New Provider

1. Create implementation in `app/providers/<provider_name>/`:
   - `sender.py` - implements sending emails
   - `receiver.py` - implements receiving emails (webhooks)

2. Register in `app/providers/__init__.py`:
   - Update `get_sender()` and `get_receiver()` factory functions

### Example: Provider Interface

```python
# contracts/sender.py
class EmailSender(Protocol):
    def send(self, to: str, subject: str, html: str) -> str: ...

# contracts/receiver.py
class EmailReceiver(Protocol):
    def receive(self, payload: dict) -> dict: ...
```

## Code Style Guidelines

### Imports
- Standard library imports first, then third-party, then local
- Use absolute imports with `app.` prefix
- Group imports by type with blank lines between groups
- Sort imports alphabetically within groups

### Formatting
- Line length: 88 characters (Black default)
- Use 4 spaces for indentation
- Use trailing commas where practical
- Use f-strings for string formatting

### Types
- Use Python 3.11+ native type hints: `list[str]` instead of `List[str]`
- Use `| None` instead of `Optional[]` for simple cases

### Error Handling
- Use FastAPI's `HTTPException` for HTTP-level errors
- Include descriptive error messages in exceptions
- Return appropriate HTTP status codes (400 for bad request, 500 for server errors)

## Testing Guidelines

- Place tests in `tests/` directory mirroring app structure
- Use `pytest` with fixtures for common setup
- Mock external services (Resend API) in unit tests
- Test error cases, not just happy paths

```python
# Example fixture in conftest.py
@pytest.fixture
def mock_resend():
    with patch("resend.emails.send") as mock:
        mock.return_value = {"id": "test-email-id"}
        yield mock
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| RESEND_API_KEY | Resend API key | Yes |
| DOMAIN | Email domain (default: aros.services) | No |
| FORWARD_TO_EMAIL | Forward webhook emails here | No |
| WEBHOOK_EMAILS | List of allowed receiving emails (default: support,noreply,team) | No |
| ENVIRONMENT | Environment (dev/staging/prod) | No |
| VERSION | Service version | No |
| LOG_LEVEL | Logging level (default: INFO) | No |

## API Endpoints

### GET /health
Health check endpoint.

### GET /metrics
Prometheus metrics endpoint. Returns metrics in Prometheus format.

### GET /health/email
Email service health check. Sends a test email to `test@resend.dev` and returns:
- `status`: healthy/unhealthy
- `latency_ms`: Response time
- `status_code`: HTTP status code from Resend
- `resend_id`: ID of sent test email

### GET /api/templates
List available email templates with their variables.

### POST /api/send
Send an email using a template.

**Example:**
```json
{
  "to": "user@example.com",
  "subject": "Welcome",
  "template": "welcome",
  "data": {"name": "John", "message": "Thanks for signing up!"}
}
```

### POST /api/receive
**This endpoint is designed to be called by Resend webhooks, not directly.**

To receive emails:

1. **Configure webhook in Resend Dashboard**:
   - Go to [Resend Webhooks](https://resend.com/webhooks)
   - Create a new webhook with URL: `https://your-domain.com/api/receive`
   - Select event type: `email.received`

2. **How it works**:
   - Resend sends a POST request when an email is received
   - The endpoint validates that the email was sent to an allowed address
   - It fetches the email content using Resend's Receiving API
   - Forwards the email to `FORWARD_TO_EMAIL`

3. **Allowed addresses** (configurable via `WEBHOOK_EMAILS`):
   - `support@your-domain.com`
   - `noreply@your-domain.com`
   - `team@your-domain.com`

## Common Tasks

### Adding a New Template
1. Create HTML file in `templates/` directory
2. Add entry to `AVAILABLE_TEMPLATES` dict in `app/services/templates.py`
