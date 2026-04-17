#!/usr/bin/env python3
"""
Scaffold a new Fabric task-flows project.

Creates the full directory tree and template files with YAML frontmatter
and section headers pre-filled. Agents then fill in content — no mkdir,
no boilerplate composition needed.

Usage:
    python scripts/new-project.py "Energy Field Intelligence"
    python scripts/new-project.py "Fraud Detection" --task-flow medallion
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import bootstrap  # noqa: F401
from paths import REPO_ROOT
from text_utils import slugify


def sanitize_name(name: str) -> str:
    """Convert project name to kebab-case folder name."""
    return slugify(name)


def today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Template files — structure is deterministic, content placeholders for agents
# ---------------------------------------------------------------------------

def discovery_brief(project: str) -> str:
    return f"""## Discovery Brief

**Project:** {project}
**Date:** {today()}

### Problem Statement

> <!-- AGENT: FILL --> Filled by /fabric-discover from the user's problem description

### 4 V's Assessment

<!-- AGENT: FILL -->
Populated by `intake-writer.py` after the user confirms each V. Each entry has
a value and a source (`user`, `inferred`, or `unknown`).

| V | Value | Source |
|---|-------|--------|
| Volume | — | unknown |
| Velocity | — | unknown |
| Variety | — | unknown |
| Versatility | — | unknown |

### Inferred Signals

| Signal | Value | Confidence | Source |
|--------|-------|------------|--------|

### Task Flow Candidates

| Candidate | Score | Why It Fits |
|-----------|-------|-------------|

### Architectural Judgment Calls

- <!-- AGENT: FILL --> Filled by /fabric-discover

### Confirmed with User

<!-- AGENT: FILL -->
Echo back the problem statement, 4 V's, top signals, and candidate task flows
so the user can confirm before design begins. See
`fabric-discover/SKILL.md` Step 6.
"""


def architecture_handoff(project: str) -> str:
    return f"""---
project: {project}
task_flow: TBD
created: {today()}
items: []
deployment_waves: 0
---

# Architecture Handoff — {project}

## Summary

<!-- AGENT: FILL -->

<!-- This file is overwritten by handoff-scaffolder.py during the Design phase.
     Run: python .github/skills/fabric-design/scripts/handoff-scaffolder.py \\
          --task-flow <id> --project {project} --output docs/architecture-handoff.md -->
"""


def pipeline_state(project: str) -> str:
    """Initial pipeline state file for orchestration tracking."""
    import json
    state = {
        "project": project,
        "task_flow": None,
        "current_phase": "0a-discovery",
        "problem_statement": None,
        "sign_off_revisions": 0,
        "phases": {
            "0a-discovery":  {"status": "pending", "agent": "fabric-advisor",    "output": "docs/discovery-brief.md"},
            "1-design":      {"status": "pending", "agent": "fabric-design",     "output": "docs/architecture-handoff.md"},
            "2a-test-plan":  {"status": "pending", "agent": "fabric-test",       "output": "docs/test-plan.md"},
            "2b-sign-off":   {"status": "pending", "agent": None,               "gate": "human"},
            "2c-deploy":     {"status": "pending", "agent": "fabric-deploy",     "output": "docs/deployment-handoff.md"},
            "3-validate":    {"status": "pending", "agent": "fabric-test",       "output": "docs/validation-report.md"},
            "4-document":    {"status": "pending", "agent": "fabric-document",   "output": "docs/project-brief.md"}
        },
        "transitions": [
            {"from": "0a-discovery", "to": "1-design",     "auto": True},
            {"from": "1-design",     "to": "2a-test-plan", "auto": True},
            {"from": "2a-test-plan", "to": "2b-sign-off",  "auto": True},
            {"from": "2b-sign-off",  "to": "2c-deploy",    "auto": False, "gate": "human"},
            {"from": "2b-sign-off",  "to": "1-design",     "auto": False, "gate": "revision", "max_cycles": 3},
            {"from": "2c-deploy",    "to": "3-validate",   "auto": True},
            {"from": "3-validate",   "to": "4-document",   "auto": True}
        ]
    }
    return json.dumps(state, indent=2)


# ---------------------------------------------------------------------------
# Main scaffolding
# ---------------------------------------------------------------------------

def scaffold(repo_root: str, display_name: str, task_flow: str | None = None):
    project = sanitize_name(display_name)
    project_dir = os.path.join(repo_root, "_projects", project)

    if os.path.exists(project_dir):
        print(f"❌ Project directory already exists: {project_dir}")
        print("   Use a different name or remove the existing directory.")
        sys.exit(1)

    print(f"🏗️  Scaffolding project: {display_name}")
    print(f"   Folder: projects/{project}/")
    print()

    # Create directory tree
    dirs = [
        os.path.join(project_dir, "docs"),
        os.path.join(project_dir, "deploy"),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"  📁 {os.path.relpath(d, repo_root)}")

    # Create template files — only for current-sprint phases
    # Future-phase files (test, validate, document) created when their phase runs
    files = {
        "docs/discovery-brief.md": discovery_brief(project),
        "docs/architecture-handoff.md": architecture_handoff(project),
        "pipeline-state.json": pipeline_state(project),
    }

    for rel_path, content in files.items():
        full_path = os.path.join(project_dir, rel_path)
        with open(full_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"  📄 {os.path.relpath(full_path, repo_root)}")

    print()
    print(f"✅ Project '{project}' scaffolded with {len(files)} files")
    print()
    print("Next steps:")
    print("  1. Invoke @fabric-advisor to fill in docs/discovery-brief.md")
    print("  2. Each agent edits its pre-created file — no file creation needed")
    print("  3. Pipeline auto-chains per _shared/workflow-guide.md")


def main():
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

    repo_root = str(REPO_ROOT)

    if not os.path.exists(os.path.join(repo_root, "task-flows.md")):
        print(f"❌ Cannot find task-flows.md in {repo_root}")
        print("   Run this script from the repository root or scripts/ directory.")
        sys.exit(1)

    scaffold(repo_root, args.name, args.task_flow)


if __name__ == "__main__":
    main()
