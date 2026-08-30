# Aros Mail

> A lightweight, self-hosted email microservice built with Python and Resend. Deploy anywhere with your custom domain.

Send and receive emails and forward messages to multiple recipients via a simple REST API. Serverless-first. No databases. No storage. No vendor lock-in. Just clone, configure, and deploy in seconds.

## Deployment on Cloud Run (serverless)

The contract and the secrets are delivered by the platform; nothing sensitive is baked
into the image.

```bash
# 1. Store the routing contract as a secret
gcloud secrets create amail-routes --data-file=config/amail.yaml

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
