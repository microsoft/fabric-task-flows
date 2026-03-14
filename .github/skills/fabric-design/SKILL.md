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

Reference `task-flows.md` for the 11 options + general. For complex multi-pattern requirements, compose a **hybrid** using a base flow + overlays (document rationale in ADR 001).

### Step 3: Resolve Architectural Decisions

```bash
python .github/skills/fabric-design/scripts/decision-resolver.py --discovery-brief _projects/[name]/docs/discovery-brief.md --format yaml
```

- **High confidence** → accept the choice
- **Ambiguous** → read the referenced guide to resolve, present trade-offs to user

Run `decision-resolver.py --help` for signal keys and fallback options.

> **Visualization terminology:** "dashboard" → **Report** (batch) or **Real-Time Dashboard** (streaming/Eventhouse).

### Step 3b: Parameterization (Multi-Environment Only)

If multi-environment and Variable Library chosen: add it as a **Wave 1 item**.

### Step 4: Produce FINAL Architecture Handoff

Write to `_projects/[name]/docs/architecture-handoff.md`.

> **⚡ Fast-forward mode:** When advancing from discovery, the pipeline may auto-generate the complete handoff (items, waves, ACs, decisions, diagram, ADRs) and fast-forward directly to sign-off. In this case, the agent reviews the pre-generated content rather than writing from scratch.

If the handoff file is **already populated** (has YAML frontmatter with real `task_flow`, filled items/waves/ACs):
- **Review** the pre-generated content for accuracy
- **Enhance** with project-specific rationale, trade-offs, and deployment strategy
- **Verify** the architecture diagram is present and correct

If the handoff file is **still a template** (contains `task_flow: TBD` or `items: []`):
- Write the complete handoff from scratch using the scaffolded template structure
- Include YAML frontmatter with `task_flow`

In either case, fill in the `> Summary:` line with a ≤20-word summary of the problem statement from the discovery brief.

### Step 5: Write ADRs

> **⚡ Fast-forward mode:** ADR files may be auto-populated by the pipeline from decision-resolver output. If they contain real decisions (not just template placeholders), review and enhance rather than rewrite.

Edit template files `docs/decisions/001-005.md` in parallel (task-flow, storage, ingestion, processing, visualization).

The scaffolded templates share an identical body structure. The title line for each file is:

| File | Title Line |
|------|-----------|
| `001-task-flow.md` | `# ADR-001: Task Flow Selection` |
| `002-storage.md` | `# ADR-002: Storage Layer Selection` |
| `003-ingestion.md` | `# ADR-003: Ingestion Approach` |
| `004-processing.md` | `# ADR-004: Processing Selection` |
| `005-visualization.md` | `# ADR-005: Visualization Selection` |

The template body after the title is identical for all 5 files:

```
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
```

Replace each file's **entire content** in a single edit — the `old_str` is the full file content above (with the appropriate title line). Write all 5 ADRs in parallel.

## Constraints

- Architecture Handoff: max 220 lines
- Never deploy or create Fabric items
- Never skip "Alternatives Considered" or "Trade-offs"

## Handoff

After producing the output file, advance:
```bash
python _shared/scripts/run-pipeline.py advance --project <project-name> -q
```

If the output shows `🟢 AUTO-CHAIN → <skill>`, **invoke that skill immediately** — do NOT stop and ask the user.
Only `🛑 HUMAN GATE` (Phase 2b sign-off) requires user action.
