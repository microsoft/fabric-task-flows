---
name: fabric-finalize
description: >
  Incorporates review feedback into a DRAFT architecture to produce a FINAL
  Architecture Handoff. Use when user says "finalize architecture",
  "incorporate review feedback", "update DRAFT to FINAL", or after design
  review is complete. Do NOT use for initial design (use fabric-design) or
  deployment (use fabric-deploy).
metadata:
  author: task-flows-team
  version: 1.0.0
  category: architecture
  tags: [fabric, architecture, finalization, review-feedback]
  pipeline-phase: 1c-finalize
---

# Fabric Architecture Finalization

Incorporate engineer and tester review feedback into the DRAFT Architecture Handoff to produce the FINAL version.

## Instructions

### Step 1: Read Reviews

Load both review files:
- `projects/[name]/prd/engineer-review.md` — deployment feasibility findings
- `projects/[name]/prd/tester-review.md` — testability findings

### Step 2: Assess Findings

For each finding with `severity: red`:
- Address the concern in the architecture
- Update affected items, waves, or acceptance criteria

For `severity: yellow`:
- Document acknowledgment and mitigation

### Step 3: Update Architecture Handoff

Edit `projects/[name]/prd/architecture-handoff.md`:
1. Add `## Design Review` section at the end
2. Populate review table: Finding | Severity | Action Taken
3. Update items/waves/ACs if design changed
4. Change phase from `DRAFT` to `FINAL` in frontmatter

### Step 4: Update ADRs (if decisions changed)

If review feedback caused a decision to change, update the relevant ADR file and add a "Review Impact" note.

## Constraints

- Only modify architecture based on review findings — no new design decisions
- Max 3 review iterations total (check `review_iteration` field)
- After 3 cycles, proceed to FINAL regardless and document unresolved findings

## Pipeline Handoff

> **⚠️ ORCHESTRATION:** Use `run-pipeline.py advance && next` for phase transitions.

After producing FINAL, advance to Phase 2a (Test Plan).
