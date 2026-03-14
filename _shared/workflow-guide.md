# Workflow Guide

> The Fabric pipeline runs as a continuous flow. You start by mentioning `@fabric-advisor` — everything else chains automatically via skills. Your only required intervention is **Phase 2b: Sign-Off**, where you approve the architecture before deployment begins.

## Overview

```
@fabric-advisor ──► /fabric-design (FINAL) ──► /fabric-test (Review + Plan)
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

**Permitted edits** (mirrors `advance` exactly): set current phase status→`"complete"`, next phase→`"in_progress"`, update `current_phase`. After Phase 1a: extract `task_flow` from handoff.

**Prohibited:** Skipping phases, bypassing human gate, modifying transition definitions.

**Recovery:** Log in STATUS.md, instruct next agent to run `reconcile --project [name]` when shell returns.

---

## Phase Summary

See `@fabric-advisor` agent instructions for the phase-to-skill mapping. Key outputs per phase:

| Phase | Produces | Key Detail |
|-------|----------|------------|
| 0a Discovery | `docs/discovery-brief.md` | Infers signals, suggests task flow candidates |
| 1a Design | DRAFT `docs/architecture-handoff.md` + ADRs `docs/decisions/001-005` | ADRs written during design (not deferred to Phase 4) |
| 1b Review | `docs/engineer-review.md` + `docs/tester-review.md` | `review_outcome: approved \| revise` (max 3 iterations) |
| 1c Finalize | FINAL `docs/architecture-handoff.md` | Incorporates review feedback; updates ADRs if decisions changed |
| 2a Test Plan | `docs/test-plan.md` | Maps each AC to validation check |
| 2b Sign-Off | — | `advance --approve` or `--revise --feedback "..."` (max 3 cycles). See [Sign-Off Guide](sign-off-guide.md) |
| 2c Deploy | `docs/deployment-handoff.md` | Wave-ordered deployment. **Design-only mode:** generates deploy scripts instead |
| 3 Validate | `docs/validation-report.md` + `docs/remediation-log.md` | Validate→remediate loop (max 3). Design issues escalate |
| 4 Document | `docs/` (README, ADRs, wiki) | Synthesizes all handoffs |

---

## Orchestration Rules

> **These rules govern automatic phase transitions.** The orchestrating agent (or human operator) MUST follow these rules — do NOT stop and ask the user between phases unless the rule says `🛑 HUMAN GATE`.

All phase transitions are automatic via `run-pipeline.py advance && next` — the only exception is Phase 2b Sign-Off which requires `--approve`.

| # | From Phase | To Phase | Trigger | Gate |
|---|-----------|----------|---------|------|
| 1 | 0a — Discovery (Brief produced) | 1a — Design | Discovery Brief saved to `docs/discovery-brief.md` | 🟢 `advance && next` |
| 2 | 1a — Design (DRAFT produced) | 1b — Review | DRAFT handoff saved to `docs/architecture-handoff.md` | 🟢 `advance && next` |
| 2a | 1b — Review (`revise`) | 1a — Design (revise) | `review_outcome: revise` in either review | 🔄 Iterative (max 3 cycles, then force-proceed) |
| 3 | 1b — Review (both `approved`) | 1c — Finalize | Reviews saved with `review_outcome: approved` | 🟢 `advance && next` |
| 4 | 1c — Finalize (FINAL produced) | 2a — Test Plan | FINAL handoff saved to `docs/architecture-handoff.md` | 🟢 `advance && next` |
| 5 | 2a — Test Plan (plan produced) | 2b — Sign-Off | Test Plan saved to `docs/test-plan.md` | 🛑 **HUMAN GATE** — `advance --approve` required |
| 5a | 2b — Sign-Off (`revise`) | 1c — Finalize (revise) | User runs `advance --revise --feedback "..."` | 🔄 Iterative (max 3 cycles, then must approve) |
| 6 | 2b — Sign-Off (user approved) | 2c — Deploy | User runs `advance --approve` | 🟢 `advance && next` |
| 7 | 2c — Deploy (deployment complete) | 3 — Validate | Deployment Handoff saved to `docs/deployment-handoff.md` | 🟢 `advance && next` |
| 7a | 3 — Validate (issues found) | 2c — Remediate | Remediation log created with `routed_to: engineer` issues | 🔄 Iterative (max 3 cycles, then escalate) |
| 7b | 3 — Validate (design issues) | ESCALATE | `category: design` issues in remediation log | 🛑 **ESCALATION GATE** — human/architect intervention |
| 8 | 3 — Validate (PASSED) | 4 — Document | Validation Report saved with `status: passed` | 🟢 `advance && next` |
| 9 | 4 — Document (docs produced) | Complete | Wiki + ADRs saved | 🟢 `advance` (final) |

**Key principle:** Only Rule #5 stops for user input (approve or revise). All other transitions use `run-pipeline.py advance && next`. If the orchestrator finds itself asking "should I continue?" at any transition other than Rule #5, the answer is always YES — run `advance && next` immediately.

### How to Pass Context Between Phases

Each agent reads the previous agent's output from the project folder. The orchestrator ensures files are saved before invoking the next agent:

| Agent | Reads From | Writes To | Format |
|-------|-----------|-----------|--------|
| /fabric-discover | (user input) | `_projects/[name]/docs/discovery-brief.md` | Markdown |
| /fabric-design | `docs/discovery-brief.md` | `_projects/[name]/docs/architecture-handoff.md` | Markdown + YAML data blocks |
| /fabric-design (review) | `docs/architecture-handoff.md` | `_projects/[name]/docs/engineer-review.md` | YAML schema |
| /fabric-design (review) | `docs/architecture-handoff.md` | `_projects/[name]/docs/tester-review.md` | YAML schema |
| /fabric-design (finalize) | `docs/engineer-review.md` + `docs/tester-review.md` | `docs/architecture-handoff.md` (updated to FINAL) | Markdown + YAML data blocks |
| /fabric-test (plan) | `docs/architecture-handoff.md` (FINAL) | `_projects/[name]/docs/test-plan.md` | YAML schema |
| /fabric-deploy | `docs/architecture-handoff.md` + `docs/test-plan.md` | `_projects/[name]/docs/deployment-handoff.md` + `docs/phase-progress.md` | YAML schema |
| /fabric-test (validate) | `docs/deployment-handoff.md` + validation checklists (via `validate-items.py`) | `_projects/[name]/docs/validation-report.md` + `docs/remediation-log.md` | YAML schema |
| /fabric-deploy (remediate) | `docs/remediation-log.md` | `docs/remediation-log.md` (updated) + `docs/phase-progress.md` | YAML schema |
| /fabric-document | All 5 documents in `docs/` | `_projects/[name]/docs/` | Markdown (wiki output) |

---

## Handoff Format Reference

Agents produce handoffs in two formats:

| Format | Used By | Why |
|--------|---------|-----|
| **Markdown with YAML data blocks** | Architecture Handoff | Human-readable for the sign-off review (Phase 2b) while keeping items, ACs, and waves in structured YAML |
| **YAML schema** | Engineer Review, Tester Review, Test Plan, Deployment Handoff, Validation Report | Machine-parseable for downstream agents; compact output reduces generation time |

### Schema Files

YAML schemas live in each skill's `schemas/` subdirectory, except review schemas which live in `_shared/schemas/`:

| Schema | Location | Agent | Mode | Output File |
|--------|----------|-------|------|-------------|
| `engineer-review.md` | `_shared/schemas/` | /fabric-design | Review | `docs/engineer-review.md` |
| `tester-review.md` | `_shared/schemas/` | /fabric-design | Review | `docs/tester-review.md` |
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
- **The documenter is the prose agent** — it reads structured YAML and produces human-readable wiki documentation
