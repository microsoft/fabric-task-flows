---
name: fabric-review
description: >
  Reviews a DRAFT architecture for both deployment feasibility and testability
  in a single pass. Produces engineer and tester review files. Use when user
  says "review architecture", "check feasibility", "review DRAFT", "is this
  deployable", or after a DRAFT Architecture Handoff is produced. Do NOT use
  for initial design (use fabric-design) or validation (use fabric-validate).
metadata:
  author: task-flows-team
  version: 1.0.0
  category: quality
  tags: [fabric, review, feasibility, testability]
  pipeline-phase: 1b-review
  pre-compute: [review-prescan]
---

# Fabric Architecture Review

Perform BOTH deployment feasibility (engineer perspective) AND testability (tester perspective) review in a single pass. Read everything once, produce both reviews.

## Instructions

### Step 1: Load Context (Read Each File ONCE)

1. `projects/[name]/prd/architecture-handoff.md` — the DRAFT architecture
2. `diagrams/[task-flow].md` — skip to `## Deployment Order` for structured data
3. `_shared/fabric-cli-commands.md` — CLI verification reference
4. `validation/[task-flow].md` — task-flow-specific validation checklist

### Step 2: Engineer Review (Deployment Feasibility)

Assess:
- **Dependency graph** — does the wave order make sense?
- **Per-item gotchas** — manual steps, portal-only items, CLI gaps
- **Wave optimization** — can waves be merged or parallelized?
- **Prerequisites** — capacity, connections, credentials accounted for?
- **CLI commands** — do fab commands match the reference?

### Step 3: Tester Review (Testability)

Assess:
- **AC specificity** — is each AC measurable with clear pass/fail?
- **Test coverage** — does every item have at least one AC?
- **Untestable criteria** — any ACs that can't be verified?
- **Edge cases** — empty data at deploy, Environment publish delays, connection dependencies
- **CLI syntax** — correct fab command format in verify commands?

### Step 4: Write Both Reviews

Edit pre-scaffolded files using YAML schemas:

1. **Engineer Review** → `projects/[name]/prd/engineer-review.md`
   - Schema: `_shared/schemas/engineer-review.md`
2. **Tester Review** → `projects/[name]/prd/tester-review.md`
   - Schema: `_shared/schemas/tester-review.md`

Set `review_outcome`:
- ANY `severity: red` → `review_outcome: revise`
- NO red findings → `review_outcome: approved`

## Constraints

- No essays — every YAML field max 15 words
- No re-stating architecture — reference items by name, ACs by ID
- Write directly to files — do NOT return content as chat output
- Never make architecture decisions — review only
- Read each reference file ONCE — efficiency over completeness

## Pipeline Handoff

> **⚠️ ORCHESTRATION:** Use `run-pipeline.py advance && next` for phase transitions.

If both reviews approved → architect produces FINAL (Phase 1c).
If either review has revise → architect revises DRAFT, then re-review.
