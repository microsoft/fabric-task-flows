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
- Updates `PROJECTS.md` with a new row

**Agents edit pre-existing files — they do not create directories or boilerplate.** Each template file contains section headers, YAML frontmatter, and HTML comments marking where the agent fills in content.

---

## Phase 0a: Discovery

Mention `@fabric-advisor` and describe what you need — e.g., "We have IoT sensors streaming temperature data and need real-time alerts plus daily trend reports." The advisor asks clarifying questions, infers architectural signals (data velocity, volume, use cases), and produces a **Discovery Brief** with task flow candidates.

**Produces:** Discovery Brief → `projects/[name]/prd/discovery-brief.md`

---

## Phase 1a: Architecture Design

The architect receives the Discovery Brief and selects the best-fit task flow. It walks through each decision guide — storage format, ingestion method, processing engine, visualization layer — and produces a DRAFT Architecture Handoff with the full deployment plan, item list, and rationale for every decision.

**Produces:** DRAFT Architecture Handoff → `projects/[name]/prd/architecture-handoff.md`

---

## Phase 1b: Design Review

The DRAFT is reviewed in parallel by two agents:

- **Engineer** — checks deployment order, per-item gotchas, prerequisites, capacity, and parallel deployment potential
- **Tester** — checks acceptance criteria specificity, test coverage gaps, pre-deployment blockers, edge cases, and validation feasibility

> **Performance optimization:** Use `@fabric-reviewer` instead of invoking `@fabric-engineer` and `@fabric-tester` separately. The combined reviewer reads the architecture once and produces both reviews in a single pass, cutting review time roughly in half.

**Produces:**Deployment Feasibility Review → `projects/[name]/prd/engineer-review.md` + Testability Review → `projects/[name]/prd/tester-review.md`

---

## Phase 1c: Incorporate Feedback

The architect incorporates both reviews into the FINAL handoff. A Design Review section is added documenting what changed and why.

**Produces:** FINAL Architecture Handoff with Design Review section

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
│  • Task flow selected           │     │  • Acceptance criteria mapped   │
│  • Decisions + rationale        │     │  • Critical verification points │
│  • Items to deploy              │     │  • Edge cases identified        │
│  • Deployment order             │     │  • Pre-deployment blockers      │
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
4. **Engineer** generates `deploy-{project}.sh` and `deploy-{project}.ps1` scripts in `projects/[name]/deployments/`
5. **User** runs the scripts at their convenience — the scripts prompt for capacity ID, tenant ID, workspace name, environment, and auth method at runtime

> **When to use design-only mode:** Teams that want architecture decisions documented and reviewed before provisioning any Fabric resources, or when deploying to a workspace managed by a separate infrastructure team.

---

## Phase 3: Validate

The tester runs through the task flow's validation checklist against the live deployment. It checks every item the engineer created, verifies acceptance criteria from the test plan, and flags anything that doesn't match expectations.

**Produces:** Validation Report → `projects/[name]/prd/validation-report.md` (PASSED / PARTIAL / FAILED)

---

## Phase 4: Document

The documenter gathers all handoffs — architecture, test plan, deployment log, and validation report — and synthesizes them into project documentation. It produces ADRs explaining the "why" behind each decision and a project README tying everything together.

**Produces:** README, ADRs, architecture page, deployment log → `projects/[name]/docs/`

---

## Orchestration Rules

> **These rules govern automatic phase transitions.** The orchestrating agent (or human operator) MUST follow these rules — do NOT stop and ask the user between phases unless the rule says `🛑 HUMAN GATE`.

| # | From Phase | To Phase | Trigger | Gate |
|---|-----------|----------|---------|------|
| 1 | 0a — Discovery (Brief produced) | 1a — Design | Discovery Brief saved to `prd/discovery-brief.md` | 🟢 Auto-chain |
| 2 | 1a — Design (DRAFT produced) | 1b — Review | DRAFT handoff saved to `prd/architecture-handoff.md` | 🟢 Auto-chain (invoke engineer + tester **in parallel**) |
| 3 | 1b — Review (both reviews complete) | 1c — Finalize | Reviews saved to `prd/engineer-review.md` and `prd/tester-review.md` | 🟢 Auto-chain |
| 4 | 1c — Finalize (FINAL produced) | 2a — Test Plan | FINAL handoff saved to `prd/architecture-handoff.md` | 🟢 Auto-chain |
| 5 | 2a — Test Plan (plan produced) | 2b — Sign-Off | Test Plan saved to `prd/test-plan.md` | 🛑 **HUMAN GATE** — present consolidated sign-off |
| 6 | 2b — Sign-Off (user approved) | 2c — Deploy | User says "approved" / "go ahead" / "deploy" | 🟢 Auto-chain |
| 7 | 2c — Deploy (deployment complete) | 3 — Validate | Deployment Handoff saved to `prd/deployment-handoff.md` | 🟢 Auto-chain |
| 8 | 3 — Validate (report produced) | 4 — Document | Validation Report saved to `prd/validation-report.md` | 🟢 Auto-chain |
| 9 | 4 — Document (docs produced) | Complete | Wiki + ADRs saved | 🟢 Pipeline complete |

**Key principle:** Only Rule #5 stops for user input. All other transitions happen automatically. If the orchestrator finds itself asking "should I continue?" at any transition other than Rule #5, the answer is always YES — continue immediately.

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
| @fabric-engineer (deploy) | `prd/architecture-handoff.md` + `prd/test-plan.md` | `projects/[name]/prd/deployment-handoff.md` | YAML schema |
| @fabric-tester (validate) | `prd/deployment-handoff.md` + `validation/[task-flow].md` | `projects/[name]/prd/validation-report.md` | YAML schema |
| @fabric-documenter | All 5 documents in `prd/` | `projects/[name]/docs/` | Markdown (wiki output) |

---

## Quick Reference

| Phase | What Happens | Produces |
|-------|-------------|----------|
| 0a — Discovery | Advisor analyzes your problem and infers architectural signals | Discovery Brief → `prd/discovery-brief.md` |
| 1a — Design | Architect selects task flow and makes design decisions | DRAFT handoff → `prd/architecture-handoff.md` |
| 1b — Review | Engineer + Tester review DRAFT in parallel | Reviews → `prd/engineer-review.md` + `prd/tester-review.md` |
| 1c — Finalize | Architect incorporates review feedback | FINAL handoff → `prd/architecture-handoff.md` (updated) |
| 2a — Test Plan | Tester maps acceptance criteria to validation checks | Test Plan → `prd/test-plan.md` |
| **2b — Sign-Off** | **🛑 You review and approve** | **Your approval** |
| 2c — Deploy | Engineer deploys items by dependency wave | Deployment handoff → `prd/deployment-handoff.md` |
| 3 — Validate | Tester validates deployment against checklist | Validation Report → `prd/validation-report.md` |
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

### Output Rules

All agents follow these constraints:

- **YAML field values: max 15 words** (test methods: max 20 words)
- **No re-stating prior documents** — reference items by name, ACs by ID
- **Architecture Handoff: max 200 lines** — uses YAML data blocks for items, ACs, waves
- **Prose sections have explicit word limits** — documented in each schema file
- **The documenter is the prose agent** — it reads structured YAML and produces human-readable wiki documentation
