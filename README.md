# Amail

Internal email service for the AROS team. Built with FastAPI and Resend API.

## Requirements

- Python 3.11
- Docker (to build the image)
- Virtualenv
- Taskfile

## First Steps

Before running commands, initialize the virtual environment with virtualenv:

```
virtualenv -p 3.11 venv

# Load environment
source venv/bin/activate
```

Then install dependencies: `pip install -r requirements.txt`

## Commands

- To run the project, use `task run`. For API documentation, see [http://localhost:8000/docs](http://localhost:8000/docs).
- To build the project, use `task build`. This command adds a new image to local Docker images.
- To lint the code, use `task lint`.

## Authentication

All API endpoints (except `/health` and `/api/token`) require JWT authentication.

1. Get a token:
   ```bash
   curl -X GET http://localhost:8000/api/token
   ```

2. Use the token in requests:
   ```bash
   curl -X POST http://localhost:8000/api/send \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "to": "recipient@example.com",
       "template": "welcome",
       "subject": "Welcome",
       "data": {"name": "John"}
     }'
   ```

## Project Structure

```
amail/
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configuration
│   ├── security.py          # JWT authentication
│   ├── contracts/           # Provider interfaces
│   │   ├── sender.py        # EmailSender protocol
│   │   └── receiver.py      # EmailReceiver protocol
│   ├── providers/           # Provider implementations
│   │   └── resend/          # Resend implementation
│   │       ├── sender.py
│   │       └── receiver.py
│   ├── routes/
│   │   └── messages.py      # API endpoints
│   ├── services/
│   │   └── templates.py     # Template management
│   └── models/
│       └── schemas.py       # Pydantic models
├── templates/                # HTML templates
├── tests/                    # Test suite
├── requirements.txt
├── Taskfile.yml
├── Dockerfile
└── AGENTS.md                # Developer guidelines
```
