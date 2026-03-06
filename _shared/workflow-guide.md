# Workflow Guide

> Step-by-step guide for orchestrating the Fabric agent pipeline. Copy-paste the prompts below to invoke each phase.

## Overview

```
Phase 1 — Design:     @fabric-architect (DRAFT → Review → FINAL)
Phase 2 — Plan+Deploy: @fabric-tester (Test Plan) + @fabric-engineer (Deploy)
Phase 3 — Validate:    @fabric-tester (Validate)
Phase 4 — Document:    @fabric-documenter (ADRs + wiki)
```

---

## Phase 1a: Architecture Design

**Invoke:** `@fabric-architect`

**Prompt:**
```
@fabric-architect I need to design a Fabric project.

- Project name: [your project name]
- Data pattern: [batch / real-time / both]
- Team skills: [T-SQL / Python/PySpark / Spark/Scala / Mixed]
- Use case: [analytics / ML / transactional / sensitive data]
- Workspace: [existing workspace name/ID, or "create new"]
```

**Output:** DRAFT Architecture Handoff saved to `projects/[name]/deployments/handoff.md`

---

## Phase 1b: Design Review (Parallel)

Send the DRAFT to both reviewers simultaneously:

**Invoke:** `@fabric-engineer`

**Prompt:**
```
@fabric-engineer Review this DRAFT architecture for deployment feasibility. The handoff is at projects/[name]/deployments/handoff.md

Check: deployment order, per-item gotchas, prerequisites, capacity, parallel deployment potential.
```

**Invoke:** `@fabric-tester`

**Prompt:**
```
@fabric-tester Review this DRAFT architecture for testability (Mode 0). The handoff is at projects/[name]/deployments/handoff.md

Check: acceptance criteria specificity, missing test coverage, pre-deployment blockers, edge cases, validation feasibility.
```

**Output:** Deployment Feasibility Review + Testability Review

---

## Phase 1c: Incorporate Feedback

**Invoke:** `@fabric-architect`

**Prompt:**
```
@fabric-architect Incorporate the Design Review feedback into the FINAL handoff for [project name].

Engineer review: [paste or reference]
Tester review: [paste or reference]

Update the handoff with a Design Review section documenting what changed.
```

**Output:** FINAL Architecture Handoff with Design Review section

---

## Phase 2a: Test Plan

**Invoke:** `@fabric-tester`

**Prompt:**
```
@fabric-tester Produce a Test Plan (Mode 1) for [project name]. The FINAL architecture handoff is at projects/[name]/deployments/handoff.md

Map acceptance criteria to validation checks, identify critical verification points, edge cases, and pre-deployment blockers.
```

**Output:** Test Plan saved to `projects/[name]/docs/test-plan.md`

---

## Phase 2b: Deploy (can start after Test Plan exists)

**Invoke:** `@fabric-engineer`

**Prompt:**
```
@fabric-engineer Deploy [project name] following the FINAL architecture handoff at projects/[name]/deployments/handoff.md

Review the test plan at projects/[name]/docs/test-plan.md before deploying. Deploy by dependency wave.
```

**Output:** Deployment Handoff with items created, manual steps, known issues

---

## Phase 3: Validate

**Invoke:** `@fabric-tester`

**Prompt:**
```
@fabric-tester Validate the deployment of [project name] (Mode 2).

Architecture handoff: projects/[name]/deployments/handoff.md
Test plan: projects/[name]/docs/test-plan.md
Deployment handoff: [reference engineer's output]

Run through the validation checklist for [task-flow-id].
```

**Output:** Validation Report (PASSED / PARTIAL / FAILED)

---

## Phase 4: Document

**Invoke:** `@fabric-documenter`

**Prompt:**
```
@fabric-documenter Generate wiki documentation for [project name].

Gather all handoffs:
- Architecture: projects/[name]/deployments/handoff.md
- Test Plan: projects/[name]/docs/test-plan.md
- Deployment: [reference engineer's output]
- Validation: [reference tester's output]

Create ADRs and project documentation in projects/[name]/docs/
```

**Output:** README, ADRs, architecture page, deployment log in `projects/[name]/docs/`

---

## Quick Reference

| Phase | Agent | Mode | Input | Output |
|-------|-------|------|-------|--------|
| 1a | @fabric-architect | — | User requirements | DRAFT handoff |
| 1b | @fabric-engineer | Review | DRAFT handoff | Feasibility review |
| 1b | @fabric-tester | Mode 0 | DRAFT handoff | Testability review |
| 1c | @fabric-architect | — | Reviews | FINAL handoff |
| 2a | @fabric-tester | Mode 1 | FINAL handoff | Test Plan |
| 2b | @fabric-engineer | Deploy | FINAL handoff + Test Plan | Deployment handoff |
| 3 | @fabric-tester | Mode 2 | All handoffs | Validation Report |
| 4 | @fabric-documenter | — | All handoffs | Wiki + ADRs |
