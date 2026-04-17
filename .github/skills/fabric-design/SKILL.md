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
---

# Fabric Architecture Design (Architect Role)

## Phase 1-design: Architecture Design

### Step 1: Load Discovery Brief

Read `_projects/[name]/docs/discovery-brief.md` for inferred signals, 4V's, and task flow candidates.

### Step 2: Select Task Flow

Reference `task-flows.md`. For complex multi-pattern requirements, compose a **hybrid** using a base flow + overlays (document rationale inline in the handoff).

### Step 3: Resolve Architectural Decisions

```bash
python .github/skills/fabric-design/scripts/decision-resolver.py --discovery-brief _projects/[name]/docs/discovery-brief.md --format yaml
```

- **High confidence** → accept the choice
- **Ambiguous** → read the referenced guide to resolve, present trade-offs to user

Run `decision-resolver.py --help` for signal keys and fallback options.

### Step 4: Produce FINAL Architecture Handoff

Write to `_projects/[name]/docs/architecture-handoff.md`.

The runner pre-generates `architecture-handoff.md` (items, waves, ACs, decisions, diagram) before this skill is invoked. Your job: (1) verify accuracy against the discovery brief and decision-resolver output, (2) add project-specific rationale, trade-offs, and deployment strategy, (3) replace the `<!-- AGENT: FILL -->` marker in the `## Summary` line (and anywhere else it appears) with a ≤20-word summary of the problem statement. Do NOT rewrite the pre-generated YAML blocks from scratch — edit in place using the `edit` tool.

## Constraints

- **Preserve YAML code blocks** — `diagram-gen.py` parses `items:` and `waves:` blocks to generate the architecture diagram. Do NOT convert them to markdown tables.
- Never deploy or create Fabric items
- Never skip "Alternatives Considered" or "Trade-offs"

## Handoff

> Handoff: see [`_shared/workflow-guide.md`](../../../_shared/workflow-guide.md#handoff) — call `run-pipeline.py advance -q` after writing the output file; AUTO-CHAIN unless a HUMAN GATE fires.
