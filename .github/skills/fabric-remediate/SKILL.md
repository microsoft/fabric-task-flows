---
name: fabric-remediate
description: >
  Fixes deployment and configuration issues identified during validation.
  Use when user says "fix deployment issues", "remediate", "resolve
  validation failures", or after validation finds issues routed to the
  engineer. Do NOT use for initial deployment (use fabric-deploy),
  validation (use fabric-validate), or design changes (escalate to
  fabric-design).
metadata:
  author: task-flows-team
  version: 1.0.0
  category: deployment
  tags: [fabric, remediation, fix, rollback]
  pipeline-phase: 3-validate
---

# Fabric Remediation

Fix deployment and configuration issues identified by the `fabric-validate` skill.

## Instructions

### Step 1: Load Remediation Log

Read `projects/[name]/prd/remediation-log.md`. Filter issues where `routed_to: engineer`.

### Step 2: Fix Issues

For each engineer-routable issue:
1. **Deployment issues** — re-create item with `fab mkdir`, verify with `fab exists`
2. **Configuration issues** — update settings with `fab set`, verify
3. **Transient issues** — wait appropriate interval, retry validation

### Step 3: Update Remediation Log

For each resolved issue:
```yaml
status: resolved
resolution: "[max 20 words — what was done]"
resolved_iteration: N
```

### Step 4: Escalate Design Issues

If any issue has `category: design`:
- Set `outcome: escalated`
- STOP — cannot fix architecture problems, escalate to architect

### Step 5: Trigger Re-Validation

After fixing all engineer-routable issues, set `outcome: remediated` and advance pipeline to trigger `fabric-validate` re-validation.

## Constraints

- Max 3 remediation iterations
- Never make architecture decisions — escalate `design` issues
- Only fix `deployment`, `configuration`, and `transient` issues
- Reference `_shared/rollback-protocol.md` for failure recovery

## Pipeline Handoff

> **⚠️ ORCHESTRATION:** Use `run-pipeline.py advance && next` for phase transitions.

After remediation, re-trigger `fabric-validate` for re-validation.
