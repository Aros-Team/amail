# Deploy with Docker

Run Amail as a container on any machine with Docker installed.

## Quick Run

```bash
docker run -d \
  --name amail \
  -p 8000:8000 \
  --env-file .env \
  ghcr.io/aros-team/amail:latest
```

Verify it's running:

```bash
curl http://localhost:8000/health
```

## Docker Compose

Create a `compose.yml`:

```yaml
services:
  amail:
    image: ghcr.io/aros-team/amail:latest
    ports:
      - "8000:8000"
    env_file: .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4); sys.exit(0)"]
      interval: 30s
      timeout: 5s
      start_period: 10s
      retries: 3
```

Start in detached mode:

```bash
docker compose up -d
```

## Environment File

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Minimum required for sending:

```
AMAIL_API_KEY=<your-generated-key>
EMAIL_PROVIDER=resend
RESEND_API_KEY=re_xxxxx
```

See [Configuration](../README.md#configuration) for the full variable
reference.

## Routing Contract

For inbound email forwarding, provide the routing contract as a secret or
mounted file.

### Option A: Environment Variable

Paste the YAML content into `AMAIL_ROUTES` in your `.env` or secret manager.

### Option B: Mounted File

Mount the config file into the container:

```bash
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  -v ./config/amail.yml:/app/config/amail.yml:ro \
  ghcr.io/aros-team/amail:latest
```

Or in Compose:

```yaml
services:
  amail:
    image: ghcr.io/aros-team/amail:latest
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - ./config/amail.yml:/app/config/amail.yml:ro
```

See [`config/amail.example.yml`](../../config/amail.example.yml) for the
contract template.

## VPS Deployment

For a VPS (e.g., DigitalOcean, Hetzner, Linode):

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Clone and configure
git clone https://github.com/aros-team/amail.git && cd amail
cp .env.example .env
nano .env  # fill in values

# Start
docker compose up -d
```

## Building from Source

```bash
git clone https://github.com/aros-team/amail.git && cd amail
docker build -t amail .
docker run -d -p 8000:8000 --env-file .env amail
```
