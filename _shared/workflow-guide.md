# Workflow Guide

> The Fabric agent pipeline runs as a continuous flow. You start by mentioning `@fabric-advisor` — everything else chains automatically. Your only required intervention is **Phase 2b: Sign-Off**, where you approve the architecture before deployment begins.

## Overview

```
@fabric-advisor ──► @fabric-architect ──► Design Review ──► Test Plan
                                                                │
                                                           YOU (Sign-Off)
                                                                │
                                                           Deploy ──► Validate ──► Document
```

---

## Pipeline Runner (Required)

> ⚠️ **All pipeline orchestration MUST go through `run-pipeline.py`.** Do not call `new-project.py` directly, manually chain agents via `AUTO-CHAIN`, or edit `pipeline-state.json` by hand. Bypassing the runner leaves pipeline state stale, skips pre-compute scripts, and breaks phase verification. See `_shared/agent-boundaries.md` rule #1.

Use the pipeline runner script to manage the full lifecycle. It scaffolds the project, tracks phase state, runs pre-compute scripts, and generates agent prompts — stopping only at Phase 2b for your approval.

```bash
# Start a new pipeline
python scripts/run-pipeline.py start "Your Project Name" --problem "describe your problem"

# Check pipeline status
python scripts/run-pipeline.py status --project your-project-name

# Get the next agent prompt (after each phase completes)
python scripts/run-pipeline.py next --project your-project-name

# Mark current phase complete and advance
python scripts/run-pipeline.py advance --project your-project-name

# Reset a phase (for re-runs after fixes)
python scripts/run-pipeline.py reset --project your-project-name --phase 1b-review
```

The runner creates a `pipeline-state.json` file in each project directory that tracks which phases are complete, which agent to invoke next, and whether the transition is automatic or requires human approval.

### State Ownership

**`pipeline-state.json` is managed exclusively by `run-pipeline.py`.** Agents must never write to this file — they write their output to `prd/` files only. The runner verifies output files exist before advancing phases and extracts metadata (e.g., `task_flow`) from agent output automatically.

This prevents dual-writer conflicts where an agent and the runner both try to update phase status, causing phases to be skipped.

### Gate Enforcement

The `advance` command enforces human gates defined in `pipeline-state.json` transitions. When a transition has `auto: false` (e.g., the 2a→2b sign-off boundary), `advance` blocks and prompts for explicit approval:

```bash
# This will be blocked at the sign-off gate:
python scripts/run-pipeline.py advance --project my-project
# 🛑  Cannot advance — Phase '2a-test-plan' is a human gate.

# Explicitly approve after reviewing architecture + test plan:
python scripts/run-pipeline.py advance --project my-project --approve
```

All other transitions (`auto: true`) advance automatically without `--approve`.

### Reconcile (Heal State Drift)

If pipeline state gets out of sync (e.g., after degraded-mode operation), reconcile rebuilds state from file evidence:

```bash
python scripts/run-pipeline.py reconcile --project my-project
```

This scans `prd/` output files, detects which phases are actually complete, extracts `task_flow` if missing, and fixes `current_phase`. It's idempotent — safe to run multiple times.

You can also reconcile before advancing in one step:

```bash
python scripts/run-pipeline.py advance --project my-project --reconcile
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
2. Include in the next agent prompt: `⚠️ State was advanced in degraded mode. Run 'python scripts/run-pipeline.py reconcile --project [name]' when shell is available.`
3. Skip pre-compute scripts gracefully — proceed with LLM reasoning alone

**When shell returns:** Run `python scripts/run-pipeline.py reconcile --project [name]` to verify state consistency and heal any drift.

---

## Step 0: Check Status

Check `PROJECTS.md` for your project's current phase and next action. If your project already exists, the pipeline resumes from wherever it left off.

To start a new project, mention `@fabric-advisor` in chat with a description of your problem.

---

## New Project Setup

Before invoking any agent, scaffold the project:

```bash
python scripts/new-project.py "Your Project Name"
```

This creates:
- `projects/[name]/prd/` — 7 template files for agent handoffs (discovery-brief, architecture-handoff, engineer-review, tester-review, test-plan, deployment-handoff, validation-report)
- `projects/[name]/docs/` — README, architecture, deployment-log, and 5 ADR templates
- `projects/[name]/deployments/` — empty, for deployment scripts
- `projects/[name]/STATUS.md` — phase tracking
- `projects/[name]/pipeline-state.json` — pipeline orchestration state (for `run-pipeline.py`)
- Updates `PROJECTS.md` with a new row

**Agents edit pre-existing files — they do not create directories or boilerplate.** Each template file contains section headers, YAML frontmatter, and HTML comments marking where the agent fills in content.

---

## Phase 0a: Discovery

Mention `@fabric-advisor` and describe what you need — e.g., "We have IoT sensors streaming temperature data and need real-time alerts plus daily trend reports." The advisor asks clarifying questions, infers architectural signals (data velocity, volume, use cases), and produces a **Discovery Brief** with task flow candidates.

**Produces:** Discovery Brief → `projects/[name]/prd/discovery-brief.md`

---

## Phase 1a: Architecture Design

The architect receives the Discovery Brief and selects the best-fit task flow. It walks through each decision guide — storage format, ingestion method, processing engine, visualization layer — and produces a DRAFT Architecture Handoff with the full deployment plan, item list, and rationale for every decision.

**ADR Write-Through:** The architect also fills in the pre-scaffolded ADR files (`docs/decisions/001-task-flow.md` through `005-visualization.md`) during this phase. Decisions are documented at the moment they're made — not deferred to Phase 4. This ensures reviewers in Phase 1b can reference the full decision rationale, and the "why" behind choices is captured while context is fresh.

**Produces:** DRAFT Architecture Handoff → `projects/[name]/prd/architecture-handoff.md` + ADRs → `projects/[name]/docs/decisions/001-*.md` through `005-*.md`

---

## Phase 1b: Design Review

The DRAFT is reviewed in parallel by two agents:

- **Engineer** — checks deployment order, per-item gotchas, prerequisites, capacity, and parallel deployment potential
- **Tester** — checks acceptance criteria specificity, test coverage gaps, pre-deployment blockers, edge cases, and validation feasibility

> **Performance optimization:** Use `@fabric-reviewer` instead of invoking `@fabric-engineer` and `@fabric-tester` separately. The combined reviewer reads the architecture once and produces both reviews in a single pass, cutting review time roughly in half.

### Review Quality Gate (Iterative)

Reviews include a `review_outcome` field (`approved` | `revise`). If either review has `review_outcome: revise` (red-severity findings), the architect revises the DRAFT and the reviewer re-reviews. This cycle repeats until both reviews show `approved` or the maximum of **3 iterations** is reached.

```
Architect (DRAFT) ──► Reviewer ──► review_outcome?
                                      │
                          ┌───────────┴───────────┐
                          ▼                       ▼
                    "approved"               "revise"
                          │                       │
                          ▼                       ▼
                    Proceed to 1c      Architect revises DRAFT
                                              │
                                              ▼
                                       Re-invoke Reviewer
                                       (iteration 2, max 3)
```

**Produces:** Deployment Feasibility Review → `projects/[name]/prd/engineer-review.md` + Testability Review → `projects/[name]/prd/tester-review.md`

---

## Phase 1c: Incorporate Feedback

The architect incorporates both reviews into the FINAL handoff. A Design Review section is added documenting what changed and why. If review feedback changed any decisions, the corresponding ADR files are updated.

**Produces:** FINAL Architecture Handoff with Design Review section + updated ADRs (if decisions changed)

---

## Phase 2a: Test Plan

The tester receives the FINAL handoff and maps each acceptance criterion to a concrete validation check. It identifies critical verification points, edge cases, and any pre-deployment blockers that need resolution before deployment can begin.

**Produces:** Test Plan → `projects/[name]/prd/test-plan.md`

---

## Phase 2b: User Sign-Off

> **This is the only step where you — not an agent — make the final call.** Everything before this point is preparation. Everything after it creates real Fabric items in your workspace.

### Why This Matters

The agents have done the analysis: the architect designed the architecture with input from the engineer and tester, and the tester produced a test plan with acceptance criteria. But before anything is deployed, you should review both documents to make sure they match your expectations.

This is your chance to catch misunderstandings, adjust scope, or ask questions — **before** resources are created.

### What You're Reviewing

```
┌─────────────────────────────────┐     ┌─────────────────────────────────┐
│   FINAL Architecture Handoff    │     │          Test Plan              │
│                                 │     │                                 │
│  • Architecture diagram         │     │  • Acceptance criteria mapped   │
│  • Task flow selected           │     │  • Critical verification points │
│  • Decisions + rationale        │     │  • Edge cases identified        │
│  • Items to deploy              │     │  • Pre-deployment blockers      │
│  • Deployment order             │     │                                 │
│  • Alternatives considered      │     │                                 │
│                                 │     │                                 │
│  projects/[name]/prd/            │     │  projects/[name]/prd/            │
│  architecture-handoff.md        │     │  test-plan.md                   │
└─────────────────────────────────┘     └─────────────────────────────────┘
                         │                         │
                         └────────┬────────────────┘
                                  ▼
                        ✅ Your Approval
                                  │
                                  ▼
                         Phase 2c: Deploy
```

### Review Checklist

Walk through these before giving the go-ahead:

- **Review the auto-generated architecture diagram** — The pipeline runner automatically generates a validated ASCII diagram from the handoff's items/waves YAML via `scripts/diagram-gen.py`. This diagram is included in the sign-off prompt. It uses proper box-drawing characters with validated borders (no broken boxes). The diagram groups items by deployment wave so you can see what gets created in what order.
- **Does the architecture diagram clearly show how data flows from your sources to your outputs?** — The diagram should use your actual item names and make the end-to-end pipeline easy to follow
- **Does the task flow match your problem?** — Re-read the problem statement and make sure the selected pattern still feels right
- **Are the items what you expected?** — Check the deployment list for anything surprising or missing
- **Do the decisions make sense for your team?** — Storage, ingestion, processing, and visualization choices should align with your team's skills and preferences
- **Are acceptance criteria clear enough?** — You'll validate against these after deployment, so make sure they describe success in terms you understand
- **Any blockers to resolve first?** — The test plan may flag pre-deployment blockers (credentials, data sources, capacity) that need your action

### When You're Ready

Say "approved" or "go ahead and deploy" to continue the pipeline. If something doesn't look right, raise your concerns — the architect or tester will revise before the pipeline continues.

---

## Phase 2c: Deploy

After your approval, the engineer deploys all Fabric items following the FINAL handoff's deployment order. Items are deployed by dependency wave — independent items go in parallel, dependent items wait for their prerequisites. The engineer reviews the test plan before deploying so it knows which verification points matter.

**Produces:** Deployment Handoff → `projects/[name]/prd/deployment-handoff.md` with items created, manual steps required, and known issues

### Design-Only Mode (Local Script Generation)

When the user selects **design-only** during architecture (instead of providing a workspace or requesting workspace creation), Phase 2c produces deploy scripts instead of deploying directly:

1. **Architect** sets `deployment-mode: design-only` in the Architecture Handoff
2. **Tester** produces the Test Plan as normal (validation criteria don't change)
3. **User** signs off on the architecture and test plan
4. **Engineer** generates `deploy-{project}.sh`, `deploy-{project}.ps1`, and `deploy-{project}.py` scripts in `projects/[name]/deployments/` — the Python script uses `_shared/fabric_deploy.py` (a shared `FabricDeployer` utility with idempotent item creation, retry with backoff, and branded output)
5. **User** runs the script of their choice at their convenience — all scripts prompt for workspace name at runtime (authentication, capacity, and tenant are handled by the `fab` CLI)

> **When to use design-only mode:** Teams that want architecture decisions documented and reviewed before provisioning any Fabric resources, or when deploying to a workspace managed by a separate infrastructure team.

---

## Phase 3: Validate

The tester runs through the task flow's validation checklist against the live deployment. It checks every item the engineer created, verifies acceptance criteria from the test plan, and flags anything that doesn't match expectations.

### Validate-Remediate Loop (Iterative)

When validation finds deployment or configuration issues, the pipeline enters a remediation loop instead of immediately proceeding to documentation:

```
Engineer (Deploy) ──► Tester (Validate) ──► validation status?
                          ▲                       │
                          │           ┌───────────┴───────────────┐
                          │           ▼                           ▼
                          │     "PASSED"                   "PARTIAL/FAILED"
                          │           │                           │
                          │           ▼                    categorize issues
                          │     Proceed to                        │
                          │     Phase 4                  ┌────────┴────────┐
                          │                              ▼                ▼
                          │                     deployment/config     design issues
                          │                     issues                    │
                          │                         │                     ▼
                          │                         ▼               ESCALATE (stop)
                          │                  Engineer (Remediate)
                          │                         │
                          └─────────────────────────┘
                                              (max 3 iterations)
```

Issues are tracked in `projects/[name]/prd/remediation-log.md`. The loop exits when:
- ✅ All issues resolved → proceed to Phase 4 (Document)
- 🛑 Design issues found → escalate to architect/user
- 🛑 Max 3 remediation iterations reached → escalate to user

**Produces:** Validation Report → `projects/[name]/prd/validation-report.md` (PASSED / PARTIAL / FAILED) + Remediation Log → `projects/[name]/prd/remediation-log.md` (if issues found)

---

## Phase 4: Document

The documenter gathers all handoffs — architecture, test plan, deployment log, and validation report — and synthesizes them into project documentation. It produces ADRs explaining the "why" behind each decision and a project README tying everything together.

**Produces:** README, ADRs, architecture page, deployment log → `projects/[name]/docs/`

---

## Orchestration Rules

> **These rules govern automatic phase transitions.** The orchestrating agent (or human operator) MUST follow these rules — do NOT stop and ask the user between phases unless the rule says `🛑 HUMAN GATE`.

### ⚠️ For LLM Orchestrators (Copilot CLI, GitHub Copilot Chat, etc.)

**You are the orchestrator.** When you invoke a custom agent (e.g., `@fabric-advisor`) and it completes, you MUST immediately invoke the next agent in the pipeline. Do NOT:
- Say "Want me to continue?"
- Say "Should I proceed to the next phase?"
- Present a summary and wait for user input
- Ask any variation of "ready to move on?"

The answer to all of these is always YES. Use `run-pipeline.py advance && next` to progress. **The ONLY exception is Phase 2b Sign-Off** — that requires `--approve`.

**Pattern to follow:**
1. Agent A completes → writes output to `prd/` files
2. Run `python scripts/run-pipeline.py advance --project [name]` (verifies output, advances state)
3. Run `python scripts/run-pipeline.py next --project [name]` (generates next agent prompt)
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
| 6 | 2b — Sign-Off (user approved) | 2c — Deploy | User says "approved" / "go ahead" / "deploy" | 🟢 `advance && next` |
| 7 | 2c — Deploy (deployment complete) | 3 — Validate | Deployment Handoff saved to `prd/deployment-handoff.md` | 🟢 `advance && next` |
| 7a | 3 — Validate (issues found) | 2c — Remediate | Remediation log created with `routed_to: engineer` issues | 🔄 Iterative (max 3 cycles, then escalate) |
| 7b | 3 — Validate (design issues) | ESCALATE | `category: design` issues in remediation log | 🛑 **ESCALATION GATE** — human/architect intervention |
| 8 | 3 — Validate (PASSED) | 4 — Document | Validation Report saved with `status: passed` | 🟢 `advance && next` |
| 9 | 4 — Document (docs produced) | Complete | Wiki + ADRs saved | 🟢 `advance` (final) |

**Key principle:** Only Rule #5 stops for user input. All other transitions use `run-pipeline.py advance && next`. If the orchestrator finds itself asking "should I continue?" at any transition other than Rule #5, the answer is always YES — run `advance && next` immediately.

### How to Pass Context Between Phases

Each agent reads the previous agent's output from the project folder. The orchestrator ensures files are saved before invoking the next agent:

| Agent | Reads From | Writes To | Format |
|-------|-----------|-----------|--------|
| @fabric-advisor | (user input) | `projects/[name]/prd/discovery-brief.md` | Markdown |
| @fabric-architect | `prd/discovery-brief.md` | `projects/[name]/prd/architecture-handoff.md` | Markdown + YAML data blocks |
| @fabric-engineer (review) | `prd/architecture-handoff.md` | `projects/[name]/prd/engineer-review.md` | YAML schema |
| @fabric-tester (review) | `prd/architecture-handoff.md` | `projects/[name]/prd/tester-review.md` | YAML schema |
| @fabric-architect (finalize) | `prd/engineer-review.md` + `prd/tester-review.md` | `prd/architecture-handoff.md` (updated to FINAL) | Markdown + YAML data blocks |
| @fabric-tester (test plan) | `prd/architecture-handoff.md` (FINAL) | `projects/[name]/prd/test-plan.md` | YAML schema |
| @fabric-engineer (deploy) | `prd/architecture-handoff.md` + `prd/test-plan.md` | `projects/[name]/prd/deployment-handoff.md` + `prd/phase-progress.md` | YAML schema |
| @fabric-tester (validate) | `prd/deployment-handoff.md` + `validation/[task-flow].md` | `projects/[name]/prd/validation-report.md` + `prd/remediation-log.md` | YAML schema |
| @fabric-engineer (remediate) | `prd/remediation-log.md` | `prd/remediation-log.md` (updated) + `prd/phase-progress.md` | YAML schema |
| @fabric-documenter | All 5 documents in `prd/` | `projects/[name]/docs/` | Markdown (wiki output) |

---

## Quick Reference

| Phase | What Happens | Produces |
|-------|-------------|----------|
| 0a — Discovery | Advisor analyzes your problem and infers architectural signals | Discovery Brief → `prd/discovery-brief.md` |
| 1a — Design | Architect selects task flow and makes design decisions | DRAFT handoff → `prd/architecture-handoff.md` |
| 1b — Review | Engineer + Tester review DRAFT in parallel (iterates until `approved` or max 3 cycles) | Reviews → `prd/engineer-review.md` + `prd/tester-review.md` |
| 1c — Finalize | Architect incorporates review feedback | FINAL handoff → `prd/architecture-handoff.md` (updated) |
| 2a — Test Plan | Tester maps acceptance criteria to validation checks | Test Plan → `prd/test-plan.md` |
| **2b — Sign-Off** | **🛑 You review and approve** | **Your approval** |
| 2c — Deploy | Engineer deploys items by dependency wave, tracks progress | Deployment handoff → `prd/deployment-handoff.md` + `prd/phase-progress.md` |
| 3 — Validate | Tester validates deployment; routes issues for remediation if needed (max 3 cycles) | Validation Report → `prd/validation-report.md` + `prd/remediation-log.md` |
| 4 — Document | Documenter synthesizes all handoffs into wiki + ADRs | Project docs → `docs/` |

---

## Handoff Format Reference

Agents produce handoffs in two formats:

| Format | Used By | Why |
|--------|---------|-----|
| **Markdown with YAML data blocks** | Architecture Handoff | Human-readable for the sign-off review (Phase 2b) while keeping items, ACs, and waves in structured YAML |
| **YAML schema** | Engineer Review, Tester Review, Test Plan, Deployment Handoff, Validation Report | Machine-parseable for downstream agents; compact output reduces generation time |

### Schema Files

All YAML schemas live in `_shared/schemas/`:

| Schema | Agent | Mode | Output File |
|--------|-------|------|-------------|
| `engineer-review.md` | @fabric-engineer | Review (Mode 0) | `prd/engineer-review.md` |
| `tester-review.md` | @fabric-tester | Review (Mode 0) | `prd/tester-review.md` |
| `test-plan.md` | @fabric-tester | Test Plan (Mode 1) | `prd/test-plan.md` |
| `deployment-handoff.md` | @fabric-engineer | Deploy | `prd/deployment-handoff.md` |
| `validation-report.md` | @fabric-tester | Validate (Mode 2) | `prd/validation-report.md` |
| `remediation-log.md` | @fabric-tester / @fabric-engineer | Validate → Remediate loop | `prd/remediation-log.md` |
| `phase-progress.md` | @fabric-engineer / @fabric-tester | Deploy / Validate / Remediate | `prd/phase-progress.md` |

### Output Rules

All agents follow these constraints:

- **YAML field values: max 15 words** (test methods: max 20 words)
- **No re-stating prior documents** — reference items by name, ACs by ID
- **Architecture Handoff: max 200 lines** — uses YAML data blocks for items, ACs, waves
- **Prose sections have explicit word limits** — documented in each schema file
- **The documenter is the prose agent** — it reads structured YAML and produces human-readable wiki documentation
