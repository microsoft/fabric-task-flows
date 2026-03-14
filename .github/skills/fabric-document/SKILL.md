---
name: fabric-document
description: >
  Synthesizes all pipeline handoffs into wiki-style documentation with
  Architecture Decision Records (ADRs). Use when user says "generate docs",
  "create documentation", "write ADRs", "produce wiki", "document the
  project", or after validation passes. Do NOT use for deployment (use
  fabric-deploy) or architecture design (use fabric-design).
---

# Fabric Documentation

## Instructions

### Step 1: Collect Handoffs

Parse YAML fields from all handoff documents in `_projects/[name]/prd/`.

### Step 2: Generate Wiki Pages

Write to `_projects/[name]/docs/`:
- **README.md** — Stakeholder-friendly overview
- **architecture.md** — Architecture narrative with data flow
- **deployment-log.md** — Deployment consolidation

Use templates from `references/documentation-templates.md`.

### Step 3: Polish ADRs

Review and polish the architect's ADR drafts (`docs/decisions/001-005.md`) in parallel. Add `006-cicd.md` for multi-environment projects.

## Constraints

- Documents only — no architecture decisions or deployments

## Handoff

After producing the output files:
```bash
python _shared/scripts/run-pipeline.py advance --project <project-name> -q
```

This updates `PROJECTS.md` status to "Documented ✅".

If the output shows `🟢 AUTO-CHAIN → <skill>`, **invoke that skill immediately** — do NOT stop and ask the user.
Only `🛑 HUMAN GATE` (Phase 2b sign-off) requires user action.
