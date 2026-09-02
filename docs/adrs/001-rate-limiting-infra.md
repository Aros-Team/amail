# ADR-001: Rate Limiting — Dual-Layer Strategy

## Status

Accepted (updated)

## Context

Amail is a serverless email microservice deployed on Cloud Run. Each request may be handled by a different instance, making in-memory rate limiting unreliable as a sole defense (state is not shared across instances).

Rate limiting is needed to protect the service from:
- **Brute force attacks**: Compromised API key used to flood the service
- **Traffic spikes**: Sudden bursts that overwhelm a single instance
- **Accidental overload**: Misconfigured clients sending excessive requests

### Why IP-based limiting doesn't work

Cloud Run assigns each request to an arbitrary instance. The `X-Forwarded-For` header may contain the caller IP, but:
- In serverless, IPs rotate across requests (no sticky sessions)
- A single legitimate user behind NAT appears as one IP but may need high throughput
- IP-based limits break when autoscaling — the same IP hits different instances with independent counters

## Decision

A **dual-layer** strategy: infrastructure rate limiting (primary) + basic app-level rate limiting (defense-in-depth).

### Layer 1: Infrastructure (primary defense)

Cloud Armor / API Gateway handles global, shared-state rate limiting. This is the primary defense against sustained abuse.

| Endpoint | Rate Limit | Notes |
|----------|-----------|-------|
| `POST /api/v1/send` | 60 req/min per API key | Primary protection |
| `POST /api/v1/send/batch` | 10 req/min per API key | Heavier operation |
| `POST /api/v1/receive` | Unlimited | Resend webhook, signed |
| `GET /health*` | Unlimited | Health checks |

Key-based rate limiting via `X-API-Key` header in Cloud Armor rules.

### Layer 2: App-level (defense-in-depth)

Basic in-memory rate limiting per instance. Protects against brute force and traffic spikes **within a single instance**.

| Endpoint Group | Per Second | Per Minute | Env Vars |
|---------------|-----------|-----------|----------|
| Send (`/send`, `/send/batch`) | 10 | 60 | `AMAIL_RATE_LIMIT_SEND_PER_SEC`, `AMAIL_RATE_LIMIT_SEND_PER_MIN` |
| Receive (`/receive`) | 10 | 60 | `AMAIL_RATE_LIMIT_RECEIVE_PER_SEC`, `AMAIL_RATE_LIMIT_RECEIVE_PER_MIN` |
| Health (`/health*`) | — | 300 | `AMAIL_RATE_LIMIT_HEALTH_PER_MIN` |

Implementation: `SlidingWindowRateLimiter` using deques in `src/amail/middleware/rate_limit.py`. Applied as FastAPI dependencies on route groups.

### What app-level rate limiting protects against

- **Brute force with compromised API key**: An attacker flooding `/send` from a single instance hits the 10 req/s limit
- **Traffic spikes**: A sudden burst is throttled before reaching Resend
- **Health check abuse**: Monitoring tools hammering `/health` are bounded at 300 req/min

### What it does NOT protect against

- **Sustained abuse under the limit**: An attacker sending 59 req/min (just under 60/min) can send ~85K emails/day. This requires infrastructure-level protection (Cloud Armor) or Resend's own limits.
- **Distributed attacks**: In-memory counters are per-instance. N instances × limit = N × limit effective throughput. Only infrastructure rate limiting provides global counters.
- **Cross-instance coordination**: Each Cloud Run instance has independent counters. No shared state.

### Why not Redis/Memorystore?

- Adds cost, latency, and operational complexity
- Defeats the "no database, no storage" design goal
- Cloud Armor already solves the shared-state problem at the infrastructure layer

### Resend limits

Resend enforces its own rate limits (100 emails/second on free tier). These are independent and additive — even if infrastructure allows a request through, Resend may reject it.

## Consequences

- Rate limiting is configured both in infrastructure (Cloud Armor) and in the app (env vars)
- App-level limits are per-instance — they complement, not replace, infrastructure limits
- No new dependencies — rate limiter uses only stdlib (`collections.deque`, `threading.Lock`, `time.monotonic`)
- Rate limit configuration in the app is documented in `.env.example`
- This ADR documents the limitation: app-level rate limiting is not a substitute for proper infrastructure protection against sustained abuse
