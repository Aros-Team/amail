# Resend Provider Setup

Resend is the primary email provider for Amail. This guide covers account
setup, API keys, domain verification, and webhook configuration.

## 1. Create a Resend Account

Sign up at [resend.com](https://resend.com). The free tier includes:

- 100 emails/day
- 1 domain
- API access

## 2. Get Your API Key

1. Go to [API Keys](https://dashboard.resend.com/api-keys)
2. Click **Create API Key**
3. Name it (e.g., `amail-production`)
4. Copy the key — it starts with `re_` and is shown only once

Set it in your environment:

```
RESEND_API_KEY=re_xxxxxxxxxxxxxxxx
```

## 3. Verify Your Domain

1. Go to [Domains](https://dashboard.resend.com/domains)
2. Click **Add Domain**
3. Enter your domain (e.g., `example.com`)
4. Add the DNS records Resend provides (MX, TXT, CNAME)
5. Wait for verification (usually 5-15 minutes)

Once verified, Amail can send from any address at your domain. The default
sender is `noreply@{domain}`.

## 4. Webhook Setup (Inbound Email)

To receive and forward incoming emails, configure a Resend webhook:

1. Go to [Webhooks](https://dashboard.resend.com/webhooks)
2. Click **Add Endpoint**
3. Enter your Amail receive URL:
   ```
   https://your-domain.com/api/v1/receive
   ```
4. Select the **email.received** event
5. Copy the signing secret (starts with `whsec_`)

Set it in your environment:

```
RESEND_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxx
```

### Webhook Verification

Amail verifies every inbound webhook using Svix signature validation. This
prevents spoofed or tampered requests from being processed.

### Routing Contract

When an email arrives, Amail matches the recipient against your routing
contract (`config/amail.yml` or `AMAIL_ROUTES`) and forwards to the configured
targets.

Example contract:

```yaml
domain: example.com

inbound:
  - to: support
    forwards:
      - ops@team.example.com

  - to: team
    forwards:
      - ops@team.example.com
      - backup.team@example.com

fallback:
  forwards: []
```

See [`config/amail.example.yml`](../../config/amail.example.yml) for the full
template.

## 5. Verify It Works

Check provider connectivity:

```bash
curl http://localhost:8000/health/provider
```

Expected response:

```json
{
  "status": "healthy",
  "latency_ms": 45.2,
  "status_code": 200,
  "timestamp": "2024-01-01T00:00:00+00:00"
}
```

Check webhook configuration:

```bash
curl http://localhost:8000/health/webhook
```

Expected response:

```json
{
  "status": "configured",
  "webhook_secret_configured": true,
  "routes_loaded": true,
  "timestamp": "2024-01-01T00:00:00+00:00"
}
```

## Environment Variables Summary

```
RESEND_API_KEY=re_xxxxx            # Required for sending
RESEND_WEBHOOK_SECRET=whsec_xxxxx  # Required for inbound
EMAIL_PROVIDER=resend              # Default, can be omitted
ADMIN_EMAIL=admin@example.com      # Optional, for batch failure reports
```
