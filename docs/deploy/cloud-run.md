# Deploy on Google Cloud Run

Deploy Amail as a serverless container on Cloud Run. The routing contract and
secrets are delivered by the platform; nothing sensitive is baked into the
image.

## Prerequisites

- Google Cloud project with billing enabled
- `gcloud` CLI authenticated (`gcloud auth login`)
- Container image pushed to a registry (Artifact Registry or GHCR)

## 1. Push the Image

Option A — Artifact Registry:

```bash
gcloud builds submit --tag us-central1-docker.pkg.dev/PROJECT/amail/amail:latest
```

Option B — GHCR:

```bash
docker tag ghcr.io/aros-team/amail:latest us-central1-docker.pkg.dev/PROJECT/amail/amail:latest
docker push us-central1-docker.pkg.dev/PROJECT/amail/amail:latest
```

## 2. Store Secrets

```bash
# API key
gcloud secrets create amail-api-key --data-file=<(echo -n "your-api-key")

# Resend API key
gcloud secrets create resend-api-key --data-file=<(echo -n "re_xxxxx")

# Resend webhook secret
gcloud secrets create resend-webhook-secret --data-file=<(echo -n "whsec_xxxxx")

# Routing contract
gcloud secrets create amail-routes --data-file=config/amail.yml
```

## 3. Deploy

```bash
gcloud run deploy amail \
  --image us-central1-docker.pkg.dev/PROJECT/amail/amail:latest \
  --region us-central1 \
  --allow-unauthenticated \
  --set-secrets=\
AMAIL_API_KEY=amail-api-key:latest,\
RESEND_API_KEY=resend-api-key:latest,\
RESEND_WEBHOOK_SECRET=resend-webhook-secret:latest,\
AMAIL_ROUTES=amail-routes:latest
```

Remove `--allow-unauthenticated` if you want Cloud Run to handle auth
externally.

## 4. Grant Secret Access

If using a custom service account:

```bash
SA=$(gcloud run services describe amail \
  --region us-central1 \
  --format='value(spec.template.spec.serviceAccountName)')

for secret in amail-api-key resend-api-key resend-webhook-secret amail-routes; do
  gcloud secrets add-iam-policy-binding "$secret" \
    --member="serviceAccount:${SA}" \
    --role="roles/secretmanager.secretAccessor"
done
```

## Why Cloud Run Works Well

- **No cold-start penalty**: Cloud Run resolves secrets and injects env vars
  before your process starts; the app reads them once and caches.
- **Hot changes**: edit a secret and create a new revision — no image rebuild,
  no code change.
- **Image privacy**: push to a private registry and sign with
  [cosign](https://docs.sigstore.dev/cosign/overview/) as defense-in-depth.
  Secrets are never baked into the image.
- **Free tier**: Cloud Run offers 180,000 vCPU-seconds and 360,000
  GiB-seconds per month at no cost.

## Updating

```bash
# Update secrets
gcloud secrets versions add amail-routes --data-file=config/amail.yml

# Deploy new revision (picks up latest secrets)
gcloud run deploy amail \
  --image us-central1-docker.pkg.dev/PROJECT/amail/amail:latest \
  --region us-central1 \
  --set-secrets=AMAIL_ROUTES=amail-routes:latest
```

## Logs

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=amail" \
  --limit 50 --format "json"
```
