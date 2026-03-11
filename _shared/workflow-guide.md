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

```bash
python _shared/scripts/run-pipeline.py start "Project Name" --problem "description"
python _shared/scripts/run-pipeline.py status --project project-name
python _shared/scripts/run-pipeline.py next --project project-name
python _shared/scripts/run-pipeline.py advance --project project-name -q
python _shared/scripts/run-pipeline.py reset --project project-name --phase 1-design
```

The runner creates `pipeline-state.json` to track phase state, run pre-compute scripts, and generate agent prompts.

### State Ownership

**`pipeline-state.json` is managed exclusively by `run-pipeline.py`.** Agents must never write to this file — they write their output to `prd/` files only. The runner verifies output files exist before advancing phases and extracts metadata (e.g., `task_flow`) from agent output automatically.

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

This scans `prd/` output files, detects which phases are actually complete, extracts `task_flow` if missing, and fixes `current_phase`. It's idempotent — safe to run multiple times.

You can also reconcile before advancing in one step:

```bash
python _shared/scripts/run-pipeline.py advance --project my-project --reconcile
```

### Shell Unavailable Fallback

When an agent loses shell/powershell access mid-session, the pipeline would normally halt because `run-pipeline.py advance` cannot be called. To prevent this, agents may enter **degraded mode** and edit `pipeline-state.json` directly using the file edit tool.

**Activation criteria — ALL must be true:**
1. Shell/powershell tool is confirmed unavailable (not just slow or erroring)
2. The agent has already written its output file (e.g., `prd/architecture-handoff.md`)
3. The output file passes the same content checks `run-pipeline.py` would apply (non-template, >200 bytes)

**Permitted edits — these mirror `run-pipeline.py advance` exactly:**
1. Set current phase's `status` to `"complete"`
2. Set next phase's `status` to `"in_progress"`
3. Update `current_phase` to the next phase ID
4. Extract `task_flow` from `prd/architecture-handoff.md` and set it (after Phase 1a only)

**Prohibited — even in degraded mode:**
- Skipping phases (must advance one at a time)
- Bypassing the Phase 2b human gate (`"gate": "human"` transitions require user approval)
- Modifying transition definitions, display_name, or problem_statement
- Running without writing the output file first

**Agent responsibilities in degraded mode:**
1. Log in `STATUS.md`: `| [Phase] | [Date] | Degraded mode — shell unavailable, state edited directly |`
2. Include in the next agent prompt: `⚠️ State was advanced in degraded mode. Run 'python _shared/scripts/run-pipeline.py reconcile --project [name]' when shell is available.`
3. Skip pre-compute scripts gracefully — proceed with LLM reasoning alone

**When shell returns:** Run `python _shared/scripts/run-pipeline.py reconcile --project [name]` to verify state consistency and heal any drift.

---

## Phase 0a: Discovery

Mention `@fabric-advisor` and describe your problem — e.g., "We have IoT sensors streaming temperature data and need real-time alerts plus daily trend reports." The advisor asks clarifying questions, infers architectural signals (data velocity, volume, use cases), and produces a **Discovery Brief** with task flow candidates.

**Produces:** Discovery Brief → `_projects/[name]/prd/discovery-brief.md`

---

## Phase 1a: Architecture Design

The architect receives the Discovery Brief and selects the best-fit task flow. It walks through each decision guide — storage format, ingestion method, processing engine, visualization layer — and produces a DRAFT Architecture Handoff with the full deployment plan, item list, and rationale for every decision.

**ADR Write-Through:** The architect also fills in the pre-scaffolded ADR files (`docs/decisions/001-task-flow.md` through `005-visualization.md`) during this phase. Decisions are documented at the moment they're made — not deferred to Phase 4. This ensures reviewers in Phase 1b can reference the full decision rationale, and the "why" behind choices is captured while context is fresh.

**Produces:** DRAFT Architecture Handoff → `_projects/[name]/prd/architecture-handoff.md` + ADRs → `_projects/[name]/docs/decisions/001-*.md` through `005-*.md`

---

## Phase 1b: Design Review

The DRAFT is reviewed for deployment feasibility and testability by the `/fabric-design` skill. Reviews include a `review_outcome` field (`approved` | `revise`). If `revise`, the architect revises and the reviewer re-reviews (max 3 iterations — see Orchestration Rules #2a).

**Produces:** `_projects/[name]/prd/engineer-review.md` + `_projects/[name]/prd/tester-review.md`

---

## Phase 1c: Incorporate Feedback

The architect incorporates both reviews into the FINAL handoff. A Design Review section is added documenting what changed and why. If review feedback changed any decisions, the corresponding ADR files are updated.

**Produces:** FINAL Architecture Handoff with Design Review section + updated ADRs (if decisions changed)

---

## Phase 2a: Test Plan

The tester receives the FINAL handoff and maps each acceptance criterion to a concrete validation check. It identifies critical verification points, edge cases, and any pre-deployment blockers that need resolution before deployment can begin.

**Produces:** Test Plan → `_projects/[name]/prd/test-plan.md`

---

## Phase 2b: User Sign-Off

> **🛑 HUMAN GATE** — This is the only step where you make the final call before deployment begins.

Review the FINAL Architecture Handoff and Test Plan, then approve or request revisions. See **[Sign-Off Guide](sign-off-guide.md)** for the full review checklist, revision loop details, and CLI commands.

- **Approve:** `python _shared/scripts/run-pipeline.py advance --project my-project --approve`
- **Revise:** `python _shared/scripts/run-pipeline.py advance --project my-project --revise --feedback "..."`
- Maximum 3 revision cycles before you must approve or abandon.

---

## Phase 2c: Deploy

After your approval, the engineer deploys all Fabric items following the FINAL handoff's deployment order. Items are deployed by dependency wave — independent items go in parallel, dependent items wait for their prerequisites. The engineer reviews the test plan before deploying so it knows which verification points matter.

**Produces:** Deployment Handoff → `_projects/[name]/prd/deployment-handoff.md` with items created, manual steps required, and known issues

### Design-Only Mode (Local Script Generation)

When the user selects **design-only** during architecture (instead of providing a workspace or requesting workspace creation), Phase 2c produces deploy scripts instead of deploying directly:

1. **Architect** sets `deployment-mode: design-only` in the Architecture Handoff
2. **Tester** produces the Test Plan as normal (validation criteria don't change)
3. **User** signs off on the architecture and test plan
4. **Engineer** generates `deploy-{project}.sh`, `deploy-{project}.ps1`, and `deploy-{project}.py` scripts in `_projects/[name]/deployments/` — the Python script embeds the `FabricDeployer` utility inline (idempotent item creation, retry with backoff, and branded output)
5. **User** runs the script of their choice at their convenience — all scripts prompt for workspace name at runtime (authentication, capacity, and tenant are handled by the `fab` CLI)

> **When to use design-only mode:** Teams that want architecture decisions documented and reviewed before provisioning any Fabric resources, or when deploying to a workspace managed by a separate infrastructure team.

---

## Phase 3: Validate

The tester validates the live deployment against the test plan and validation checklists. Issues enter a validate-remediate loop (max 3 iterations — see Orchestration Rules #7a/#7b). Design issues are escalated.

Issues are tracked in `_projects/[name]/prd/remediation-log.md`.

**Produces:** Validation Report → `_projects/[name]/prd/validation-report.md` (PASSED / PARTIAL / FAILED) + Remediation Log (if issues found)

---

## Phase 4: Document

The documenter gathers all handoffs — architecture, test plan, deployment log, and validation report — and synthesizes them into project documentation. It produces ADRs explaining the "why" behind each decision and a project README tying everything together.

**Produces:** README, ADRs, architecture page, deployment log → `_projects/[name]/docs/`

---

## Orchestration Rules

> **These rules govern automatic phase transitions.** The orchestrating agent (or human operator) MUST follow these rules — do NOT stop and ask the user between phases unless the rule says `🛑 HUMAN GATE`.

### ⚠️ For LLM Orchestrators (Copilot CLI, GitHub Copilot Chat, etc.)

**You are the orchestrator.** When `@fabric-advisor` completes a phase, `run-pipeline.py` automatically generates the prompt for the next skill. Do NOT:
- Say "Want me to continue?"
- Say "Should I proceed to the next phase?"
- Present a summary and wait for user input
- Ask any variation of "ready to move on?"

The answer to all of these is always YES. Use `run-pipeline.py advance && next` to progress. **The ONLY exception is Phase 2b Sign-Off** — that requires `--approve`.

**Pattern to follow:**
1. Agent A completes → writes output to `prd/` files
2. Run `python _shared/scripts/run-pipeline.py advance --project [name]` (verifies output, advances state)
3. Run `python _shared/scripts/run-pipeline.py next --project [name]` (generates next agent prompt)
4. Paste prompt into chat → agent B completes → repeat
5. At Phase 2b: runner blocks — requires `advance --approve` after user reviews

| # | From Phase | To Phase | Trigger | Gate |
|---|-----------|----------|---------|------|
| 1 | 0a — Discovery (Brief produced) | 1a — Design | Discovery Brief saved to `prd/discovery-brief.md` | 🟢 `advance && next` |
| 2 | 1a — Design (DRAFT produced) | 1b — Review | DRAFT handoff saved to `prd/architecture-handoff.md` | 🟢 `advance && next` |
| 2a | 1b — Review (`revise`) | 1a — Design (revise) | `review_outcome: revise` in either review | 🔄 Iterative (max 3 cycles, then force-proceed) |
| 3 | 1b — Review (both `approved`) | 1c — Finalize | Reviews saved with `review_outcome: approved` | 🟢 `advance && next` |
| 4 | 1c — Finalize (FINAL produced) | 2a — Test Plan | FINAL handoff saved to `prd/architecture-handoff.md` | 🟢 `advance && next` |
| 5 | 2a — Test Plan (plan produced) | 2b — Sign-Off | Test Plan saved to `prd/test-plan.md` | 🛑 **HUMAN GATE** — `advance --approve` required |
| 5a | 2b — Sign-Off (`revise`) | 1c — Finalize (revise) | User runs `advance --revise --feedback "..."` | 🔄 Iterative (max 3 cycles, then must approve) |
| 6 | 2b — Sign-Off (user approved) | 2c — Deploy | User runs `advance --approve` | 🟢 `advance && next` |
| 7 | 2c — Deploy (deployment complete) | 3 — Validate | Deployment Handoff saved to `prd/deployment-handoff.md` | 🟢 `advance && next` |
| 7a | 3 — Validate (issues found) | 2c — Remediate | Remediation log created with `routed_to: engineer` issues | 🔄 Iterative (max 3 cycles, then escalate) |
| 7b | 3 — Validate (design issues) | ESCALATE | `category: design` issues in remediation log | 🛑 **ESCALATION GATE** — human/architect intervention |
| 8 | 3 — Validate (PASSED) | 4 — Document | Validation Report saved with `status: passed` | 🟢 `advance && next` |
| 9 | 4 — Document (docs produced) | Complete | Wiki + ADRs saved | 🟢 `advance` (final) |

**Key principle:** Only Rule #5 stops for user input (approve or revise). All other transitions use `run-pipeline.py advance && next`. If the orchestrator finds itself asking "should I continue?" at any transition other than Rule #5, the answer is always YES — run `advance && next` immediately.

### How to Pass Context Between Phases

Each agent reads the previous agent's output from the project folder. The orchestrator ensures files are saved before invoking the next agent:

| Agent | Reads From | Writes To | Format |
|-------|-----------|-----------|--------|
| /fabric-discover | (user input) | `_projects/[name]/prd/discovery-brief.md` | Markdown |
| /fabric-design | `prd/discovery-brief.md` | `_projects/[name]/prd/architecture-handoff.md` | Markdown + YAML data blocks |
| /fabric-design (review) | `prd/architecture-handoff.md` | `_projects/[name]/prd/engineer-review.md` | YAML schema |
| /fabric-design (review) | `prd/architecture-handoff.md` | `_projects/[name]/prd/tester-review.md` | YAML schema |
| /fabric-design (finalize) | `prd/engineer-review.md` + `prd/tester-review.md` | `prd/architecture-handoff.md` (updated to FINAL) | Markdown + YAML data blocks |
| /fabric-test (plan) | `prd/architecture-handoff.md` (FINAL) | `_projects/[name]/prd/test-plan.md` | YAML schema |
| /fabric-deploy | `prd/architecture-handoff.md` + `prd/test-plan.md` | `_projects/[name]/prd/deployment-handoff.md` + `prd/phase-progress.md` | YAML schema |
| /fabric-test (validate) | `prd/deployment-handoff.md` + validation checklists (via `validate-items.py`) | `_projects/[name]/prd/validation-report.md` + `prd/remediation-log.md` | YAML schema |
| /fabric-deploy (remediate) | `prd/remediation-log.md` | `prd/remediation-log.md` (updated) + `prd/phase-progress.md` | YAML schema |
| /fabric-document | All 5 documents in `prd/` | `_projects/[name]/docs/` | Markdown (wiki output) |

---

## Handoff Format Reference

Agents produce handoffs in two formats:

| Format | Used By | Why |
|--------|---------|-----|
| **Markdown with YAML data blocks** | Architecture Handoff | Human-readable for the sign-off review (Phase 2b) while keeping items, ACs, and waves in structured YAML |
| **YAML schema** | Engineer Review, Tester Review, Test Plan, Deployment Handoff, Validation Report | Machine-parseable for downstream agents; compact output reduces generation time |

### Schema Files

All YAML schemas live in each skill's `schemas/` subdirectory:

| Schema | Agent | Mode | Output File |
|--------|-------|------|-------------|
| `engineer-review.md` | /fabric-design | Review | `prd/engineer-review.md` |
| `tester-review.md` | /fabric-design | Review | `prd/tester-review.md` |
| `test-plan.md` | /fabric-test | Test Plan | `prd/test-plan.md` |
| `deployment-handoff.md` | /fabric-deploy | Deploy | `prd/deployment-handoff.md` |
| `validation-report.md` | /fabric-test | Validate | `prd/validation-report.md` |
| `remediation-log.md` | /fabric-test + /fabric-deploy | Validate → Remediate loop | `prd/remediation-log.md` |
| `phase-progress.md` | /fabric-deploy + /fabric-test | Deploy / Validate / Remediate | `prd/phase-progress.md` |

### Output Rules

All agents follow these constraints:

- **YAML field values: max 15 words** (test methods: max 20 words)
- **No re-stating prior documents** — reference items by name, ACs by ID
- **Architecture Handoff: max 200 lines** — uses YAML data blocks for items, ACs, waves
- **Prose sections have explicit word limits** — documented in each schema file
- **The documenter is the prose agent** — it reads structured YAML and produces human-readable wiki documentation
