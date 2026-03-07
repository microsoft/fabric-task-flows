---
name: fabric-validate
description: >
  Validates deployed Fabric items against the test plan and task-flow-specific
  checklist. Use when user says "validate deployment", "run validation",
  "check items", "verify deployment", "test the deployment", or after
  deployment is complete. Do NOT use for test plan creation (use
  fabric-test-plan), deployment (use fabric-deploy), or remediation
  (use fabric-remediate).
metadata:
  author: task-flows-team
  version: 1.0.0
  category: quality
  tags: [fabric, validation, testing, post-deployment]
  pipeline-phase: 3-validate
  pre-compute: [validate-items]
---

# Fabric Post-Deployment Validation

Validate deployed items against the test plan, phase by phase.

## Instructions

### Step 1: Load Context

1. `projects/[name]/prd/test-plan.md` — acceptance criteria mapping
2. `projects/[name]/prd/deployment-handoff.md` — what was deployed
3. `validation/[task-flow].md` — task-flow-specific checklist
4. `projects/[name]/prd/phase-progress.md` — resume from partial if re-validating
5. `_shared/learnings.md` — known timing/propagation gotchas

### Step 2: Validate by Phase

Execute checks in order: Foundation → Environment → Ingestion → Transformation → Visualization → ML

For each phase:
1. Run `fab exists` / `fab ls` / `fab get` commands per item
2. Compare results against acceptance criteria
3. Record pass/fail per item

### Step 3: Categorize Failures

For each failure, assign:
- **Category:** deployment | configuration | transient | design
- **Severity:** red | yellow | green
- **Routed to:** engineer | tester | architect

Routing rules:
- `deployment` (item missing, fab fails, wrong type) → engineer
- `configuration` (misconfigured setting) → engineer
- `transient` (timing, propagation delay) → engineer (retry)
- `design` (wrong architecture) → architect (STOP — escalate)

### Step 4: Produce Validation Report

Write to `projects/[name]/prd/validation-report.md`:

```yaml
validation_status: "PASSED | PARTIAL | FAILED"

phases_validated:
  - phase: "Foundation"
    status: "passed | failed"
    items_checked: ["item-1", "item-2"]

issues_found:
  - issue_id: "ISSUE-1"
    severity: "red"
    category: "deployment"
    item: "item-name"
    description: "[max 20 words]"
    routed_to: "engineer"
```

**Required prose sections:**
- **Validation Context** (max 100 words)
- **Future Considerations** (max 100 words)

### Step 5: Create Remediation Log (if issues)

If issues found, write `projects/[name]/prd/remediation-log.md` with categorized issues for the `fabric-remediate` skill.

### Step 6: Record Learnings

Append operational learnings to `_shared/learnings.md`.

## Constraints

- Never modify Fabric items — validate only
- Never skip phases in the validation checklist
- Never invent acceptance criteria not in the Architecture Handoff
- Validation Context and Future Considerations are MANDATORY

## Pipeline Handoff

> **⚠️ ORCHESTRATION:** Use `run-pipeline.py advance && next` for phase transitions.

If PASSED → advance to Phase 4 (Document).
If PARTIAL/FAILED → trigger remediation loop (max 3 iterations).
