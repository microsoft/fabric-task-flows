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

### Step 1: Load Architecture

Read `_projects/[name]/prd/architecture-handoff.md` (FINAL). Extract items, ACs, waves.

### Step 2: Pre-fill Registry Data

```bash
python .github/skills/fabric-test/scripts/test-plan-prefill.py --handoff _projects/[name]/prd/architecture-handoff.md
```

Returns structured criteria mappings, validation phases, and test methods from all registries. Use this output for Steps 3–5.

### Step 3: Architecture Review

Assess and flag concerns with severity (`red` = blocks deployment, `yellow` = warning):

- **Testability:** AC specificity, coverage gaps, untestable criteria, edge cases
- **Feasibility:** Wave ordering, per-item gotchas, missing prerequisites

### Step 4: Map ACs to Test Methods

For each AC: determine test method (REST API / manual UI / dependency check), write verification command, define expected result (max 20 words), assign criticality, map to validation phase.

### Step 5: Identify CVPs + Edge Cases

CVPs = checks that, if failed, block deployment. Also document edge cases (empty lakehouse, environment publish delays, connection timeouts).

### Step 6: Produce Test Plan

Write to `_projects/[name]/prd/test-plan.md` using schema `schemas/test-plan.md`.

**Include `## Architecture Concerns` section** if any red or yellow issues found:

```yaml
concerns:
  - id: C-01
    severity: red | yellow
    category: testability | feasibility
    finding: "Description of concern (max 20 words)"
    recommendation: "Suggested fix (max 20 words)"
```

Set `review_outcome` in frontmatter:
- `approved` — No red concerns, safe to proceed
- `concerns` — Has red concerns, user should review before sign-off

---

## Mode 2: Post-Deployment Validation (Phase 3)

> **Deployment is deterministic.** If `fabric-cicd` succeeded, items exist. Phase 3 only validates manual configuration and runs smoke tests.

### Step 1: Generate Config Checklist

Run `validate-items.py` to generate the manual configuration checklist:

```bash
python .github/skills/fabric-test/scripts/validate-items.py _projects/[name]/prd/deployment-handoff.md
```

### Step 2: Verify Manual Configuration

For each item in `config_checklist`:
1. Open item in Fabric Portal
2. Complete the `action` step (e.g., "Create tables, configure security")
3. Mark `confirmed: true`

### Step 3: Run Smoke Tests

Verify data actually flows:
- **Query test**: Run a simple query against the Semantic Model / Lakehouse
- **Pipeline test**: Trigger a test run of the data pipeline
- **Report test**: Open the Report and verify visuals render

### Step 4: Produce Validation Report

Update `_projects/[name]/prd/validation-report.md`:
- Set `status: passed` when all config steps confirmed and smoke tests pass
- Set `status: failed` if any critical step cannot be completed

---

## Constraints

- Do NOT read registry JSON files directly — use `test-plan-prefill.py` and `validate-items.py` (registry files total 170+ KB of raw JSON)
- Every AC must have a test method — no gaps
- Test methods: max 20 words
- Never modify Fabric items — validate only
- Never invent ACs not in the Architecture Handoff
- Trust deployment success — don't re-verify item existence

Mode 1: After test plan → Phase 2b (User Sign-Off).
Mode 2: If PASSED → Phase 4 (Document). If PARTIAL/FAILED → remediation loop (max 3).
