# Verification

> How to verify that work is correct.

---

## 1. Before declaring a task `done`

1. Run `uv run python scripts/harness.py` — all blocks must pass (exit code 0).
2. Verify lint: `uv run ruff check .` — no errors.
3. Verify format: `uv run ruff format --check .` — formatted.
4. Verify tests: `uv run pytest` — all green.
5. Review `docs/CHECKPOINTS.md` — all applicable checkboxes marked.

---

## 2. Manual Verification Steps

### Code Quality
- No `print()` or debug statements left behind
- No TODOs without context
- Type hints on all signatures
- No unused imports or dead code

### Architecture Compliance
- Routes → services → providers (one-way dependency)
- Providers implement the `contracts/` Protocols and self-register
- Services return `EmailResponse` instead of raising for send failures
- Pydantic models in `models/schemas.py`, `response_model` on every route

### Provider Compliance
- New providers live in `app/providers/<name>/` and are registered in their `__init__.py`
- Error mapping: SDK/HTTP failures wrapped in typed errors (retryable vs non-retryable)
- Mock provider needs no credentials and makes no network calls

### Template Compliance
- New templates registered in `TEMPLATE_METADATA`
- No hardcoded branding — all via variables with defaults
- Bilingual via `lang` (`es`/`en`)

### Logging
- Events logged via `get_logger(__name__)` (structlog)
- `request_id` present for send paths
- No sensitive data (API keys, full bodies) in logs

### Tests
- New functionality has tests in `tests/`
- Tests mock provider boundaries — no real network calls
- Tests pass independently

---

## 3. Reviewer Checklist

The reviewer agent must verify:

- [ ] Harness passes (`uv run python scripts/harness.py` exits 0)
- [ ] Ruff check passes (`uv run ruff check .`)
- [ ] Ruff format clean (`uv run ruff format --check .`)
- [ ] All tests pass (`uv run pytest`)
- [ ] One-way layering respected (routes → services → providers)
- [ ] Protocols in `contracts/` match implementations
- [ ] Providers self-registered in their `__init__.py`
- [ ] Errors mapped to typed exceptions; nothing swallowed silently
- [ ] No `print()`, TODOs without context, unused imports
- [ ] Pydantic models used for request/response; `response_model` set
- [ ] Template metadata updated for new templates
- [ ] No hardcoded branding in templates
- [ ] Logs structured, with `request_id` on sends, no secrets
- [ ] Tests added and mocked (no real API calls)
- [ ] No real credentials or `.env` content committed

---

## 4. Git Hygiene

Before closing a session:

- [ ] No temp files (`.pyc`, `__pycache__`, `*.tmp`)
- [ ] `progress/current.md` emptied to template
- [ ] Summary moved to `progress/history.md`
- [ ] `activities.json` status updated
- [ ] `docs/CHECKPOINTS.md` reflects the final state
