# Changelog

All notable changes to this project are documented in this file.
Releases follow the service version reported by the API (`app.version`).

## [1.3.1](https://github.com/Aros-Team/amail/compare/v1.3.0...v1.3.1) (2026-09-02)


### Bug Fixes

* **ci:** read version from pyproject.toml for Docker tags ([3c3f7fe](https://github.com/Aros-Team/amail/commit/3c3f7fecbfbdf75824719ba2d6b8d4f1a3f0c02f))

## [1.3.0](https://github.com/Aros-Team/amail/compare/v1.2.1...v1.3.0) (2026-09-02)


### Features

* **security:** add in-memory rate limiting for API endpoints ([0c5695b](https://github.com/Aros-Team/amail/commit/0c5695b09c77181450bc0e78ba88308996e9fa48))
* **security:** add path traversal guard for routing config file ([dbc8ee5](https://github.com/Aros-Team/amail/commit/dbc8ee59311c4988c0f586b50dbc7a7fbe8da219))
* **security:** batch limit, read-only API key, provider health check ([63981fa](https://github.com/Aros-Team/amail/commit/63981fa39e1c33ff293d15b2de08424203adaf03))
* **security:** map health provider errors to generic categories ([1523466](https://github.com/Aros-Team/amail/commit/1523466f9a1f980478cee2bb20c980dab0b3155b))


### Bug Fixes

* **security:** harden BodyLimitMiddleware against bypass attacks ([d809672](https://github.com/Aros-Team/amail/commit/d8096727eb87a71406b98caf706616c10f1b92be))
* **security:** sanitize HTML in batch reports and webhook forwards ([63744e3](https://github.com/Aros-Team/amail/commit/63744e308278e0d158f1571f27ab8e9719507d51))
* update test_security.py for get_settings change + uv.lock sync ([d7a839a](https://github.com/Aros-Team/amail/commit/d7a839a904f10c6141102f169ce547f04881f41a))


### Documentation

* **adr:** add ADR-003 provider-agnostic architecture + singleton pattern ([f6375fc](https://github.com/Aros-Team/amail/commit/f6375fc76fcca6874a5c54090a77c64243a32898))
* **adr:** update ADR-001 with dual-layer rate limiting strategy ([87ae2e9](https://github.com/Aros-Team/amail/commit/87ae2e93d234e6ba78a584e46b376c8856216a36))
* **security:** update architecture.md — auth dev mode, singleton, workers ([538c6c3](https://github.com/Aros-Team/amail/commit/538c6c3921f0d5f1a2dc777e1156a88915dac048))

## [1.2.1](https://github.com/Aros-Team/amail/compare/v1.2.0...v1.2.1) (2026-08-31)


### Bug Fixes

* sync version to 1.2.0 + fix release-please paths for src layout ([106993b](https://github.com/Aros-Team/amail/commit/106993b333c51884adf755ec5f8e9dbcc06ecf6e))

## [1.2.0](https://github.com/Aros-Team/amail/compare/v1.1.0...v1.2.0) (2026-08-31)


### Features

* add API key authentication for send endpoints ([47795ba](https://github.com/Aros-Team/amail/commit/47795ba000121d202a833b5fce7ef2ba397e5a4f))


### Bug Fixes

* **ci:** add build-system, fix compileall paths for src layout ([86cd8d2](https://github.com/Aros-Team/amail/commit/86cd8d27204035e6774186d28eda3e2a17b336a0))
* require API key in production + limit request body to 1MB ([91ce5db](https://github.com/Aros-Team/amail/commit/91ce5db170fed8cde8cadc17d438a14ded4c7009))
* return 500 on receive errors + fix DEV_ROUTES_PATH ([c748114](https://github.com/Aros-Team/amail/commit/c74811485d75b2e38d36204d16b8a4ac5b9716fb))
* **taskfile:** show server logs in run:cloud instead of hiding them ([b8357a8](https://github.com/Aros-Team/amail/commit/b8357a834931ddab22c2f641f9fd2846a7c7913b))
* update stale app/config/routes paths to src/amail/config/routes ([ff3322c](https://github.com/Aros-Team/amail/commit/ff3322c3ecbf6f6591a3df8b5e73726305bfeb02))


### Documentation

* add ADRs for rate limiting and routing convention ([e0e0809](https://github.com/Aros-Team/amail/commit/e0e0809afd00f9f87490dfc6dca8a25cd834f73d))

## [1.1.0](https://github.com/Aros-Team/amail/compare/v1.0.0...v1.1.0) (2026-08-08)


### Features

* add monitoring, structured logging and health checks ([0e23b5c](https://github.com/Aros-Team/amail/commit/0e23b5c5389b306cc9c70f835fd8b55f48bd2259))
* add release-please workflow with validation gate ([c451321](https://github.com/Aros-Team/amail/commit/c4513212761cd0714853920429ac2d594655ed24))
* add template render endpoint with route tests ([7cf4c46](https://github.com/Aros-Team/amail/commit/7cf4c463678815f6b5592436418f2ece70360f3f))
* add two_factor template and enhanced /api/templates endpoint ([d942a62](https://github.com/Aros-Team/amail/commit/d942a626c5fea83d8dec52aa2e6b92982946ee54))
* **config:** declarative YAML inbound routing contract ([7edf254](https://github.com/Aros-Team/amail/commit/7edf254d51c261c1052e0d2d38d93ae6f42b176f))
* improve Resend error logging and add connection error handling ([fd1c479](https://github.com/Aros-Team/amail/commit/fd1c4791df8d15531f36253740d332b18db9a2cd))
* update templates; chore: add uv project manager. ([987a928](https://github.com/Aros-Team/amail/commit/987a928df96eb7abe7b10b964db9b35e75715fa0))


### Bug Fixes

* improve email receiving and sending ([dd001c5](https://github.com/Aros-Team/amail/commit/dd001c50defc53c12b19c3d098d44296cae3c586))
* **webhook:** verify inbound signature with resend.Webhooks.verify ([b89ac7a](https://github.com/Aros-Team/amail/commit/b89ac7aba56814178c079d96d3bfa3fb94931b9f))


### Documentation

* fix section numbering in testing policy ([499ab5c](https://github.com/Aros-Team/amail/commit/499ab5c452bbe8f12d67123c984a6fdfc607c399))
* update API docs and environment variables ([f686f58](https://github.com/Aros-Team/amail/commit/f686f5874703300620560fce61587c1742f6e5b2))

## [Unreleased]

### Added
- Harness workflow (`scripts/harness.py`, `scripts/build_harness.py`) for verifying environment, tracking, lint, compile, and tests.

### Changed
- Removed the template subsystem: Jinja2 templates, the `render/` seam, `services/templates.py`, and the `/templates` and `/templates/render` endpoints.
- `EmailRequest` now uses `body` (plain text) instead of `template`/`data`/`lang`.
- The sender contract and Resend/Mock senders now support both `html` and `text` (optional); `EmailService.send` sends the plain-text `body` as `text`.

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
