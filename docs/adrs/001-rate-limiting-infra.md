# ADR-001: Rate Limiting at Infrastructure Level

## Status

Accepted

## Context

Amail is a serverless email microservice deployed on Cloud Run. Each request may be handled by a different instance, making in-memory rate limiting unreliable (state is not shared across instances).

Rate limiting is needed to protect the service from abuse, bot traffic, and accidental overload.

## Decision

Rate limiting will NOT be implemented in the application code. It will be handled at the infrastructure layer using Google Cloud Armor or API Gateway.

### Why not in-app rate limiting?

- **Stateless architecture**: Cloud Run instances don't share memory. A per-instance counter allows `N * instances` requests, defeating the limit.
- **Redis/Memorystore**: Adds cost, latency, and operational complexity for a problem the platform already solves.
- **Slowapi/in-memory**: Only works reliably with a single instance. Breaks silently when autoscaling kicks in.

### Why infrastructure-level?

- **Applied before compute**: Requests are rejected at the load balancer, saving CPU/memory.
- **Shared state**: Cloud Armor and API Gateway maintain global counters across all instances.
- **Configurable without deploys**: Rate limits can be adjusted in the console without code changes or redeployment.
- **Visible in monitoring**: Cloud Armor metrics integrate with Cloud Monitoring out of the box.

### Recommended configuration

| Endpoint | Rate Limit | Notes |
|----------|-----------|-------|
| `POST /api/v1/send` | 60 req/min per API key | Primary protection |
| `POST /api/v1/send/batch` | 10 req/min per API key | Heavier operation |
| `POST /api/v1/receive` | Unlimited | Resend webhook, no abuse vector |
| `GET /health*` | Unlimited | Health checks |

Key-based rate limiting via `X-API-Key` header in Cloud Armor rules.

### Resend limits

Resend enforces its own rate limits (100 emails/second on free tier). These are independent and additive — even if infrastructure allows a request through, Resend may reject it.

## Consequences

- No rate limiting dependencies in `pyproject.toml`
- No rate limiting code in `src/amail/`
- Rate limiting configuration lives in Terraform / gcloud commands, not in the app
- Documented in `docs/architecture.md` as an infrastructure concern
