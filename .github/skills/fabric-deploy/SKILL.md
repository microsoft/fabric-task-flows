---
name: fabric-deploy
description: >
  Deploys Fabric items in dependency-ordered waves using the fab CLI or
  generates deployment scripts. Use when user says "deploy", "create items",
  "fab mkdir", "run deployment", "execute architecture", "start deployment",
  or after user sign-off is complete. Do NOT use for design (use
  fabric-design), test planning (use fabric-test-plan), or validation
  (use fabric-validate).
metadata:
  author: task-flows-team
  version: 1.0.0
  category: deployment
  tags: [fabric, deployment, fab-cli, waves]
  pipeline-phase: 2c-deploy
  pre-compute: [deploy-script-gen]
---

# Fabric Deployment

Deploy Fabric items following the Architecture Handoff's deployment waves, using the `fab` CLI or generated scripts.

## Instructions

### Step 1: Verify Sign-Off

Confirm Phase 2b (User Sign-Off) is complete. Never deploy without approval.

### Step 2: Load Context

Read in this order:
1. `projects/[name]/prd/architecture-handoff.md` — items, waves, dependencies
2. `diagrams/[task-flow].md` — skip to `## Deployment Order`
3. `projects/[name]/prd/test-plan.md` — awareness of what will be validated
4. `_shared/learnings.md` — known gotchas before deploying
5. `_shared/fabric-cli-commands.md` — CLI reference

### Step 3: Deploy by Wave

For each wave (sequential across waves, parallel within):

1. **Update phase-progress.md** — set items to `in_progress`
2. **Execute deployment:**
   - **Normal mode:** Run `fab mkdir` commands directly
   - **Design-only mode:** Generate scripts (.sh, .ps1, .py) with interactive prompts
3. **Verify creation:** Run `fab exists` for each item
4. **Update phase-progress.md** — set items to `completed` or `failed`
5. **Handle failures:** If any item fails, stop wave, document in deployment handoff

### Step 4: Handle Manual Steps

For portal-only items (Real-Time Dashboard, Activator/Reflex, Mirrored Database):
1. Document as manual step with guided portal instructions
2. Add interactive confirmation prompt in deploy scripts
3. Track as `manual_steps` with `status: pending | completed`

### Step 5: Produce Deployment Handoff

Write to `projects/[name]/prd/deployment-handoff.md` using schema:

```yaml
items_deployed:
  - item_name: "item-name"
    type: "ItemType"
    status: "created | skipped | failed"
    deployment_time: "N seconds"

manual_steps:
  - step_id: "M-1"
    title: "Description"
    status: "pending | completed"
```

**Required prose sections:**
- **Implementation Notes** (max 150 words) — deviations, workarounds, timing
- **Configuration Rationale** (table) — Item | Setting | Rationale (max 10 words per cell)

## Constraints

- Never make architecture decisions — follow the handoff exactly
- Never proceed to next wave if current wave has failures
- Always generate both .sh and .ps1 scripts for design-only mode
- Implementation Notes and Configuration Rationale are MANDATORY

## Pipeline Handoff

> **⚠️ ORCHESTRATION:** Use `run-pipeline.py advance && next` for phase transitions.

After deployment, advance to Phase 3 (Validate).
