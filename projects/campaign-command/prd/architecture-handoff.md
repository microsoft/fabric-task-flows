---
project: campaign-command
task_flow: TBD
phase: draft
status: draft
created: 2026-03-09
last_updated: 2026-03-09
design_review:
  engineer: pending
  tester: pending
items: 0
acceptance_criteria: 0
manual_steps: 0
deployment_waves: 0
blockers:
  critical: []
  medium: []
next_phase: design-review
---

# Architecture Handoff — DRAFT

**Project:** campaign-command
**Task flow:** TBD
**Date:** 2026-03-09
**Status:** DRAFT — Awaiting design review by /fabric-deploy and /fabric-test.

---

### Problem Reference
> See: prd/discovery-brief.md
> Summary: <!-- /fabric-design: ≤20 word summary -->

---

## Architecture Diagram

<!-- /fabric-design: Draw a project-specific ASCII data flow diagram.
     - Use box-drawing characters (┌─┐│└─┘, ──►, ──▶)
     - Data sources on the left, outputs on the right
     - Label every box with the ACTUAL project item name (e.g., "call-events-lakehouse", not just "Lakehouse")
     - Show how data flows between items with arrows
     - This is NOT the generic task-flow diagram — it's this project's specific architecture
-->

```
<!-- Replace this block with your ASCII diagram -->
```

---

## Decisions

<!-- DECISION CONTEXT (from decisions/_index.md quick_decision fields):
Storage: Spark/Python → Lakehouse | T-SQL analytics → Warehouse | T-SQL transactional → SQL Database | KQL time-series → Eventhouse | NoSQL/document → Cosmos DB
Ingestion: Real-time streaming → Eventstream | Database replication (CDC) → Mirroring | Small-medium + transforms needed → Dataflow Gen2 | Small-medium + no transforms → Copy Job | Large + code-first team → Pipeline + Notebook | Large + orchestration needed → Pipeline (Copy activity) | Complex orchestration (any volume) → Pipeline
Processing: Interactive + Python/Spark → Notebook | Interactive + KQL → KQL Queryset | Interactive + visual/no-code → Dataflow Gen2 | Production Spark + CI/CD → Spark Job Definition | Production Spark + simple schedule → Notebook (via Pipeline) | Production T-SQL → Stored Procedures | Production KQL → KQL Queryset (update policies) | Production Power Query → Dataflow Gen2
Visualization: Interactive exploration + filters → Power BI Report | Pixel-perfect / printable / multi-page → Paginated Report | Goal/KPI tracking + check-ins → Metrics Scorecard | Live streaming data (sub-second) → Real-Time Dashboard | Live geospatial/location data → Real-Time Map
Parameterization: Single environment → Environment Variables (or skip) | Multi-env + Fabric Git → Variable Library | Multi-env + fabric-cicd → parameter.yml | Multi-env + fab CLI → Environment Variables or Variable Library
-->

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Storage | | |
| Ingestion | | |
| Processing | | |
| Visualization | | |
| Semantic Model Query Mode | | |

### Items to Deploy

```yaml
items:
  # /fabric-design: fill in items
  # - id: 1
  #   name: ""
  #   type: ""
  #   skillset: ""
  #   depends_on: []
  #   purpose: ""
```

### Deployment Order

```yaml
waves:
  # /fabric-design: fill in waves
  # - id: 1
  #   items: []
  # - id: 2
  #   items: []
  #   blocked_by: [1]
```

### Acceptance Criteria

```yaml
acceptance_criteria:
  # /fabric-design: fill in ACs
  # - id: AC-1
  #   type: structural
  #   criterion: ""
  #   verify: ""
  #   target: ""
```

## Alternatives Considered

| # | Decision | Option Rejected | Why Rejected |
|---|----------|-----------------|--------------|
| | | | |

## Trade-offs

| # | Trade-off | Benefit | Cost | Mitigation |
|---|-----------|---------|------|------------|
| | | | | |

## Deployment Strategy

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Workspace Approach | | |
| Environments | | |
| CI/CD Tool | | |
| Parameterization | | |
| Branching Model | | |

## References

- Project folder: projects/campaign-command/
- Diagram: diagrams/TBD.md
- Validation: validation/TBD.md

## Design Review

| Reviewer | Feedback Summary | Incorporated? | What Changed |
|----------|-----------------|---------------|--------------|
| /fabric-deploy | <!-- pending --> | | |
| /fabric-test | <!-- pending --> | | |
