#!/usr/bin/env python3
"""Bootstrap the harness tracking structure for the amail project.

Run with: uv run python scripts/build_harness.py [project_name] [description]

Creates (only if missing):
  - activities.json
  - progress/current.md
  - progress/history.md
  - progress/explore/
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CURRENT_MD_TEMPLATE = """# Current Session

## Activity
- ID:
- Name:
- Type:
- Status:

## Tasks
- Current:
- Pending:

## Plan

## Notes

## Blockers

---
"""

HISTORY_MD_TEMPLATE = """# Session History

> Append-only log of completed sessions/activities.

---
"""


def init_project(project_name: str, description: str) -> None:
    print(f"Initializing project structure: {project_name}")

    progress_dir = PROJECT_ROOT / "progress"
    progress_dir.mkdir(parents=True, exist_ok=True)
    (progress_dir / "explore").mkdir(parents=True, exist_ok=True)

    activities_path = PROJECT_ROOT / "activities.json"
    if not activities_path.exists():
        activities_path.write_text(
            json.dumps(
                {"project": project_name, "description": description, "activities": []},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print("Created activities.json")
    else:
        print("activities.json already exists")

    current_md = progress_dir / "current.md"
    if not current_md.exists():
        current_md.write_text(CURRENT_MD_TEMPLATE, encoding="utf-8")
        print("Created progress/current.md")
    else:
        print("progress/current.md already exists")

    history_md = progress_dir / "history.md"
    if not history_md.exists():
        history_md.write_text(HISTORY_MD_TEMPLATE, encoding="utf-8")
        print("Created progress/history.md")
    else:
        print("progress/history.md already exists")

    print("Project initialization complete.")


if __name__ == "__main__":
    args = sys.argv[1:]
    project_name = args[0] if args else "amail"
    description = args[1] if len(args) > 1 else "Aros mail system"
    init_project(project_name, description)
