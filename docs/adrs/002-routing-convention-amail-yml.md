# ADR-002: Routing Convention with amail.yml

## Status

Accepted

## Context

The email service needs a declarative configuration that defines:
- Which domain the service handles
- Which inbound addresses are accepted
- Where each address forwards to
- A fallback for unmatched addresses

This configuration must be available in both local development and serverless production.

## Decision

Routing configuration lives in a single YAML file named `amail.yml` (not `routes.yaml`, not `routing.yaml`).

### File location

| Environment | Source |
|-------------|--------|
| Development | `config/amail.yml` (gitignored, local file) |
| Production | `AMAIL_ROUTES` env var (YAML content as string) or `AMAIL_ROUTES_FILE` (path to file) |

Source precedence: `AMAIL_ROUTES` (text) > `AMAIL_ROUTES_FILE` (path) > `config/amail.yml` (dev file).

### File structure

```yaml
domain: spalax.dev

inbound:
  - to: support       # local part only, domain is inherited
    forwards:
      - ops@team.example.com

fallback:
  forwards:
    - jorgity345@gmail.com
```

### Naming rationale

- `amail.yml` — named after the project, like `docker-compose.yml` or `nginx.conf`. Generic enough to hold future top-level config if needed.
- NOT `routes.yaml` — too generic, could be confused with API routes.
- NOT `routing.yaml` — confused with API routing (FastAPI routers).
- NOT `inbound.yaml` — too narrow, the file also defines the domain (used for outbound health checks).
- `.yml` extension — shorter, consistent with common DevOps conventions.

### `to:` field convention

The `to:` field accepts only the **local part** of the email address (e.g., `support`, not `support@spalax.dev`). The domain is inherited from the top-level `domain` field. This avoids redundancy.

The `forwards:` field requires **full email addresses** because forwarding targets are external and not bound to the service domain.

### Loader

`src/amail/config/routing.py` — `load_routing_config()` returns a cached `RoutingConfig` model. The dev file path is resolved relative to the project root (`config/amail.yml`).

## Consequences

- `config/amail.yml` is gitignored — never committed, each developer has their own
- `config/amail.example.yml` is tracked — serves as a template for new setups
- In production, the YAML is injected via Cloud Secret Manager as an env var
- No code changes needed to switch between environments
