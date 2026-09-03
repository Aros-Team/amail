# Amail

> Lightweight, self-hosted email microservice. Send, receive, and forward emails
> via a REST API. Serverless-first. No databases. No storage.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Container](https://img.shields.io/badge/container-ready-0ea5e9.svg)](https://github.com/aros-team/amail/pkgs/container/amail)

## Quick Start

### Docker

```bash
# 1. Generate an API key
openssl rand -base64 32

# 2. Create .env (copy the example and fill in your values)
cp .env.example .env

# 3. Run
docker run -d -p 8000:8000 --env-file .env ghcr.io/aros-team/amail:latest
```

### From Source

```bash
git clone https://github.com/aros-team/amail.git && cd amail
cp .env.example .env   # edit with your values
uv sync
uv run uvicorn amail.main:app --port 8000
```

The API is now available at `http://localhost:8000`. OpenAPI docs at
`http://localhost:8000/docs` (disabled in production).

## Configuration

All configuration is environment-driven. Copy `.env.example` to `.env` and
adjust values. Secrets should be stored in your platform's secret manager in
production.

### Environment Variables

#### Authentication

| Variable | Required | Default | Description |
|---|---|---|---|
| `AMAIL_API_KEY` | Yes* | — | API key for `POST /api/v1/send` and `/api/v1/send/batch`. Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `ENVIRONMENT` | No | `development` | Set to `production` to enforce API key and disable `/docs` |

*Can be empty in development mode.

#### Email Provider

| Variable | Required | Default | Description |
|---|---|---|---|
| `EMAIL_PROVIDER` | No | `resend` | Active provider: `resend` or `mock` |
| `RESEND_API_KEY` | Yes | — | Resend API key (starts with `re_`). See [Resend setup](docs/providers/resend.md) |
| `RESEND_WEBHOOK_SECRET` | Yes* | — | Webhook signing secret (starts with `whsec_`) for inbound email verification |
| `ADMIN_EMAIL` | No | — | Recipient for batch failure reports |

*Required for inbound email forwarding.

#### Inbound Routing

Inbound forwarding is driven by a declarative YAML contract. Sources in order:

1. `AMAIL_ROUTES` — YAML content as an env var or secret
2. `AMAIL_ROUTES_FILE` — path to a YAML file
3. `config/amail.yml` — development file (gitignored)

See [`config/amail.example.yml`](config/amail.example.yml) for the contract
template.

#### Rate Limiting

| Variable | Default | Description |
|---|---|---|
| `AMAIL_RATE_LIMIT_SEND_PER_SEC` | `10` | Send endpoints: requests per second |
| `AMAIL_RATE_LIMIT_SEND_PER_MIN` | `60` | Send endpoints: requests per minute |
| `AMAIL_RATE_LIMIT_RECEIVE_PER_SEC` | `10` | Receive endpoint: requests per second |
| `AMAIL_RATE_LIMIT_RECEIVE_PER_MIN` | `60` | Receive endpoint: requests per minute |
| `AMAIL_RATE_LIMIT_HEALTH_PER_MIN` | `300` | Health endpoints: requests per minute |

#### Advanced

| Variable | Default | Description |
|---|---|---|
| `AMAIL_MAX_BATCH_SIZE` | `25` | Max emails per batch request |
| `AMAIL_WORKERS` | `1` | Uvicorn worker count |
| `LOG_LEVEL` | `INFO` | Structured log level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |

## Deploy

Amail runs anywhere you can run a container.

| Provider | Guide |
|---|---|
| Docker / Docker Compose | [docs/deploy/docker.md](docs/deploy/docker.md) |
| Google Cloud Run | [docs/deploy/cloud-run.md](docs/deploy/cloud-run.md) |
| AWS Lambda | Coming soon |
| Azure Container Apps | Coming soon |

## API Reference

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/send` | Yes | Send a single email |
| `POST` | `/api/v1/send/batch` | Yes | Send multiple emails (batch) |
| `POST` | `/api/v1/receive` | No | Inbound email webhook (Resend) |
| `GET` | `/health` | No | Liveness probe |
| `GET` | `/health/provider` | No | Provider connectivity check |
| `GET` | `/health/webhook` | No | Webhook configuration check |

Full request/response schemas are available at `/openapi.json` in development
mode (`ENVIRONMENT != production`).

### Send Example

```bash
curl -X POST http://localhost:8000/api/v1/send \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "to": "user@example.com",
    "subject": "Hello from Amail",
    "body": "This is a test email."
  }'
```

## Email Providers

| Provider | Status | Docs |
|---|---|---|
| Resend | Production | [Setup guide](docs/providers/resend.md) |
| Mock | Testing | [Setup guide](docs/providers/mock.md) |

## Security

- **Secrets**: never bake API keys or webhook secrets into container images.
  Use your platform's secret manager (e.g., GCP Secret Manager, AWS Secrets
  Manager, Docker secrets).
- **HTTPS**: use TLS in production. Cloud Run and most platforms provide this
  by default.
- **API key rotation**: rotate `AMAIL_API_KEY` periodically. The key is
  checked on every request to send endpoints.
- **Webhook verification**: inbound email webhooks are verified using Svix
  signature validation. Always set `RESEND_WEBHOOK_SECRET`.

## License

[Apache License 2.0](LICENSE)
