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

> <!-- @fabric-advisor: paste the user's problem description here -->

### Inferred Signals

<!-- Valid signal names (must match for decision-resolver.py):
     Batch / Scheduled, Real-time / Streaming, Both / Mixed (Lambda),
     Machine Learning, Sensitive Data, Transactional,
     Unstructured / Semi-Structured, Data Quality / Layered,
     Application Backend, Document / NoSQL / AI-Ready, Semantic Governance -->

| Signal | Value | Confidence | Source |
|--------|-------|------------|--------|
| <!-- use signal names from list above --> | | | |

### Suggested Task Flow Candidates

| Candidate | Why It Fits | Confidence |
|-----------|-------------|------------|
| | | |

### Confirmed with User

- [ ] Project name confirmed
- [ ] Signals confirmed or corrected

### Architectural Judgment Calls

- <!-- design trade-offs only — NOT customer-answerable questions -->
"""


def architecture_handoff(project: str) -> str:
    return f"""---
project: {project}
task_flow: TBD
phase: draft
status: draft
created: {today()}
last_updated: {today()}
design_review:
  engineer: pending
  tester: pending
items: 0
acceptance_criteria: 0
manual_steps: 0
deployment_waves: 0
blockers:
  critical: []
  medium: []
next_phase: design-review
---

# Architecture Handoff — DRAFT

**Project:** {project}
**Task flow:** TBD
**Date:** {today()}
**Status:** DRAFT — Awaiting design review by /fabric-deploy and /fabric-test.

---

### Problem Reference
> See: prd/discovery-brief.md
> Summary: <!-- /fabric-design: ≤20 word summary -->

---

## Architecture Diagram

<!-- /fabric-design: Draw a project-specific ASCII data flow diagram.
     - Use box-drawing characters (┌─┐│└─┘, ──►, ──▶)
     - Data sources on the left, outputs on the right
     - Label every box with the ACTUAL project item name (e.g., "call-events-lakehouse", not just "Lakehouse")
     - Show how data flows between items with arrows
     - This is NOT the generic task-flow diagram — it's this project's specific architecture
-->

```
<!-- Replace this block with your ASCII diagram -->
```

---

## Decisions

<!-- DECISION CONTEXT (from decisions/_index.md quick_decision fields):
Storage: Spark/Python → Lakehouse | T-SQL analytics → Warehouse | T-SQL transactional → SQL Database | KQL time-series → Eventhouse | NoSQL/document → Cosmos DB
Ingestion: Real-time streaming → Eventstream | Database replication (CDC) → Mirroring | Small-medium + transforms needed → Dataflow Gen2 | Small-medium + no transforms → Copy Job | Large + code-first team → Pipeline + Notebook | Large + orchestration needed → Pipeline (Copy activity) | Complex orchestration (any volume) → Pipeline
Processing: Interactive + Python/Spark → Notebook | Interactive + KQL → KQL Queryset | Interactive + visual/no-code → Dataflow Gen2 | Production Spark + CI/CD → Spark Job Definition | Production Spark + simple schedule → Notebook (via Pipeline) | Production T-SQL → Stored Procedures | Production KQL → KQL Queryset (update policies) | Production Power Query → Dataflow Gen2
Visualization: Interactive exploration + filters → Power BI Report | Pixel-perfect / printable / multi-page → Paginated Report | Goal/KPI tracking + check-ins → Metrics Scorecard | Live streaming data (sub-second) → Real-Time Dashboard | Live geospatial/location data → Real-Time Map
Parameterization: Single environment → Environment Variables (or skip) | Multi-env + Fabric Git → Variable Library | Multi-env + fabric-cicd → parameter.yml | Multi-env + fab CLI → Environment Variables or Variable Library
-->

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Storage | | |
| Ingestion | | |
| Processing | | |
| Visualization | | |
| Semantic Model Query Mode | | |

### Items to Deploy

```yaml
items:
  # /fabric-design: fill in items
  # - id: 1
  #   name: ""
  #   type: ""
  #   skillset: ""
  #   depends_on: []
  #   purpose: ""
```

### Deployment Order

```yaml
waves:
  # /fabric-design: fill in waves
  # - id: 1
  #   items: []
  # - id: 2
  #   items: []
  #   blocked_by: [1]
```

### Acceptance Criteria

```yaml
acceptance_criteria:
  # /fabric-design: fill in ACs
  # - id: AC-1
  #   type: structural
  #   criterion: ""
  #   verify: ""
  #   target: ""
```

## Alternatives Considered

| # | Decision | Option Rejected | Why Rejected |
|---|----------|-----------------|--------------|
| | | | |

## Trade-offs

| # | Trade-off | Benefit | Cost | Mitigation |
|---|-----------|---------|------|------------|
| | | | | |

## Deployment Strategy

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Workspace Approach | | |
| Environments | | |
| CI/CD Tool | | |
| Parameterization | | |
| Branching Model | | |

## References

- Project folder: projects/{project}/
- Diagram: diagrams/TBD.md
- Validation: _shared/registry/validation-checklists.json

## Design Review

| Reviewer | Feedback Summary | Incorporated? | What Changed |
|----------|-----------------|---------------|--------------|
| /fabric-deploy | <!-- pending --> | | |
| /fabric-test | <!-- pending --> | | |
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


def docs_readme(project: str, display_name: str) -> str:
    return f"""# {display_name} — Architecture Documentation

> Generated: <!-- /fabric-document: timestamp -->
> Task flow: <!-- /fabric-document: task flow name -->
> Status: <!-- /fabric-document: DEPLOYED | VALIDATED | PARTIAL -->

## Overview

<!-- /fabric-document: 2-3 sentence summary -->

## Quick Links

| Document | Description |
|----------|-------------|
| [Architecture](architecture.md) | System diagram and item relationships |
| [Deployment Log](deployment-log.md) | What was deployed and how |
| [Deployments](../deployments/) | Scripts, notebooks, and queries |

### Decision Records

| ADR | Decision | Outcome |
|-----|----------|---------|
| [001-task-flow](decisions/001-task-flow.md) | Which task flow pattern? | |
| [002-storage](decisions/002-storage.md) | Storage layer | |
| [003-ingestion](decisions/003-ingestion.md) | Ingestion approach | |
| [004-processing](decisions/004-processing.md) | Processing/transformation | |
| [005-visualization](decisions/005-visualization.md) | Visualization | |
"""


def docs_architecture(project: str) -> str:
    return """# Architecture

<!-- /fabric-document: generate from Architecture Handoff -->

## System Diagram

<!-- /fabric-document: mermaid diagram -->

## Items

| Item | Type | Purpose | Dependencies |
|------|------|---------|--------------|
| | | | |

## Data Flow

<!-- /fabric-document: describe data movement -->

## Deployment Strategy

| Aspect | Choice |
|--------|--------|
| Workspace approach | |
| Environments | |
| CI/CD tool | |
| Branching model | |

## Configuration Summary

<!-- /fabric-document: pull Configuration Rationale from engineer handoff -->
"""


def docs_deployment_log(project: str) -> str:
    return """# Deployment Log

**Deployed:** <!-- /fabric-document: timestamp -->
**Task flow:** <!-- /fabric-document: name -->
**Validation Status:** <!-- /fabric-document: from validation report -->

## Items Deployed

| Order | Item | Type | Status | Notes |
|-------|------|------|--------|-------|
| | | | | |

## Implementation Notes

<!-- /fabric-document: pull from engineer handoff -->

## Configuration Rationale

<!-- /fabric-document: pull from engineer handoff -->

## Manual Steps

### Completed
<!-- /fabric-document: list from engineer -->

### Pending
<!-- /fabric-document: list from engineer -->

## Issues & Resolutions

| Issue | Resolution | Status |
|-------|-----------|--------|
| | | |

## Lessons Learned

<!-- /fabric-document: pull from validation report Future Considerations -->
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
            "0a-discovery":  {"status": "pending", "agent": "fabric-advisor",    "output": "prd/discovery-brief.md"},
            "1-design":      {"status": "pending", "agent": "fabric-design",     "output": "prd/architecture-handoff.md"},
            "2a-test-plan":  {"status": "pending", "agent": "fabric-test",       "output": "prd/test-plan.md"},
            "2b-sign-off":   {"status": "pending", "agent": None,               "gate": "human"},
            "2c-deploy":     {"status": "pending", "agent": "fabric-deploy",     "output": "prd/deployment-handoff.md"},
            "3-validate":    {"status": "pending", "agent": "fabric-test",       "output": "prd/validation-report.md"},
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
        os.path.join(project_dir, "prd"),
        os.path.join(project_dir, "docs", "decisions"),
        os.path.join(project_dir, "deployments"),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"  📁 {os.path.relpath(d, repo_root)}")

    # Create template files
    files = {
        # PRD files (agent handoffs)
        "prd/discovery-brief.md": discovery_brief(project),
        "prd/architecture-handoff.md": architecture_handoff(project),
        "prd/engineer-review.md": engineer_review(project),
        "prd/tester-review.md": tester_review(project),
        "prd/test-plan.md": test_plan(project),
        "prd/deployment-handoff.md": deployment_handoff(project),
        "prd/validation-report.md": validation_report(project),
        # Status
        "STATUS.md": status_md(project, display_name),
        # Pipeline state (orchestration tracking)
        "pipeline-state.json": pipeline_state(project),
        # Docs (documenter fills these)
        "docs/README.md": docs_readme(project, display_name),
        "docs/architecture.md": docs_architecture(project),
        "docs/deployment-log.md": docs_deployment_log(project),
        "docs/decisions/001-task-flow.md": adr_template("001", "Task Flow Selection"),
        "docs/decisions/002-storage.md": adr_template("002", "Storage Layer Selection"),
        "docs/decisions/003-ingestion.md": adr_template("003", "Ingestion Approach"),
        "docs/decisions/004-processing.md": adr_template("004", "Processing Selection"),
        "docs/decisions/005-visualization.md": adr_template("005", "Visualization Selection"),
    }

    for rel_path, content in files.items():
        full_path = os.path.join(project_dir, rel_path)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  📄 {os.path.relpath(full_path, repo_root)}")

    print()

    # Update PROJECTS.md
    update_projects_md(repo_root, project)

    print()
    print(f"✅ Project '{project}' scaffolded with {len(files)} template files")
    print()
    print("Next steps:")
    print("  1. Invoke @fabric-advisor to fill in prd/discovery-brief.md")
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
