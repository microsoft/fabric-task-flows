---
name: fabric-test
description: >
  The QA skill — creates test plans from acceptance criteria and validates
  deployments against them. Use when user says "create test plan", "validate
  deployment", "run validation", "map acceptance criteria", "check items",
  "what should we test", or after architecture is finalized or deployment
  is complete. Do NOT use for architecture design (use fabric-design) or
  deployment (use fabric-deploy).
pre-compute: [test-plan-prefill, validate-items]
# author: task-flows-team
# version: 2.0.0
# category: quality
# tags: [fabric, testing, validation, acceptance-criteria, qa]
# pipeline-phases: [2a-test-plan, 3-validate]
---

# Fabric Testing & Validation (QA Role)

Covers the full QA lifecycle: write the test plan, then validate after deployment.

## Mode 1: Test Plan (Phase 2a)

### Step 1: Load Architecture

Read `projects/[name]/prd/architecture-handoff.md` (FINAL). Extract items, acceptance criteria, deployment waves.

### Step 2: Load Validation Checklist

Read `validation/[task-flow].md` for task-flow-specific validation phases.

### Step 3: Map ACs to Test Methods

For each acceptance criterion:
1. Determine test method (fab CLI command, manual UI check, or dependency check)
2. Write verification command (exact fab CLI syntax)
3. Define expected result (max 20 words)
4. Assign criticality (critical / high / medium)
5. Map to validation phase (Foundation → Environment → Ingestion → Transformation → Visualization → ML)

### Step 4: Identify Critical Verification Points

Define CVPs — checks that, if failed, block deployment.

### Step 5: Document Edge Cases

- Empty lakehouse at deploy time
- Environment publish delays
- Connection timeout scenarios

### Step 6: Produce Test Plan

Write to `projects/[name]/prd/test-plan.md` using schema `schemas/test-plan.md`.

---

## Mode 2: Post-Deployment Validation (Phase 3)

### Step 1: Load Context

1. `projects/[name]/prd/test-plan.md` — acceptance criteria mapping
2. `projects/[name]/prd/deployment-handoff.md` — what was deployed
3. `validation/[task-flow].md` — task-flow-specific checklist
4. `projects/[name]/prd/phase-progress.md` — resume from partial
5. `_shared/learnings.md` — known timing/propagation gotchas

### Step 2: Validate by Phase

Run `validate-items.py` (REST API, no `fab` CLI dependency) or the legacy `validate-items.ps1`/`.sh` scripts:

```bash
python .github/skills/fabric-test/scripts/validate-items.py projects/[name]/prd/deployment-handoff.md
```

Execute checks in order: Foundation → Environment → Ingestion → Transformation → Visualization → ML

### Step 3: Categorize Failures

| Category | Routed To | Examples |
|----------|-----------|---------|
| deployment | engineer | Item missing, fab fails, wrong type |
| configuration | engineer | Misconfigured setting |
| transient | engineer | Timing, propagation delay (retry) |
| design | architect | Wrong architecture (STOP — escalate) |

### Step 4: Produce Validation Report

Write to `projects/[name]/prd/validation-report.md` using schema `schemas/validation-report.md`.

Required prose: Validation Context (max 100 words), Future Considerations (max 100 words).

### Step 5: Create Remediation Log (if issues)

Write `projects/[name]/prd/remediation-log.md` using schema `schemas/remediation-log.md`.

### Step 6: Record Learnings

Append operational learnings to `_shared/learnings.md`.

---

## Constraints

- Every AC must have a test method — no gaps
- Test methods: max 20 words
- Never modify Fabric items — validate only
- Never skip phases in the validation checklist
- Never invent ACs not in the Architecture Handoff
- Validation Context and Future Considerations are MANDATORY

## Pipeline Handoff

> **⚠️ ORCHESTRATION:** Use `run-pipeline.py advance && next` for phase transitions.

Mode 1: After test plan → Phase 2b (User Sign-Off).
Mode 2: If PASSED → Phase 4 (Document). If PARTIAL/FAILED → remediation loop (max 3).
