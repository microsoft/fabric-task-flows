# Workflow Guide

> The Fabric pipeline runs as a continuous flow. You start by mentioning `@fabric-advisor`, which routes to `/fabric-discover` to collect the project name, problem statement, and the 4 V's (Volume, Velocity, Variety, Versatility). From there the pipeline chains automatically through Design → Test Plan → Sign-Off → Deploy → Validate → Document. Two moments require you: **Phase 2b Sign-Off** (approve the architecture or request revisions, max 3 cycles) and the immediately-following **deploy-mode choice** (deploy live to a Fabric workspace, or generate artifacts only). Everything else advances via `run-pipeline.py advance && next`.

## Overview

```
@fabric-advisor ──► /fabric-discover ──► /fabric-design ──► /fabric-test (Test Plan)
                                                                          │
                                                                     YOU (Sign-Off)
                                                                          │
                                                                YOU (live or artifacts-only?)
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

If the shell is unavailable mid-session, agents enter a **read-only degraded mode**: they may inspect `pipeline-state.json` and project `docs/` files to report status to the user, but they MUST NOT write to `pipeline-state.json` — the top-of-file rule against direct state edits applies without exception. Any phase transition that would normally run through `advance` must be deferred until the shell returns; escalate to the user if forward progress is blocked.

**Recovery:** Note the blocked transition in `STATUS.md` (if present) and instruct the next agent to run `reconcile --project [name]` once the shell is back, so state is rebuilt from file evidence rather than hand-edited.

---

## Phase Summary

See `@fabric-advisor` agent instructions for the phase-to-skill mapping. Key outputs per phase:

| Phase | Produces | Key Detail |
|-------|----------|------------|
| 0a Discovery | `docs/discovery-brief.md` | Infers signals, suggests task flow candidates. Before the brief is written, the skill renders a deterministic 4 V's + signals + candidate task-flows recap via `run-pipeline.py discovery-summary --project <p>` (reads `.signal-mapper-cache.json` + `.discovery-intake.json`) so the user confirms inputs, not prose. |
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
| 3 | 2a — Test Plan (plan produced) | 2b — Sign-Off | Test Plan saved to `docs/test-plan.md` | 🟢 `advance && next` (auto-advances into the 2b holding state) |
| 3a | 2b — Sign-Off (holding) | 2c — Deploy | User runs `advance --approve --deploy-mode {live,artifacts_only}` | 🛑 **HUMAN GATE + DEPLOY MODE** — `--approve` required; default is `artifacts_only` if flag omitted |
| 3b | 2b — Sign-Off (`revise`) | 1 — Design (revise) | User runs `advance --revise --feedback "..."` | 🔄 Iterative (max 3 cycles, then must approve) |
| 4 | 2c — Deploy (deployment complete) | 3 — Validate | Deployment Handoff saved to `docs/deployment-handoff.md` | 🟢 `advance && next` |
| 4a | 3 — Validate (issues found) | 2c — Remediate | Remediation log created with `routed_to: engineer` issues | 🔄 Iterative (max 3 cycles, then escalate) |
| 4b | 3 — Validate (design issues) | ESCALATE | `category: design` issues in remediation log | 🛑 **ESCALATION GATE** — human/architect intervention |
| 5 | 3 — Validate (PASSED) | 4 — Document | Validation Report saved with `status: passed` | 🟢 `advance && next` |
| 6 | 4 — Document (docs produced) | Complete | Project brief saved | 🟢 `advance` (final) |

> **Note:** `2b-sign-off` is itself a holding state, not a transition. The pipeline auto-advances *into* 2b after the test plan is produced; the human gate is the transition *out* of 2b (row 3a), which requires `advance --approve` (or `--revise`).

### Deployment Mode

The deploy mode is selected at the 2b sign-off gate via the `--deploy-mode` flag on `advance --approve`. Default (no flag) is `artifacts_only`. This sets `deploy_mode` in `pipeline-state.json` (via the runner — never by direct file edit) and controls Phase 2c/3/4 behavior:

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
| /fabric-test (validate) | `docs/deployment-handoff.md` + manual validation checklist (via `validate-items.py`) | `_projects/[name]/docs/validation-report.md` + `docs/remediation-log.md` | YAML schema |
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

---

## Handoff

Every skill ends its work the same way: after writing its output file to `_projects/[name]/docs/`, the skill invokes the pipeline runner to advance the phase and surface the next step.

```bash
python _shared/scripts/run-pipeline.py advance --project <project-name> -q
```

Interpret the runner's output:

- `🟢 AUTO-CHAIN → <skill>` — the next skill was printed; invoke it immediately. Do NOT stop and ask the user.
- `🛑 HUMAN GATE` — Phase 2b sign-off (the only human gate in the pipeline outside the deploy-mode choice). Present the sign-off to the user and wait for `--approve` or `--revise --feedback "..."`.

Skills never write to `pipeline-state.json` and never call the next skill directly — the runner is the sole orchestrator. If `advance` exits non-zero, stop and escalate to the user.
