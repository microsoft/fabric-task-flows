---
name: fabric-test
description: >
  The QA skill — reviews architecture for testability, creates test plans from
  acceptance criteria, and validates deployments. Use when user says "create
  test plan", "validate deployment", "run validation", "review architecture",
  "check items", "what should we test", or after architecture is finalized or
  deployment is complete. Do NOT use for architecture design (use fabric-design)
  or deployment (use fabric-deploy).
pre-compute: [test-plan-prefill, validate-items]
---

# Fabric Testing & Validation (QA Role)

## Mode 1: Architecture Review + Test Plan (Phase 2a)

> **⚡ Fast-forward:** This phase is auto-completed by `run-pipeline.py` fast-forward. The test plan is pre-filled deterministically. This skill is only invoked if fast-forward fails or the user requests manual review.

### Step 1: Load Architecture

Read `_projects/[name]/docs/architecture-handoff.md`. Extract items, ACs, waves.

### Step 2: Review + Produce Test Plan

> The test plan at `_projects/[name]/docs/test-plan.md` is pre-filled with criteria mapping from the pipeline's auto-generation. **Enhance rather than rewrite.**

1. Assess testability and feasibility — flag concerns (`red` blocks, `yellow` warns)
2. Map each AC to test method, verification command, expected result
3. Write to `_projects/[name]/docs/test-plan.md`

Set `review_outcome`: `approved` (no red) or `concerns` (has red).

## Mode 2: Post-Deployment Validation (Phase 3)

> **⚡ Fast-forward:** After sign-off approval, `run-pipeline.py` auto-generates `validation-report.md` with all ACs marked as structural pass. This skill is only invoked if the fast-forward was skipped, or for live workspace validation.

### Step 1: Verify Pre-Generated Report

Check if `_projects/[name]/docs/validation-report.md` already exists with structural validation results. If it does, **review rather than recreate**.

For live workspace validation (not design-only), run:
```bash
python .github/skills/fabric-test/scripts/validate-items.py _projects/[name]/docs/deployment-handoff.md
```

### Step 2: Verify + Report

1. Complete manual configuration steps from checklist
2. Run smoke tests (query, pipeline trigger, report render)
3. Update `_projects/[name]/docs/validation-report.md` with `status: passed | failed`

## Constraints

- Never invent ACs not in the Architecture Handoff
- Never modify Fabric items — validate only

## Handoff

After producing the output file, advance:
```bash
python _shared/scripts/run-pipeline.py advance --project <project-name> -q
```

Phase 2a triggers human gate (sign-off). Phase 3 routes to Document or Remediation based on validation result.

If the output shows `🟢 AUTO-CHAIN → <skill>`, **invoke that skill immediately** — do NOT stop and ask the user.
Only `🛑 HUMAN GATE` (Phase 2b sign-off) requires user action.
