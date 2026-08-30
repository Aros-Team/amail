# AGENTS.md — Amail

> Agent navigation map. Read only what you need (progressive disclosure).

## Before start

1. `uv run python scripts/harness.py` — must end green. If it fails, **STOP** and resolve env first.
2. If it reports missing files, run `uv run python scripts/build_harness.py`.
3. Read `progress/current.md` (session state) and `activities.json` (pending activities/tasks).
4. Check the OpenAPI spec at `http://localhost:8000/openapi.json` before touching or consuming routes.
5. Delegate ONE task from ONE pending activity. **Never work directly — always delegate.**

## Repo map

| Path | When read |
|---|---|
| `activities.json`, `progress/current.md` | always, at start |
| `progress/history.md` | need past context |
| `docs/architecture.md` | before implement |
| `docs/conventions.md` | before write code |
| `docs/verification.md`, `docs/CHECKPOINTS.md` | before declaring done |
| `scripts/harness.py` | verification gate |
| `src/amail/`, `tests/` | implement / verify |

- All paths relative to repo root. No absolute paths, no `../`. Workspace name is `aros`.

## Hard rules

- **One task at a time**; don't mix activities. Parallel tasks only within one activity.
- **No `done` without green tests** — `uv run python scripts/harness.py` all green.
- Document in `progress/current.md` **while** working, not after. Include plan + task breakdown.
- If unsure, check `docs/` before inventing. If a tool misbehaves, log it in `progress/current.md` and stop — no workarounds.

## Activities

- Types: `fix` (bug), `feat` (feature), `chore` (refactor/config/deps).
- Schema (see `.opencode/agent/main-orchestrator.md`): `{id, type, name, title, description, acceptance[], tasks[], status}`.

## Delegation

| Agent | Use for |
|---|---|
| `task-executor` | implementation |
| `implementation-reviewer` | validate before done |
| `explore` | fast codebase search |
| `general` | multi-step research |

Flow: open `activities.json` → pick a `pending` task → delegate → set task `in_progress` → annotate `progress/current.md` (activity, task, start time).

## Session close

1. Harness all green.
2. Mark task/activity `done` in `activities.json` (activity only when all tasks done).
3. Move summary from `progress/current.md` to end of `progress/history.md`, then reset `current.md` to the template.
4. No temp files, debug prints, or context-less TODOs.
5. If all activities are done, ask the user whether to clean the session (clear `activities.json`, reset `current.md`).

## Greeting

```
| > Hello, I am the main orchestrator for Amail.
We currently have X pending activity(ies).
What would you like to do today? (new feature / bug fix / improvement or refactor)
```

Replace X with the pending count from `activities.json`.
