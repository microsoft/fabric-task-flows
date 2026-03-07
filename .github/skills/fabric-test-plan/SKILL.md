---
name: fabric-test-plan
description: >
  Creates a test plan by mapping acceptance criteria to concrete validation
  checks. Use when user says "create test plan", "map acceptance criteria",
  "prepare for validation", "what should we test", or after architecture is
  finalized (FINAL). Do NOT use for post-deployment validation (use
  fabric-validate) or architecture design (use fabric-design).
metadata:
  author: task-flows-team
  version: 1.0.0
  category: quality
  tags: [fabric, testing, test-plan, acceptance-criteria]
  pipeline-phase: 2a-test-plan
  pre-compute: [test-plan-prefill]
---

# Fabric Test Plan

Map each acceptance criterion from the FINAL Architecture Handoff to a concrete, executable validation check.

## Instructions

### Step 1: Load Architecture

Read `projects/[name]/prd/architecture-handoff.md` (FINAL). Extract:
- Items to deploy (names, types)
- Acceptance criteria (AC IDs, criterion text, type)
- Deployment waves

### Step 2: Load Validation Checklist

Read `validation/[task-flow].md` for task-flow-specific validation phases and checks.

### Step 3: Map ACs to Test Methods

For each acceptance criterion:
1. Determine test method (fab CLI command, manual UI check, or dependency check)
2. Write verification command (exact fab CLI syntax)
3. Define expected result (max 20 words)
4. Assign criticality (critical / high / medium)
5. Map to validation phase (Foundation → Environment → Ingestion → Transformation → Visualization → ML)

### Step 4: Identify Critical Verification Points

Define CVPs — checks that, if failed, block deployment:
- Real-time data arrival
- Storage accessibility
- Compute environment readiness

### Step 5: Document Edge Cases

- Empty lakehouse at deploy time
- Environment publish delays
- Connection timeout scenarios

### Step 6: Produce Test Plan

Write to `projects/[name]/prd/test-plan.md` using schema from `_shared/schemas/test-plan.md`:

```yaml
task_flow: "[task-flow-id]"
total_acceptance_criteria: N

acceptance_criteria_mapping:
  - ac_id: "AC-1"
    criterion: "[criterion text]"
    test_method: "[fab command or manual check]"
    expected_result: "[max 20 words]"
    criticality: "critical | high | medium"
```

## Constraints

- Every AC must have a test method — no gaps
- Test methods: max 20 words
- Include fab CLI commands for every verifiable item
- Never invent ACs not in the Architecture Handoff

## Pipeline Handoff

> **⚠️ ORCHESTRATION:** Use `run-pipeline.py advance && next` for phase transitions.

After producing the test plan, advance to Phase 2b (User Sign-Off — human gate).
