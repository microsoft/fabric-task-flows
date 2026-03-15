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

> **File editing:** This file is pre-scaffolded. Replace the **entire file contents** using the `edit` tool — use the full existing file as `old_str` and the completed handoff as `new_str`. Do NOT use `create` (the file already exists) or pass an empty `old_str`.

> **⚡ Fast-forward mode:** When advancing from discovery, the pipeline may auto-generate the complete handoff (items, waves, ACs, decisions, diagram) and fast-forward directly to sign-off. In this case, the agent reviews the pre-generated content rather than writing from scratch.

If the handoff file is **already populated** (has YAML frontmatter with real `task_flow`, filled items/waves/ACs):
- **Review** the pre-generated content for accuracy
- **Enhance** with project-specific rationale, trade-offs, and deployment strategy
- **Verify** the architecture diagram is present and correct

If the handoff file is **still a template** (contains `task_flow: TBD` or `items: []`):
- Write the complete handoff from scratch using the scaffolded template structure
- Include YAML frontmatter with `task_flow`

In either case, fill in the `> Summary:` line with a ≤20-word summary of the problem statement from the discovery brief.

## Constraints

- **Preserve YAML code blocks** — `diagram-gen.py` parses `items:` and `waves:` blocks to generate the architecture diagram. Do NOT convert them to markdown tables.
- Never deploy or create Fabric items
- Never skip "Alternatives Considered" or "Trade-offs"

## Handoff

After producing the output file, advance:
```bash
python _shared/scripts/run-pipeline.py advance --project <project-name> -q
```

If the output shows `🟢 AUTO-CHAIN → <skill>`, **invoke that skill immediately** — do NOT stop and ask the user.
Only `🛑 HUMAN GATE` (Phase 2b sign-off) requires user action.
