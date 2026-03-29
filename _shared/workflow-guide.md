# Workflow Guide

> The Fabric pipeline runs as a continuous flow. You start by mentioning `@fabric-advisor` — everything else chains automatically via skills. Your only required intervention is **Phase 2b: Sign-Off**, where you approve the architecture before deployment begins.

## Overview

```
@fabric-advisor ──► /fabric-design ──► /fabric-test (Test Plan)
                                                       │
                                                  YOU (Sign-Off)
                                                       │
                                                  /fabric-deploy ──► /fabric-test (Validate) ──► /fabric-document
```

---

## Pipeline Runner (Required)

> ⚠️ **All pipeline orchestration MUST go through `run-pipeline.py`.** Do not call scripts directly, chain agents manually, or edit `pipeline-state.json` by hand.

See `@fabric-advisor` agent instructions for pipeline runner commands (`start`, `status`, `next`, `advance`, `reset`).

### State Ownership

**`pipeline-state.json` is managed exclusively by `run-pipeline.py`.** Agents must never write to this file — they write their output to `docs/` files only. The runner verifies output files exist before advancing phases and extracts metadata (e.g., `task_flow`) from agent output automatically.

This prevents dual-writer conflicts where an agent and the runner both try to update phase status, causing phases to be skipped.

### Gate Enforcement

The `advance` command enforces human gates defined in `pipeline-state.json` transitions. When a transition has `auto: false` (e.g., the 2a→2b sign-off boundary), `advance` blocks and prompts for explicit approval:

```bash
# This will be blocked at the sign-off gate:
python _shared/scripts/run-pipeline.py advance --project my-project
# 🛑  Cannot advance — Phase '2a-test-plan' is a human gate.

# Explicitly approve after reviewing architecture + test plan:
python _shared/scripts/run-pipeline.py advance --project my-project --approve
```

All other transitions (`auto: true`) advance automatically without `--approve`.

### Reconcile (Heal State Drift)

If pipeline state gets out of sync (e.g., after degraded-mode operation), reconcile rebuilds state from file evidence:

```bash
python _shared/scripts/run-pipeline.py reconcile --project my-project
```

This scans `docs/` output files, detects which phases are actually complete, extracts `task_flow` if missing, and fixes `current_phase`. It's idempotent — safe to run multiple times.

You can also reconcile before advancing in one step:

```bash
python _shared/scripts/run-pipeline.py advance --project my-project --reconcile
```

### Shell Unavailable Fallback

When shell access is lost mid-session, agents may enter **degraded mode** — editing `pipeline-state.json` directly via file edit tool.

**Activation:** Shell confirmed unavailable + output file written + passes content checks (non-template, >200 bytes).

**Permitted edits** (mirrors `advance` exactly): set current phase status→`"complete"`, next phase→`"in_progress"`, update `current_phase`. After Phase 1 (Design): extract `task_flow` from handoff.

**Prohibited:** Skipping phases, bypassing human gate, modifying transition definitions.

**Recovery:** Log in STATUS.md, instruct next agent to run `reconcile --project [name]` when shell returns.

---

## Phase Summary

See `@fabric-advisor` agent instructions for the phase-to-skill mapping. Key outputs per phase:

| Phase | Produces | Key Detail |
|-------|----------|------------|
| 0a Discovery | `docs/discovery-brief.md` | Infers signals, suggests task flow candidates |
| 1 Design | `docs/architecture-handoff.md` | Architecture handoff with decisions inline (not separate ADR files) |
| 2a Test Plan | `docs/test-plan.md` | Maps each AC to validation check |
| 2b Sign-Off | — | `advance --approve` or `--revise --feedback "..."` (max 3 cycles). See [Sign-Off Guide](sign-off-guide.md) |
| 2c Deploy | `docs/deployment-handoff.md` | Live: skill-driven deployment. Artifacts-only: deterministic fast-forward (no skill invoked) |
| 3 Validate | `docs/validation-report.md` + `docs/remediation-log.md` | Live: validate→remediate loop (max 3). Artifacts-only: deterministic structural validation (no skill invoked) |
| 4 Document | `docs/project-brief.md` | Live: skill-driven synthesis. Artifacts-only: deterministic brief generation (no skill invoked) |

---

## Orchestration Rules

> **These rules govern automatic phase transitions.** The orchestrating agent (or human operator) MUST follow these rules — do NOT stop and ask the user between phases unless the rule says `🛑 HUMAN GATE`.

### Rule 0: Cold Start (No Active Project)

When a user's first message arrives and no project/phase is active:

| User Intent | Action | Gate |
|-------------|--------|------|
| Describes a data, analytics, reporting, or integration problem | Route to `/fabric-discover` to collect intake (project name + problem statement) | 🟢 Immediate |
| Asks a how-to, tutorial, or general tech question | **Decline.** Explain you're a Fabric architecture specialist and ask the user to describe their data problem instead | 🚫 Out of scope |
| Asks about an existing project | Load project state via `run-pipeline.py status` and resume at current phase | 🟢 Immediate |

> **The orchestrator must NEVER freelance answers.** If the query could plausibly be a data problem, route to `/fabric-discover` — a false-positive intake is recoverable; a skipped discovery is not.

All phase transitions are automatic via `run-pipeline.py advance && next` — the only exception is Phase 2b Sign-Off which requires `--approve`.

| # | From Phase | To Phase | Trigger | Gate |
|---|-----------|----------|---------|------|
| 1 | 0a — Discovery (Brief produced) | 1 — Design | Discovery Brief saved to `docs/discovery-brief.md` | 🟢 `advance && next` |
| 2 | 1 — Design (handoff produced) | 2a — Test Plan | Architecture handoff saved to `docs/architecture-handoff.md` | 🟢 `advance && next` |
| 3 | 2a — Test Plan (plan produced) | 2b — Sign-Off | Test Plan saved to `docs/test-plan.md` | 🛑 **HUMAN GATE** — `advance --approve` required |
| 3a | 2b — Sign-Off (`revise`) | 1 — Design (revise) | User runs `advance --revise --feedback "..."` | 🔄 Iterative (max 3 cycles, then must approve) |
| 4 | 2b — Sign-Off (user approved) | 2c — Deploy | User runs `advance --approve`. Orchestrator asks: deploy live or artifacts only? | 🟡 **DEPLOY MODE GATE** — ask user before proceeding |
| 5 | 2c — Deploy (deployment complete) | 3 — Validate | Deployment Handoff saved to `docs/deployment-handoff.md` | 🟢 `advance && next` |
| 5a | 3 — Validate (issues found) | 2c — Remediate | Remediation log created with `routed_to: engineer` issues | 🔄 Iterative (max 3 cycles, then escalate) |
| 5b | 3 — Validate (design issues) | ESCALATE | `category: design` issues in remediation log | 🛑 **ESCALATION GATE** — human/architect intervention |
| 6 | 3 — Validate (PASSED) | 4 — Document | Validation Report saved with `status: passed` | 🟢 `advance && next` |
| 7 | 4 — Document (docs produced) | Complete | Project brief saved | 🟢 `advance` (final) |

**Key principle:** Rules #5 and #6 stop for user input. Rule #5 is the architecture sign-off (approve or revise). Rule #6 is the deployment mode choice (live or artifacts-only). All other transitions use `run-pipeline.py advance && next` — run immediately without asking.

### Deployment Mode

After sign-off approval, the orchestrator presents generated artifacts and asks the user whether to deploy live or review artifacts only. This sets `deploy_mode` in `pipeline-state.json` which controls Phase 2c/3/4 behavior:

| Mode | Phase 2c | Phase 3 | Phase 4 |
|------|----------|---------|---------|
| `live` | User runs deploy script → items created in Fabric | Validate in Portal + smoke tests | "Deployed and validated" |
| `artifacts_only` | Review artifacts → handoff with `status: planned` | Structural validation only | "Artifacts ready, deployment pending" |

#### Artifacts-Only Fast Path

When `deploy_mode` is set to `artifacts_only`, the pipeline runner executes a **deterministic fast path** that auto-generates all remaining handoffs without LLM involvement:

```
Phase 2c (Deploy):   deploy-script-gen.py → workspace/, config.yml, deploy script
                     → _generate_deployment_handoff() → deployment-handoff.md (status: planned)

Phase 3 (Validate):  _generate_validation_report() → validation-report.md (structural pass)

Phase 4 (Document):  _generate_project_brief() → project-brief.md (synthesized from all handoffs)
```

All three phases complete in a single `advance` call. The runner marks each phase complete in `pipeline-state.json` sequentially, maintaining proper state transitions even though no skill agent is invoked.

> **Why this matters:** In `artifacts_only` mode, the `/fabric-deploy`, `/fabric-test` (validate), and `/fabric-document` skills are **not invoked**. Their output files are generated deterministically by `run-pipeline.py`'s fast-forward generators. This is by design — it ensures reproducible output without LLM variability.

> **Contrast with live mode:** In `live` mode, each phase invokes the corresponding skill agent, which reads prior handoffs and produces its own output. The runner only orchestrates transitions, not content generation.

### How to Pass Context Between Phases

Each agent reads the previous agent's output from the project folder. The orchestrator ensures files are saved before invoking the next agent:

| Agent | Reads From | Writes To | Format |
|-------|-----------|-----------|--------|
| /fabric-discover | (user input) | `_projects/[name]/docs/discovery-brief.md` | Markdown |
| /fabric-design | `docs/discovery-brief.md` | `_projects/[name]/docs/architecture-handoff.md` | Markdown + YAML data blocks |
| /fabric-test (plan) | `docs/architecture-handoff.md` | `_projects/[name]/docs/test-plan.md` | YAML schema |
| /fabric-deploy | `docs/architecture-handoff.md` + `docs/test-plan.md` | `_projects/[name]/docs/deployment-handoff.md` + `docs/phase-progress.md` | YAML schema |
| /fabric-test (validate) | `docs/deployment-handoff.md` + validation checklists (via `validate-items.py`) | `_projects/[name]/docs/validation-report.md` + `docs/remediation-log.md` | YAML schema |
| /fabric-deploy (remediate) | `docs/remediation-log.md` | `docs/remediation-log.md` (updated) + `docs/phase-progress.md` | YAML schema |
| /fabric-document | All handoffs in `docs/` | `_projects/[name]/docs/project-brief.md` | Markdown (synthesized brief) |

---

## Handoff Format Reference

Agents produce handoffs in two formats:

| Format | Used By | Why |
|--------|---------|-----|
| **Markdown with YAML data blocks** | Architecture Handoff | Human-readable for the sign-off review (Phase 2b) while keeping items, ACs, and waves in structured YAML |
| **YAML schema** | Test Plan, Deployment Handoff, Validation Report | Machine-parseable for downstream agents; compact output reduces generation time |

### Schema Files

YAML schemas live in each skill's `schemas/` subdirectory:

| Schema | Location | Agent | Mode | Output File |
|--------|----------|-------|------|-------------|
| `test-plan.md` | /fabric-test | Test Plan | `docs/test-plan.md` |
| `deployment-handoff.md` | /fabric-deploy | Deploy | `docs/deployment-handoff.md` |
| `validation-report.md` | /fabric-test | Validate | `docs/validation-report.md` |
| `remediation-log.md` | /fabric-test + /fabric-deploy | Validate → Remediate loop | `docs/remediation-log.md` |
| `phase-progress.md` | /fabric-deploy + /fabric-test | Deploy / Validate / Remediate | `docs/phase-progress.md` |

### Output Rules

All agents follow these constraints:

- **YAML field values: max 15 words** (test methods: max 20 words)
- **No re-stating prior documents** — reference items by name, ACs by ID
- **Architecture Handoff: max 220 lines** — uses YAML data blocks for items, ACs, waves
- **Prose sections have explicit word limits** — documented in each schema file
- The documenter reads structured YAML and produces a single human-readable project brief
