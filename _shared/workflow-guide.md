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

## Pipeline Runner

All pipeline orchestration goes through `run-pipeline.py`. Commands: `start`, `status`, `next`, `advance`, `reset`, `reconcile`.

### State Ownership

`pipeline-state.json` is managed exclusively by `run-pipeline.py`. Agents write their output to `docs/` files only. The runner verifies output files exist before advancing phases and extracts metadata (e.g., `task_flow`) from agent output automatically.

### Gate Enforcement

The `advance` command enforces human gates defined in `pipeline-state.json` transitions. When a transition has `auto: false` (the 2a→2b sign-off boundary), `advance` blocks and prompts for explicit approval:

```bash
python _shared/scripts/run-pipeline.py advance --project my-project --approve
```

All other transitions (`auto: true`) advance automatically without `--approve`.

### Reconcile

If pipeline state gets out of sync, reconcile rebuilds state from file evidence:

```bash
python _shared/scripts/run-pipeline.py reconcile --project my-project
```

---

## Phase Summary

See `@fabric-advisor` agent instructions for the phase-to-skill mapping. Key outputs per phase:

| Phase | Produces | Key Detail |
|-------|----------|------------|
| 0a Discovery | `docs/discovery-brief.md` | Infers signals, suggests task flow candidates. Before the brief is written, the skill renders a deterministic 4 V's + signals + candidate task-flows recap via `run-pipeline.py discovery-summary --project <p>` (reads `.signal-mapper-cache.json` + `.discovery-intake.json`) so the user confirms inputs, not prose. |
| 1 Design | `docs/architecture-handoff.md` | Architecture handoff with decisions inline (not separate ADR files) |
| 2a Test Plan | `docs/test-plan.md` | Maps each AC to validation check |
| 2b Sign-Off | — | `advance --approve` or `--revise --feedback "..."` (max 3 cycles) |
| 2c Deploy | `docs/deployment-handoff.md` | Live: skill-driven deployment. Artifacts-only: deterministic fast-forward (no skill invoked) |
| 3 Validate | `docs/validation-report.md` + `docs/remediation-log.md` | Live: validate→remediate loop (max 3). Artifacts-only: deterministic structural validation (no skill invoked) |
| 4 Document | `docs/project-brief.md` | Live: skill-driven synthesis. Artifacts-only: deterministic brief generation (no skill invoked) |

---

## Orchestration Rules

### Cold Start

| User Intent | Action |
|-------------|--------|
| Describes a data problem | Route to `/fabric-discover` |
| Asks how-to / tutorial | Decline — ask for their data problem |
| Asks about existing project | Load state via `run-pipeline.py status` and resume |

### Phase Transitions

All transitions are automatic via `run-pipeline.py advance && next` except Phase 2b Sign-Off which requires `--approve`.

| # | From Phase | To Phase | Trigger | Gate |
|---|-----------|----------|---------|------|
| 1 | 0a Discovery | 1 Design | Discovery brief saved | 🟢 auto |
| 2 | 1 Design | 2a Test Plan | Architecture handoff saved | 🟢 auto |
| 3 | 2a Test Plan | 2b Sign-Off | Test plan saved | 🟢 auto |
| 3a | 2b Sign-Off | 2c Deploy | `advance --approve` | 🛑 Human gate |
| 3b | 2b Sign-Off | 1 Design (revise) | `advance --revise --feedback "..."` | 🔄 max 3 cycles |
| 4 | 2c Deploy | 3 Validate | Deployment handoff saved | 🟢 auto |
| 4a | 3 Validate (issues) | 2c Remediate | Remediation log with engineer issues | 🔄 max 3 cycles |
| 4b | 3 Validate (design issues) | ESCALATE | Design category in remediation log | 🛑 Escalation |
| 5 | 3 Validate (passed) | 4 Document | Validation report passed | 🟢 auto |
| 6 | 4 Document | Complete | Project brief saved | 🟢 auto |

### Deployment Mode

Selected at 2b sign-off via `--deploy-mode {live,artifacts_only}`. Default is `artifacts_only`.

| Mode | Phase 2c | Phase 3 | Phase 4 |
|------|----------|---------|---------|
| `live` | Deploy script → items created in Fabric | Validate + smoke tests | "Deployed and validated" |
| `artifacts_only` | Review artifacts → `status: planned` | Structural validation only | "Artifacts ready" |

#### Artifacts-Only Fast Path

When `deploy_mode` is `artifacts_only`, the runner auto-generates all remaining handoffs in a single `advance` call:

```
Phase 2c: deploy-script-gen.py → workspace/, deploy script → deployment-handoff.md (status: planned)
Phase 3:  validation-report.md (structural pass)
Phase 4:  project-brief.md (synthesized from all handoffs)
```

In `artifacts_only` mode, skills `/fabric-deploy`, `/fabric-test` (validate), and `/fabric-document` are not invoked. In `live` mode, each phase invokes its skill agent.

### Context Flow Between Phases

| Agent | Reads From | Writes To |
|-------|-----------|-----------|
| /fabric-discover | (user input) | `docs/discovery-brief.md` |
| /fabric-design | `docs/discovery-brief.md` | `docs/architecture-handoff.md` |
| /fabric-test (plan) | `docs/architecture-handoff.md` | `docs/test-plan.md` |
| /fabric-deploy | `docs/architecture-handoff.md` + `docs/test-plan.md` | `docs/deployment-handoff.md` |
| /fabric-test (validate) | `docs/deployment-handoff.md` | `docs/validation-report.md` + `docs/remediation-log.md` |
| /fabric-document | All `docs/` files | `docs/project-brief.md` |

---

## Handoff Format

| Format | Used By | Purpose |
|--------|---------|---------|
| Markdown + YAML data blocks | Architecture Handoff | Human-readable for sign-off; structured for parsing |
| YAML schema | Test Plan, Deployment, Validation | Machine-parseable for downstream agents |

Schemas live in each skill's `schemas/` subdirectory.

### Output Rules

- YAML field values: max 15 words (test methods: max 20 words)
- No re-stating prior documents — reference items by name, ACs by ID
- Architecture Handoff: max 220 lines

---

## Skill Handoff Pattern

Every skill ends by running:

```bash
python _shared/scripts/run-pipeline.py advance --project <name> -q
```

Runner output signals:
- `🟢 AUTO-CHAIN → <skill>` — invoke next skill immediately
- `🛑 HUMAN GATE` — present sign-off, wait for user
