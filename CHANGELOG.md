# Changelog

All notable changes to this project are documented in this file.
Releases follow the service version reported by the API (`app.version`).

## [Unreleased]

### Added
- `POST /api/v1/templates/render` — render a template to HTML with given data (used by the template preview tool).
- Harness workflow (`scripts/harness.py`, `scripts/build_harness.py`) for verifying environment, tracking, lint, compile, and tests.

## [1.0.0] — 2026-07-16

### Added
- Provider registry pattern with Resend and Mock providers.
- Generic Jinja2 templates (`action`, `notification`, `verification`, `custom`) with `base.html` shell and reusable components.
- Batch sending with best-effort semantics and admin failure reports (`/api/v1/send/batch`).
- `SET_FORWARD:` email command for runtime forward-target updates.
- `/api/v1/templates` endpoint with per-template variable metadata.

### Changed
- Restructured into `app/` with clear layers: routes, services, providers, contracts.
- Pydantic `BaseSettings` for configuration.
- Protocol-based provider contracts.
- Structured logging (structlog) and health checks (`/health`, `/health/email`, `/health/webhook`).
- Resend error classification and retryable handling with tenacity.
- Renamed route prefix to `/api/v1/*`.

### Fixed
- Resend error logging and connection error handling.

## [0.x] — 2026-04

### Added
- Initial email sending via Resend.
- JWT authentication.
- Email receiving/forwarding and enhanced templates.
- CI/CD pipeline and Taskfile.
