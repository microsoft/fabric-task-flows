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

> **⚡ Fast-forward:** After sign-off approval, `run-pipeline.py` auto-generates `docs/README.md`, `docs/architecture.md`, and `docs/deployment-log.md` deterministically from handoff data. This skill is only invoked if fast-forward was skipped, or for ADR polish and enhancement.

## Instructions

### Step 1: Verify Pre-Generated Docs

Check if `_projects/[name]/docs/` already contains:
- `README.md` — project overview with items table
- `architecture.md` — wave-by-wave deployment order
- `deployment-log.md` — timeline and item status

If these exist, **review and enhance** rather than rewrite. Add narrative, context, and stakeholder-friendly language.

### Step 2: Polish ADRs

Review and polish the architect's ADR drafts (`docs/decisions/001-005.md`) in parallel. Add `006-cicd.md` for multi-environment projects.

This is the primary value-add of this skill — ADRs require judgment and narrative that scripts cannot provide.

### Step 3: Enhance Documentation (Optional)

If the pre-generated docs need enrichment:
- Add data flow narratives to `architecture.md`
- Add operational runbooks to `README.md`
- Add troubleshooting guides based on `_shared/learnings.md`

## Constraints

- Documents only — no architecture decisions or deployments
- Enhance pre-generated docs, don't replace them

## Handoff

After producing the output files:
```bash
python _shared/scripts/run-pipeline.py advance --project <project-name> -q
```

This updates `PROJECTS.md` status to "Documented ✅".

If the output shows `🟢 AUTO-CHAIN → <skill>`, **invoke that skill immediately** — do NOT stop and ask the user.
Only `🛑 HUMAN GATE` (Phase 2b sign-off) requires user action.
