---
name: fabric-document
description: >
  Synthesizes all pipeline handoffs into a single human-readable project brief.
  Use when user says "generate docs", "create documentation", "document the
  project", or after validation passes. Do NOT use for deployment (use
  fabric-deploy) or architecture design (use fabric-design).
---

# Fabric Documentation

> **Goal:** Produce ONE deliverable — `docs/project-brief.md` — that a CTO can read in 10 minutes.

## Instructions

### Step 1: Read Pipeline Handoffs

Read these files **in parallel** from `_projects/[name]/docs/` (all are independent inputs):
- `discovery-brief.md` — problem statement and signals
- `architecture-handoff.md` — items, waves, decisions, trade-offs, diagram
- `deployment-handoff.md` — what was deployed, config rationale, manual steps
- `test-plan.md` — acceptance criteria, edge cases
- `validation-report.md` — pass/fail results

### Step 2: Synthesize into `project-brief.md`

Write ONE file: `_projects/[name]/docs/project-brief.md`

Follow the template in `references/documentation-templates.md`. Key rules:
1. **~1,500 words max** — every fact appears exactly once
2. **Decisions inline** — as a table in "Why This Architecture", NOT separate ADR files
3. **No separate files** — do NOT create README.md, architecture.md, deployment-log.md, or decisions/*.md
4. **Synthesize, don't copy** — distill the handoffs into narrative, don't paste YAML blocks

### Step 3: Verify Completeness

The brief must answer these 5 questions:
1. What problem are we solving? (from discovery)
2. What did we build? (items + diagram from architecture)
3. Why this approach? (decisions from architecture)
4. How to deploy it? (from deployment handoff)
5. Did it work? (from validation)

## Constraints

- Documents only — no architecture decisions or deployments
- ONE output file: `project-brief.md`
- Do NOT create README.md, architecture.md, deployment-log.md, or decisions/*.md

## Handoff

After producing the output file:
```bash
python _shared/scripts/run-pipeline.py advance --project <project-name> -q
```

If the output shows `🟢 AUTO-CHAIN → <skill>`, **invoke that skill immediately** — do NOT stop and ask the user.
Only `🛑 HUMAN GATE` (Phase 2b sign-off) requires user action.
