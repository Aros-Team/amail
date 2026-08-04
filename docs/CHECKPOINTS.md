# CHECKPOINTS — Final State Evaluation

> In multi-agent systems, the path is not evaluated, the destination is.
> These are objective checkpoints a judge (human or AI) can use
> to decide if the project is healthy.

## C1 — Harness is Complete

- [ ] Base files exist: `AGENTS.md`, `scripts/harness.py`, `scripts/build_harness.py`, `activities.json`, `progress/current.md`.
- [ ] Docs exist: `docs/architecture.md`, `docs/conventions.md`, `docs/verification.md`.
- [ ] `uv run python scripts/harness.py` exits with code 0.

## C2 — State is Coherent

- [ ] At most one activity in `in_progress` in `activities.json`.
- [ ] Every `done` activity has associated passing tests.
- [ ] `progress/current.md` is empty or describes the active session (no leftover junk from previous sessions).

## C3 — Code Respects Architecture

- [ ] `app/` only contains modules described in `docs/architecture.md`.
- [ ] No external dependencies outside `pyproject.toml` scope.
- [ ] No stray `print()` for debug, no TODOs without context.

## C4 — Verification is Real

- [ ] `tests/` has tests covering the modules in `app/`.
- [ ] Tests mock provider boundaries — no real network calls.
- [ ] `uv run pytest` shows > 0 tests and all green.

## C5 — Session Closed Properly

- [ ] No suspicious untracked files (`*.tmp`, `__pycache__`, build artifacts outside `.gitignore`).
- [ ] `progress/history.md` has an entry for the last session.
- [ ] The last worked activity reflects its correct state.

---

**How to use this file:** a reviewer agent (`.opencode/agent/implementation-reviewer.md`) goes through each checkbox, marks `[x]` or `[ ]`, and rejects session close if any boxes in C1-C5 remain empty.
