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

> **⚡ Fast-forward:** This phase is auto-completed by `run-pipeline.py` fast-forward. The test plan is pre-filled by `test-plan-prefill.py`. This skill is only invoked if fast-forward fails or the user requests manual review.

### Step 1: Review Pre-Filled Test Plan

The test plan at `_projects/[name]/docs/test-plan.md` is pre-generated. Review for:
- Testability concerns (`red` blockers, `yellow` warnings)
- Missing edge cases or expected results

Enhance if needed; do not rewrite from scratch.

Set `review_outcome`: `approved` (no red) or `concerns` (has red).

## Mode 2: Post-Deployment Validation (Phase 3)

For live workspace validation:
```bash
python .github/skills/fabric-test/scripts/validate-items.py _projects/[name]/docs/deployment-handoff.md
```

Follow the checklist from tool output. Write `_projects/[name]/docs/validation-report.md` with `status: passed | failed`.

## Constraints

- Never invent ACs not in the Architecture Handoff
- Never modify Fabric items — validate only

## Handoff

After producing the output file, advance:
```bash
python _shared/scripts/run-pipeline.py advance --project <project-name> -q
```

If the output shows `🟢 AUTO-CHAIN → <skill>`, **invoke that skill immediately** — do NOT stop and ask the user.
Only `🛑 HUMAN GATE` (Phase 2b sign-off) requires user action.
