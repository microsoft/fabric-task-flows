---
name: fabric-design
description: >
  The Architect skill — designs Microsoft Fabric architectures and produces
  the FINAL architecture handoff. Use when user says "design architecture",
  "which task flow", "medallion vs lambda", "create architecture", or asks
  about Fabric architecture patterns. Do NOT use for deployment (use
  fabric-deploy), testing (use fabric-test), or discovery (use
  fabric-discover).
pre-compute: [decision-resolver, handoff-scaffolder]
# author: task-flows-team
# version: 3.0.0
# category: architecture
# tags: [fabric, task-flow, architecture-design, decisions]
# pipeline-phases: [1-design]
---

# Fabric Architecture Design (Architect Role)

## Phase 1-design: Architecture Design

### Step 1: Load Discovery Brief

Read `_projects/[name]/prd/discovery-brief.md` for inferred signals, 4V's, and task flow candidates.

If no Discovery Brief exists, ask for project name, problem statement, team skillset, and workspace strategy.

### Step 2: Select Task Flow

Reference `task-flows.md` for the 11 options + general. For complex multi-pattern requirements, compose a **hybrid** using a base flow + overlays (document rationale in ADR 001).

### Step 3: Resolve Architectural Decisions

```bash
python .github/skills/fabric-design/scripts/decision-resolver.py --discovery-brief _projects/[name]/prd/discovery-brief.md --format yaml
```

- **High confidence** → accept the choice
- **Ambiguous** → read the referenced guide to resolve, present trade-offs to user

Run `decision-resolver.py --help` for signal keys and fallback options.

> **Visualization terminology:** "dashboard" → **Report** (batch) or **Real-Time Dashboard** (streaming/Eventhouse).

### Step 3b: Parameterization (Multi-Environment Only)

If multi-environment and Variable Library chosen: add it as a **Wave 1 item**.

### Step 4: Produce FINAL Architecture Handoff

Write to `_projects/[name]/prd/architecture-handoff.md` using the scaffolded template structure. Include YAML frontmatter with `task_flow`.

### Step 5: Write ADRs

Edit template files `docs/decisions/001-005.md` in parallel (task-flow, storage, ingestion, processing, visualization).

---

## Constraints

- Architecture Handoff: max 220 lines
- Never deploy or create Fabric items
- Never skip "Alternatives Considered" or "Trade-offs"

## Handoff

After producing the output file, advance:
```bash
python _shared/scripts/run-pipeline.py advance --project <project-name> -q
```
