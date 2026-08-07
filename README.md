# Aros Mail

> A lightweight, self-hosted email microservice built with Python and Resend. Deploy anywhere with your custom domain and templates.

Send and receive emails, forward messages to multiple recipients, and manage custom HTML templates via a simple REST API. Serverless-first. No databases. No storage. No vendor lock-in. Just clone, configure, and deploy in seconds.

## Routing contract

Inbound email forwarding is driven by a **declarative YAML routing contract**, not by
individual environment variables. The contract declares the email `domain`, which
inbound addresses are accepted, and where each one is forwarded (one or many targets)
plus an optional fallback.

Sources, in precedence order (the loader caches once at startup):

1. `AMAIL_ROUTES` — the YAML content as an env var / secret.
2. `AMAIL_ROUTES_FILE` — path to a YAML file.
3. `app/config/routes.yaml` — local development file (gitignored).

See `app/config/routes.example.yaml` for a documented template.

```yaml
domain: example.com
inbound:
  - to: support@example.com
    forwards: [ops@team.example.com]
  - to: team@example.com
    forwards: [ops@team.example.com, backup.team@example.com]
fallback:
  forwards: []
```

- Email to an address **not** in `inbound` is ignored.
- Email matching one or more rules is forwarded to the **union** of their `forwards`.
- Email to an accepted address that matches no rule uses `fallback.forwards`; if empty, it is ignored.
- If no contract is present, the app logs an error at startup and `GET /health/webhook`
  returns `routes_loaded: false` / `missing_routes`.

## Deployment on Cloud Run (serverless)

The contract and the secrets are delivered by the platform; nothing sensitive is baked
into the image.

```bash
# 1. Store the routing contract as a secret
gcloud secrets create amail-routes --data-file=app/config/routes.yaml

# 2. Deploy, wiring the secret into the AMAIL_ROUTES env var
gcloud run deploy amail \
    --image gcr.io/PROJECT/amail:latest \
    --region us-central1 \
    --set-secrets=AMAIL_ROUTES=amail-routes:latest

# 3. Grant the service account read access to the secret
gcloud secrets add-iam-policy-binding amail-routes \
    --member="serviceAccount:$(gcloud run services describe amail --format='value(spec.template.spec.serviceAccountName)')" \
    --role="roles/secretmanager.secretAccessor"
```

- **No cold-start penalty**: Cloud Run resolves the secret and injects `AMAIL_ROUTES`
  before your process starts; the app reads it once and caches it.
- **Hot changes**: edit the secret and redeploy a revision — no image rebuild, no code change.
- **Image privacy**: push the image to a private registry and sign it (e.g. cosign) as
  defense-in-depth. The routing contract and secrets are never baked into the image.
