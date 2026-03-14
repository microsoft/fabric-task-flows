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
# author: task-flows-team
# version: 3.0.0
# category: quality
# tags: [fabric, testing, validation, acceptance-criteria, qa, review]
# pipeline-phases: [2a-test-plan, 3-validate]
---

# Fabric Testing & Validation (QA Role)

## Mode 1: Architecture Review + Test Plan (Phase 2a)

> **Output is lightweight.** Write a concise YAML test plan per the schema in `schemas/test-plan.md`. Do NOT present a sign-off summary — the pipeline auto-advances to Phase 2b where the user reviews both the architecture handoff and test plan.

### Step 1: Load Architecture

Read `_projects/[name]/prd/architecture-handoff.md`. Extract items, ACs, waves.

### Step 2: Pre-fill Registry Data

```bash
python .github/skills/fabric-test/scripts/test-plan-prefill.py --handoff _projects/[name]/prd/architecture-handoff.md
```

### Step 3: Review + Produce Test Plan

1. Assess testability and feasibility — flag concerns (`red` blocks, `yellow` warns)
2. Map each AC to test method, verification command, expected result
3. Write to `_projects/[name]/prd/test-plan.md`

Set `review_outcome`: `approved` (no red) or `concerns` (has red).

---

## Mode 2: Post-Deployment Validation (Phase 3)

### Step 1: Generate Config Checklist

```bash
python .github/skills/fabric-test/scripts/validate-items.py _projects/[name]/prd/deployment-handoff.md
```

### Step 2: Verify + Report

1. Complete manual configuration steps from checklist
2. Run smoke tests (query, pipeline trigger, report render)
3. Update `_projects/[name]/prd/validation-report.md` with `status: passed | failed`

---

## Constraints

- Never invent ACs not in the Architecture Handoff
- Never modify Fabric items — validate only

## Handoff

After producing the output file, advance:
```bash
python _shared/scripts/run-pipeline.py advance --project <project-name> -q
```

Phase 2a triggers human gate (sign-off). Phase 3 routes to Document or Remediation based on validation result.
