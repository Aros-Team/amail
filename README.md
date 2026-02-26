# Email Service

Internal email service for AROS team. Built with FastAPI and Resend API.

## Requirements

- Python 3.12+
- Docker (for container)

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your RESEND_API_KEY
```

## Local Development

```bash
# Run development server
uvicorn app.main:app --reload --port 8000
```

## Docker Usage

```bash
# Build image
docker build -t email-service .

# Run container
docker run -p 8000:8000 --env-file .env email-service
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| RESEND_API_KEY | Resend API key | Yes |
| DOMINIO | Email domain (e.g., aros.services) | No (default: aros.services) |
| FORWARD_TO_EMAIL | Destination email for webhook forwarding | No |

### Email Domain

The base domain is configured with `DOMINIO` (default: `aros.services`). Webhook emails can be received from:
- support@{DOMINIO}
- noreply@{DOMINIO}
- team@{DOMINIO}

## API Endpoints

### Health Check
```
GET /health
```

### List Templates
```
GET /api/templates
```

### Send Email
```
POST /api/send
```

**Body:**
```json
{
  "to": "recipient@example.com",
  "template": "welcome",
  "subject": "Welcome",
  "data": {
    "name": "John",
    "message": "Thanks for signing up"
  }
}
```

### Resend Webhook
```
POST /api/webhook
```

## Project Structure

```
email-service/
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configuration
│   ├── routes/
│   │   ├── email.py         # Email endpoints
│   │   └── webhook.py       # Webhook endpoint
│   ├── services/
│   │   ├── resend_client.py # Resend client
│   │   └── templates.py     # Template management
│   └── models/
│       └── schemas.py       # Pydantic models
├── templates/                # HTML templates
├── requirements.txt
├── Dockerfile
├── .env.example
└── AGENTS.md                # Developer guidelines
```

## License

MIT
