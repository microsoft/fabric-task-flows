---
name: fabric-document
description: >
  Synthesizes all pipeline handoffs into wiki-style documentation with
  Architecture Decision Records (ADRs). Use when user says "generate docs",
  "create documentation", "write ADRs", "produce wiki", "document the
  project", or after validation passes. Do NOT use for deployment (use
  fabric-deploy) or architecture design (use fabric-design).
# author: task-flows-team
# version: 1.0.0
# category: documentation
# tags: [fabric, documentation, adr, wiki]
# pipeline-phase: 4-document
---

# Fabric Documentation

Synthesize all 5 pipeline handoffs into human-readable wiki documentation.

## Instructions

### Step 1: Collect Handoffs

Read all 5 handoff documents (parse YAML fields directly, not prose):

| Handoff | Source | File |
|---------|--------|------|
| Discovery Brief | @fabric-advisor | `prd/discovery-brief.md` |
| Architecture Handoff | /fabric-design | `prd/architecture-handoff.md` |
| Test Plan | /fabric-test | `prd/test-plan.md` |
| Deployment Handoff | /fabric-deploy | `prd/deployment-handoff.md` |
| Validation Report | /fabric-test | `prd/validation-report.md` |

### Step 2: Generate Wiki Pages

Write to `projects/[name]/docs/`:

1. **README.md** — Stakeholder-friendly overview
   - Problem statement (from Discovery Brief)
   - Architecture summary (from Architecture Handoff)
   - Deployment status (from Deployment Handoff)
   - Validation results (from Validation Report)

2. **architecture.md** — Architecture narrative
   - Data flow diagram
   - Item descriptions with rationale
   - Design trade-offs

3. **deployment-log.md** — Deployment consolidation
   - Wave-by-wave summary
   - Manual steps (completed vs pending)
   - Configuration rationale
   - Known issues and mitigations

### Step 3: Polish ADRs

The architect wrote initial ADR drafts during Phase 1a. Your job:
1. Review Context, Decision, Alternatives, Consequences sections
2. Polish language for non-technical stakeholders
3. Add cross-links between ADRs and decision guides (`decisions/` directory)
4. Ensure "Alternatives Considered" is complete
5. Write any missing ADRs from the Architecture Handoff
6. Include `006-cicd.md` only for multi-environment projects

Use template from `references/adr-template.md`.

## Constraints

- Never re-state handoff content — use markdown links and YAML field references
- Use `references/documentation-templates.md` for wiki structure
- Never deploy or modify Fabric items
- Documents only — no architecture decisions

## Pipeline Handoff

> **⚠️ ORCHESTRATION:** Use `run-pipeline.py advance && next` for phase transitions.

After documentation is complete, the pipeline is finished. Update PROJECTS.md status to "Documented ✅".
