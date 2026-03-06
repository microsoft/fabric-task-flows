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

## Phase 0a: Discovery

Mention `@fabric-advisor` and describe what you need — e.g., "We have IoT sensors streaming temperature data and need real-time alerts plus daily trend reports." The advisor asks clarifying questions, infers architectural signals (data velocity, volume, use cases), and produces a **Discovery Brief** with task flow candidates.

**Produces:** Discovery Brief with inferred signals and task flow candidates

---

## Phase 1a: Architecture Design

The architect receives the Discovery Brief and selects the best-fit task flow. It walks through each decision guide — storage format, ingestion method, processing engine, visualization layer — and produces a DRAFT Architecture Handoff with the full deployment plan, item list, and rationale for every decision.

**Produces:** DRAFT Architecture Handoff → `projects/[name]/deployments/handoff.md`

---

## Phase 1b: Design Review

The DRAFT is reviewed in parallel by two agents:

- **Engineer** — checks deployment order, per-item gotchas, prerequisites, capacity, and parallel deployment potential
- **Tester** — checks acceptance criteria specificity, test coverage gaps, pre-deployment blockers, edge cases, and validation feasibility

**Produces:** Deployment Feasibility Review + Testability Review

---

## Phase 1c: Incorporate Feedback

The architect incorporates both reviews into the FINAL handoff. A Design Review section is added documenting what changed and why.

**Produces:** FINAL Architecture Handoff with Design Review section

---

## Phase 2a: Test Plan

The tester receives the FINAL handoff and maps each acceptance criterion to a concrete validation check. It identifies critical verification points, edge cases, and any pre-deployment blockers that need resolution before deployment can begin.

**Produces:** Test Plan → `projects/[name]/docs/test-plan.md`

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
│  projects/[name]/deployments/   │     │  projects/[name]/docs/          │
│  handoff.md                     │     │  test-plan.md                   │
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

**Produces:** Deployment Handoff with items created, manual steps required, and known issues

---

## Phase 3: Validate

The tester runs through the task flow's validation checklist against the live deployment. It checks every item the engineer created, verifies acceptance criteria from the test plan, and flags anything that doesn't match expectations.

**Produces:** Validation Report (PASSED / PARTIAL / FAILED)

---

## Phase 4: Document

The documenter gathers all handoffs — architecture, test plan, deployment log, and validation report — and synthesizes them into project documentation. It produces ADRs explaining the "why" behind each decision and a project README tying everything together.

**Produces:** README, ADRs, architecture page, deployment log → `projects/[name]/docs/`

---

## Orchestration Rules

> **These rules govern automatic phase transitions.** The orchestrating agent (or human operator) MUST follow these rules — do NOT stop and ask the user between phases unless the rule says `🛑 HUMAN GATE`.

| # | From Phase | To Phase | Trigger | Gate |
|---|-----------|----------|---------|------|
| 1 | 0a — Discovery (Brief produced) | 1a — Design | Discovery Brief saved to project folder | 🟢 Auto-chain |
| 2 | 1a — Design (DRAFT produced) | 1b — Review | DRAFT handoff saved to `deployments/handoff.md` | 🟢 Auto-chain (invoke engineer + tester **in parallel**) |
| 3 | 1b — Review (both reviews complete) | 1c — Finalize | Engineer AND Tester feedback received | 🟢 Auto-chain |
| 4 | 1c — Finalize (FINAL produced) | 2a — Test Plan | FINAL handoff saved to `deployments/handoff.md` | 🟢 Auto-chain |
| 5 | 2a — Test Plan (plan produced) | 2b — Sign-Off | Test Plan saved to `docs/test-plan.md` | 🛑 **HUMAN GATE** — present consolidated sign-off |
| 6 | 2b — Sign-Off (user approved) | 2c — Deploy | User says "approved" / "go ahead" / "deploy" | 🟢 Auto-chain |
| 7 | 2c — Deploy (deployment complete) | 3 — Validate | Deployment Handoff saved | 🟢 Auto-chain |
| 8 | 3 — Validate (report produced) | 4 — Document | Validation Report saved | 🟢 Auto-chain |
| 9 | 4 — Document (docs produced) | Complete | Wiki + ADRs saved | 🟢 Pipeline complete |

**Key principle:** Only Rule #5 stops for user input. All other transitions happen automatically. If the orchestrator finds itself asking "should I continue?" at any transition other than Rule #5, the answer is always YES — continue immediately.

### How to Pass Context Between Phases

Each agent reads the previous agent's output from the project folder. The orchestrator ensures files are saved before invoking the next agent:

| Agent | Reads From | Writes To |
|-------|-----------|-----------|
| @fabric-advisor | (user input) | Discovery Brief (in conversation or project folder) |
| @fabric-architect | Discovery Brief | `projects/[name]/deployments/handoff.md` |
| @fabric-engineer (review) | `deployments/handoff.md` | Review feedback (in conversation) |
| @fabric-tester (review) | `deployments/handoff.md` | Review feedback (in conversation) |
| @fabric-architect (finalize) | Review feedback | `deployments/handoff.md` (updated to FINAL) |
| @fabric-tester (test plan) | `deployments/handoff.md` (FINAL) | `projects/[name]/docs/test-plan.md` |
| @fabric-engineer (deploy) | `deployments/handoff.md` + `docs/test-plan.md` | Deployment Handoff |
| @fabric-tester (validate) | Deployment Handoff + `validation/[task-flow].md` | Validation Report |
| @fabric-documenter | All handoffs in project folder | `projects/[name]/docs/` |

---

## Quick Reference

| Phase | What Happens | Produces |
|-------|-------------|----------|
| 0a — Discovery | Advisor analyzes your problem and infers architectural signals | Discovery Brief |
| 1a — Design | Architect selects task flow and makes design decisions | DRAFT handoff |
| 1b — Review | Engineer + Tester review DRAFT in parallel | Feasibility + Testability reviews |
| 1c — Finalize | Architect incorporates review feedback | FINAL handoff |
| 2a — Test Plan | Tester maps acceptance criteria to validation checks | Test Plan |
| **2b — Sign-Off** | **🛑 You review and approve** | **Your approval** |
| 2c — Deploy | Engineer deploys items by dependency wave | Deployment handoff |
| 3 — Validate | Tester validates deployment against checklist | Validation Report |
| 4 — Document | Documenter synthesizes all handoffs into wiki + ADRs | Project docs |
