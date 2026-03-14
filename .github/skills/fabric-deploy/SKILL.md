---
name: fabric-deploy
description: >
  The Engineer skill — deploys Fabric items in dependency-ordered waves and
  remediates issues found during validation. Use when user says "deploy",
  "create items", "run deployment", "fix deployment issues",
  "remediate", or after user sign-off is complete. Do NOT use for design
  (use fabric-design) or testing (use fabric-test).
pre-compute: [deploy-script-gen]
---

# Fabric Deployment

> **⚡ Fast-forward:** After sign-off approval, `run-pipeline.py advance --approve` auto-generates all deployment artifacts deterministically: workspace/ with .platform files, config.yml, deploy script, taskflow JSON, phase-progress.md, and deployment-handoff.md. The files below are **pre-generated** — review and execute, don't rewrite.

## Instructions

### Step 1: Verify Pre-Generated Artifacts

After sign-off approval, the pipeline fast-forward generates these files automatically:

| File | Location | What It Contains |
|------|----------|-----------------|
| `.platform` files | `deploy/workspace/` | All Fabric item definitions |
| `config.yml` | `deploy/` | fabric-cicd scope with all item types |
| `deploy-*.py` | `deploy/` | Standalone Python deploy script |
| `taskflow-*.json` | `deploy/` | Fabric Portal task flow import |
| `phase-progress.md` | `docs/` | Wave-by-wave progress tracking |
| `deployment-handoff.md` | `docs/` | Deployment status YAML |

**Verify** these files exist and look correct. If any are missing, run:
```bash
python .github/skills/fabric-deploy/scripts/deploy-script-gen.py --handoff _projects/[name]/docs/architecture-summary.json --project [name] --output-dir _projects/[name]/deployments
```

### Step 2: Execute Deployment

Run the pre-generated deploy script:

```bash
cd _projects/[name]/deployments
python deploy-[name].py
```

The script handles: workspace creation, capacity assignment, fabric-cicd deployment, and Variable Library population — all interactively.

### Step 3: Handle Manual Steps

For portal-only items (Real-Time Dashboard, Activator/Reflex, Mirrored Database):
1. Document as manual step with guided portal instructions
2. Track as `manual_steps` with `status: pending | completed`

### Step 4: Update Handoff (if deviations)

If deployment matched the architecture exactly, **no updates needed** — the pre-generated `deployment-handoff.md` is already correct.

If there were deviations, failures, or manual steps, update `deployment-handoff.md`:
- Set `status: failed` or `status: skipped` for affected items
- Add `notes` with error context (max 15 words)
- Update `manual_steps` section
- Add **Implementation Notes** (max 150 words) — deviations only
- Update **Configuration Rationale** table

## Constraints

- Do NOT read registry JSON files directly — use `deploy-script-gen.py`, `deployment_loader`, and `registry_loader` Python tools (registry files total 170+ KB of raw JSON)
- Never make architecture decisions — follow the handoff exactly
- Never proceed to next wave if current wave has failures
- Implementation Notes and Configuration Rationale are MANDATORY (even if "No deviations.")

## Mode 2: Remediation (Phase 3+)

Fix deployment and configuration issues identified during validation.

### Step 1: Load Remediation Log

Read `_projects/[name]/docs/remediation-log.md`. Filter issues where `routed_to: engineer`.

### Step 2: Fix Issues

- **Deployment issues** — re-deploy item via `fabric-cicd`, verify with `validate-items.py`
- **Configuration issues** — update settings via Fabric REST API or portal, re-run validation
- **Transient issues** — wait appropriate interval, retry validation

### Step 3: Update Remediation Log

Set `status: resolved`, fill `resolution` (max 20 words), record `resolved_iteration`.

### Step 4: Escalate Design Issues

If `category: design` → set `outcome: escalated`, STOP. Cannot fix architecture — escalate.

### Step 5: Trigger Re-Validation

Set `outcome: remediated` and advance pipeline to re-trigger QA validation.

Max 3 remediation iterations.

## Handoff

After producing the output file, advance:
```bash
python _shared/scripts/run-pipeline.py advance --project <project-name> -q
```

If the output shows `🟢 AUTO-CHAIN → <skill>`, **invoke that skill immediately** — do NOT stop and ask the user.
Only `🛑 HUMAN GATE` (Phase 2b sign-off) requires user action.
