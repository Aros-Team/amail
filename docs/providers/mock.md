# Mock Provider Setup

The mock provider is used for local development and testing. It makes no
network calls and simulates email sending/receiving.

## When to Use

- Local development without a Resend account
- CI/CD pipelines where you don't need real email delivery
- Unit and integration tests

## Configuration

Set the provider to `mock`:

```
EMAIL_PROVIDER=mock
```

No API keys or webhook secrets are required.

## Behavior

- **Send**: returns a simulated success response with a fake `email_id`
- **Receive**: processes the webhook payload but does not forward anywhere
- **Health check**: always returns healthy

## Testing

```bash
# Start with mock provider
EMAIL_PROVIDER=mock uvicorn amail.main:app --port 8000

# Send a test email
curl -X POST http://localhost:8000/api/v1/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "test@example.com",
    "subject": "Test",
    "body": "Hello from mock"
  }'
```

Expected response:

```json
{
  "success": true,
  "message": "Email sent successfully",
  "email_id": "mock-email-id",
  "to": "test@example.com"
}
```
