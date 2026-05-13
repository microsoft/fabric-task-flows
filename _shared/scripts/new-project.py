#!/usr/bin/env python3
"""Scaffold a new Fabric task-flows project. See _shared/lib/new_project.py."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
from new_project import (
    architecture_handoff,
    discovery_brief,
    pipeline_state,
    sanitize_name,
    scaffold,
    today,
)
from paths import REPO_ROOT


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scaffold a new Fabric task-flows project"
    )
    parser.add_argument(
        "name",
        help='Project display name (e.g., "Energy Field Intelligence")',
    )
    parser.add_argument(
        "--task-flow",
        default=None,
        help="Pre-set the task flow (optional — usually decided by architect)",
    )
    args = parser.parse_args()

    repo_root = REPO_ROOT
    if not (repo_root / "task-flows.md").exists():
        print(f"❌ Cannot find task-flows.md in {repo_root}")
        print("   Run this script from the repository root or scripts/ directory.")
        sys.exit(1)

    scaffold(str(repo_root), args.name, args.task_flow)


if __name__ == "__main__":
    main()
