#!/usr/bin/env python3
"""
Verification harness for the amail project.

Run with: uv run python scripts/harness.py

Checks, in order:
  1. Environment (uv / python present)
  2. Base harness files exist (AGENTS.md, activities.json, progress/, docs/)
  3. activities.json is valid (statuses, types, one in_progress at most)
  4. Code quality (ruff check + ruff format --check)
  5. Compilation (python -m compileall)
  6. Tests (pytest)

Exit code 0 only when every block passes.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RED = "\x1b[0;31m"
GREEN = "\x1b[0;32m"
YELLOW = "\x1b[0;33m"
NC = "\x1b[0m"

exit_code = 0


def ok(msg: str) -> None:
    """Print a success message in green."""
    print(f"{GREEN}[OK]{NC}    {msg}")


def warn(msg: str) -> None:
    """Print a warning message in yellow."""
    print(f"{YELLOW}[WARN]{NC}  {msg}")


def fail(msg: str) -> None:
    """Print an error message in red and mark the run as failed."""
    global exit_code
    print(f"{RED}[FAIL]{NC}  {msg}")
    exit_code = 1


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run a command in the project root and return the completed process."""
    return subprocess.run(cmd, cwd=cwd or PROJECT_ROOT)


def command_exists(cmd: str) -> bool:
    """Return True when the command is available on the PATH."""
    return shutil.which(cmd) is not None


print("── 1. Environment Check ─────────────────────────────")

if not command_exists("uv"):
    fail("uv is not installed")
    sys.exit(1)
uv_result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
ok(f"uv -> {uv_result.stdout.strip()}")

if not command_exists("python3"):
    fail("python3 is not installed")
    sys.exit(1)
python_result = subprocess.run(["python3", "--version"], capture_output=True, text=True)
ok(f"python3 -> {python_result.stdout.strip()}")

print("\n── 2. Base Harness Files ─────────────────────────────")

base_files = [
    "AGENTS.md",
    "activities.json",
    "progress/current.md",
    "progress/history.md",
    "docs/architecture.md",
    "docs/conventions.md",
    "docs/verification.md",
    "docs/CHECKPOINTS.md",
    "docs/testing.md",
]

for f in base_files:
    if (PROJECT_ROOT / f).exists():
        ok(f"Exists {f}")
    else:
        fail(f"Missing base file: {f}")

print("\n── 3. Validating activities.json ─────────────────────")

try:
    data = json.loads((PROJECT_ROOT / "activities.json").read_text(encoding="utf-8"))
    activities = data if isinstance(data, list) else data.get("activities", [])
    valid_statuses = {"pending", "in_progress", "done", "blocked"}
    valid_types = {"fix", "feat", "chore"}
    valid_task_statuses = {"pending", "in_progress", "done", "blocked"}
    valid_agents = {"implementer", "reviewer"}

    in_progress = [a for a in activities if a.get("status") == "in_progress"]

    if len(in_progress) > 1:
        fail(f"Found {len(in_progress)} activities in in_progress (max 1)")

    for a in activities:
        if (
            a.get("status") == "done"
            and a.get("tasks")
            and any(t.get("status") != "done" for t in a["tasks"])
        ):
            warn(f"Activity {a.get('id')} is done but has tasks not done")

    for a in in_progress:
        if not a.get("tasks") or not any(
            t.get("status") == "in_progress" for t in a["tasks"]
        ):
            warn(f"Activity {a.get('id')} is in_progress but no task is in_progress")

    has_invalid = False
    for a in activities:
        if a.get("status") not in valid_statuses:
            fail(f"Invalid status in activity {a.get('id')}: {a.get('status')}")
            has_invalid = True
        if a.get("type") and a["type"] not in valid_types:
            fail(
                "Invalid type in activity "
                f"{a.get('id')}: {a.get('type')} "
                "(must be fix, feat, or chore)"
            )
            has_invalid = True
        if a.get("tasks") and isinstance(a["tasks"], list):
            for t in a["tasks"]:
                if not t.get("id") or not t.get("description"):
                    fail(f"Task missing id or description in activity {a.get('id')}")
                    has_invalid = True
                if t.get("status") and t["status"] not in valid_task_statuses:
                    fail(
                        "Invalid task status in activity "
                        f"{a.get('id')}: {t.get('status')}"
                    )
                    has_invalid = True
                if t.get("agent") and t["agent"] not in valid_agents:
                    fail(
                        "Invalid task agent in activity "
                        f"{a.get('id')}: {t.get('agent')} "
                        "(must be implementer or reviewer)"
                    )
                    has_invalid = True

    if not has_invalid:
        ok(f"activities.json valid ({len(activities)} activities)")
except Exception as e:
    fail(f"activities.json invalid: {e}")

print("\n── 4. Code Quality (ruff) ────────────────────────────")

result = run(["uv", "run", "ruff", "check", "."])
if result.returncode == 0:
    ok("Ruff check passed")
else:
    fail("Ruff check errors found")

result = run(["uv", "run", "ruff", "format", "--check", "."])
if result.returncode == 0:
    ok("Ruff format clean")
else:
    fail("Ruff format drift (run 'uv run ruff format .')")

print("\n── 5. Compilation ─────────────────────────────────────")

result = run(["uv", "run", "python", "-m", "compileall", "-q", "src/amail"])
if result.returncode == 0:
    ok("Compilation succeeded")
else:
    fail("Compilation failed")

print("\n── 6. Running Tests ───────────────────────────────────")

result = run(["uv", "run", "pytest"])
if result.returncode == 0:
    ok("All tests pass")
else:
    fail("Some tests are broken")

print("\n── 7. Summary ─────────────────────────────────────────")

if exit_code == 0:
    ok("Environment ready. You can start working.")
else:
    fail("Environment NOT ready. Resolve errors before advancing.")

sys.exit(exit_code)
