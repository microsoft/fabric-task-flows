---
name: fabric-test
description: >
  The QA skill — reviews architecture for testability, creates test plans from
  acceptance criteria, and validates deployments. Use when user says "create
  test plan", "validate deployment", "run validation", "review architecture",
  "check items", "what should we test", or after architecture is finalized or
  deployment is complete. Do NOT use for architecture design (use fabric-design)
  or deployment (use fabric-deploy).
pre-compute: [test-plan-prefill]
---

# Fabric Testing & Validation (QA Role)

## Mode 1: Architecture Review + Test Plan (Phase 2a)

The runner pre-generates `test-plan.md` via `test-plan-prefill.py` before this skill is invoked. Your job: (1) verify each acceptance criterion maps to the correct items/waves from the architecture handoff, (2) add edge cases and expected results where missing, (3) replace every `<!-- AGENT: FILL -->` marker with real content. Set `review_outcome`: `approved` (no red blockers) or `concerns` (has red). Do NOT rewrite from scratch — edit in place.

## Mode 2: Post-Deployment Validation (Phase 3)

For live workspace validation:
```bash
python .github/skills/fabric-test/scripts/validate-items.py _projects/[name]/docs/deployment-handoff.md
```

`validate-items.py` emits a manual validation checklist (it does not call the Fabric REST API). Follow the checklist from tool output. Write `_projects/[name]/docs/validation-report.md` with `status: passed | partial | failed`.

If any finding is `routed_to: engineer`, also write `remediation-log.md` per the schema at `.github/skills/fabric-test/schemas/remediation-log.md`.

## Constraints

- Never invent ACs not in the Architecture Handoff
- Never modify Fabric items — validate only

## Handoff

> Handoff: see [`_shared/workflow-guide.md`](../../../_shared/workflow-guide.md#handoff) — call `run-pipeline.py advance -q` after writing the output file; AUTO-CHAIN unless a HUMAN GATE fires.
