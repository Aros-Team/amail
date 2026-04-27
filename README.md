# Amail

Internal email service for the AROS team. Built with FastAPI and Resend API.

## Requirements

- Python 3.11
- Docker (to build the image)
- Virtualenv
- Taskfile

## First Steps

Before running commands, initialize the virtual environment with virtualenv:

```code
virtualenv -p 3.11 venv

# Load environment
source venv/bin/activate
```

Then install dependencies: `pip install -r requirements.txt`

## Commands

- To run the project, use `task run`. For API documentation, see [http://localhost:8000/docs](http://localhost:8000/docs).
- To build the project, use `task build`. This command adds a new image to local Docker images.
- To lint the code, use `task lint`.

## Usage

```code
curl -X POST http://localhost:8000/api/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "recipient@example.com",
    "template": "welcome",
    "subject": "Welcome",
    "data": {"name": "John"}
  }'
```
