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

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
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

> <!-- Filled by /fabric-discover from the user's problem description -->

### Inferred Signals

| Signal | Confidence | Source |
|--------|------------|--------|

### Task Flow Candidates

| Candidate | Score | Why It Fits |
|-----------|-------|-------------|

### Architectural Judgment Calls

- <!-- Filled by /fabric-discover -->
"""


def architecture_handoff(project: str) -> str:
    return f"""---
project: {project}
task_flow: TBD
created: {today()}
items: 0
deployment_waves: 0
---

# Architecture Handoff — {project}

<!-- This file is overwritten by handoff-scaffolder.py during the Design phase.
     Run: python .github/skills/fabric-design/scripts/handoff-scaffolder.py \\
          --task-flow <id> --project {project} --output docs/architecture-handoff.md -->
"""


def engineer_review(project: str) -> str:
    return f"""```yaml
# Engineer Review — /fabric-deploy Mode 0
# Schema: _shared/schemas/engineer-review.md
project: {project}
task_flow: TBD
review_date: {today()}
architecture_version: draft

findings: []
  # - id: F-1
  #   area: ""
  #   severity: green
  #   finding: ""
  #   suggestion: ""

wave_optimization:
  current_waves: 0
  proposed_waves: 0
  changes: []

cli_verification: []

prerequisites: []

assessment: pending  # ready | needs-changes | blocked
must_fix: []
should_fix: []
no_change: []
```
"""


def tester_review(project: str) -> str:
    return f"""```yaml
# Tester Review — /fabric-test Mode 0
# Schema: _shared/schemas/tester-review.md
project: {project}
task_flow: TBD
review_date: {today()}

findings: []
  # - id: T-1
  #   area: ""
  #   severity: green
  #   finding: ""
  #   suggestion: ""

untestable_criteria: []
missing_coverage: []

blockers:
  architecture: []
  deployment: []

assessment: pending  # testable | needs-refinement | major-gaps
must_fix: []
should_fix: []
```
"""


def test_plan(project: str) -> str:
    return f"""```yaml
# Test Plan — /fabric-test Mode 1
# Schema: .github/skills/fabric-test/schemas/test-plan.md
project: {project}
task_flow: TBD
architecture_date: {today()}
test_plan_date: ""

criteria_mapping: []
  # - ac_id: AC-1
  #   type: structural
  #   checklist_ref: ""
  #   test_method: ""

critical_verification: []
edge_cases: []

blockers:
  architecture: []
  deployment: []
```
"""


def deployment_handoff(project: str) -> str:
    return f"""```yaml
# Deployment Handoff — /fabric-deploy
# Schema: .github/skills/fabric-deploy/schemas/deployment-handoff.md
project: {project}
task_flow: TBD
validation_checklist: ""
deployment_tool: fabric-cicd
parameterization: none

items: []
  # - name: ""
  #   type: ""
  #   wave: 1
  #   status: deployed
  #   command: ""
  #   notes: ""

waves: []

manual_steps:
  completed: []
  pending: []

known_issues: []
cicd_notes: []
```

### Implementation Notes
<!-- Max 150 words. Document ONLY deviations from the architecture handoff. -->

### Configuration Rationale

| Item | Setting | Why |
|------|---------|-----|
| | | |
"""


def validation_report(project: str) -> str:
    return f"""```yaml
# Validation Report — /fabric-test Mode 2
# Schema: .github/skills/fabric-test/schemas/validation-report.md
project: {project}
task_flow: TBD
date: ""
status: pending  # passed | partial | failed

phases:
  - name: Foundation
    status: pending
    notes: ""
  - name: Environment
    status: pending
    notes: ""
  - name: Ingestion
    status: pending
    notes: ""
  - name: Transformation
    status: pending
    notes: ""
  - name: Visualization
    status: pending
    notes: ""
  - name: CI/CD Readiness
    status: na
    notes: ""

items_validated: []
manual_steps: []
issues: []
next_steps: []
```

### Validation Context
<!-- Max 100 words. What successful validation means for this project. -->

### Future Considerations
<!-- Max 100 words. Operational learnings. -->
"""


def status_md(project: str, display_name: str) -> str:
    return f"""# {display_name} — Project Status

**Project ID:** {project}
**Created:** {today()}

## Current State

| Field | Value |
|-------|-------|
| Phase | Discovery |
| Task Flow | TBD |
| Blockers | None |
| Next Action | Architecture Design (Phase 1a) |

## Phase Progression

| Phase | Date | Notes |
|-------|------|-------|
| Discovery | {today()} | Discovery Brief produced |

## Blockers

None.

## Wave Progress

<!-- Updated by /fabric-deploy during deployment -->

| Wave | Items | Status |
|------|-------|--------|
| | | |

## Manual Steps

<!-- Updated by /fabric-deploy during deployment -->

| ID | Description | Status |
|----|-------------|--------|
| | | |
"""


def adr_template(number: str, title: str) -> str:
    return f"""# ADR-{number}: {title}

## Status

Accepted

**Date:** <!-- /fabric-document: date -->
**Deciders:** fabric-architect agent + user confirmation

## Context

<!-- /fabric-document: problem, constraints, requirements -->

## Decision

<!-- /fabric-document: what was chosen -->

## Alternatives Considered

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| | | | |

## Consequences

### Benefits
<!-- /fabric-document: what this enables -->

### Costs
<!-- /fabric-document: what this limits -->

### Mitigations
<!-- /fabric-document: how costs are addressed -->

## References

- Decision guide: <!-- /fabric-document: link to decisions/*.md -->
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
            "4-document":    {"status": "pending", "agent": "fabric-document",   "output": "docs/"}
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
# PROJECTS.md updater
# ---------------------------------------------------------------------------

def update_projects_md(repo_root: str, project: str):
    """Add a row to PROJECTS.md."""
    projects_path = os.path.join(repo_root, "PROJECTS.md")
    if not os.path.exists(projects_path):
        print(f"  ⚠ PROJECTS.md not found at {projects_path}, skipping")
        return

    with open(projects_path, "r", encoding="utf-8") as f:
        content = f.read()

    new_row = (
        f"| {project} | TBD | Discovery | "
        f"Scaffolded — awaiting Discovery Brief | None | "
        f"Discovery (Phase 0a) |"
    )

    if project in content:
        print(f"  ⚠ Project '{project}' already exists in PROJECTS.md, skipping")
        return

    # Insert before the phase legend section
    marker = "\n> Project rows"
    if marker in content:
        content = content.replace(marker, f"\n{new_row}{marker}")
    else:
        # Fallback: insert after the last table row
        lines = content.split("\n")
        insert_idx = None
        for i, line in enumerate(lines):
            if line.startswith("|") and "---" not in line and "Project" not in line:
                insert_idx = i + 1
        if insert_idx:
            lines.insert(insert_idx, new_row)
            content = "\n".join(lines)

    with open(projects_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("  ✅ Added row to PROJECTS.md")


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
    # Future-phase files (test, validate, document, ADRs) created when their phase runs
    files = {
        "docs/discovery-brief.md": discovery_brief(project),
        "docs/architecture-handoff.md": architecture_handoff(project),
        "pipeline-state.json": pipeline_state(project),
    }

    for rel_path, content in files.items():
        full_path = os.path.join(project_dir, rel_path)
        with open(full_path, "w", encoding="utf-8") as f:
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

    # Find repo root (look for task-flows.md)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)

    if not os.path.exists(os.path.join(repo_root, "task-flows.md")):
        print(f"❌ Cannot find task-flows.md in {repo_root}")
        print("   Run this script from the repository root or scripts/ directory.")
        sys.exit(1)

    scaffold(repo_root, args.name, args.task_flow)


if __name__ == "__main__":
    main()
