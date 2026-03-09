---
project: campaign-command
task_flow: lambda
phase: draft
status: draft
created: 2026-03-09
last_updated: 2026-03-09
design_review:
  engineer: pending
  tester: pending
items: 13
acceptance_criteria: 10
manual_steps: 1
deployment_waves: 7
blockers:
  critical: []
  medium: []
next_phase: design-review
---

# Architecture Handoff — DRAFT

**Project:** Campaign Command
**Task flow:** lambda + conversational-analytics (overlay)
**Date:** 2026-03-09
**Status:** DRAFT — Awaiting design review by /fabric-deploy and /fabric-test.

---

### Problem Reference
> See: prd/discovery-brief.md
> Summary: Batch ad analytics + real-time social sentiment + exec chatbot for campaign ROI optimization.

---

## Architecture Diagram

```
  ┌─ EXTERNAL SOURCES ────────────────────────────────────────────────────────────┐
  │  Google Analytics API    AdWords API    Social Media APIs (sentiment stream)  │
  └──────┬──────────────────────┬────────────────────────┬───────────────────────┘
         │                      │                        │
         ▼                      ▼                        ▼
  ┌─ BATCH PATH ──────────────────────────┐  ┌─ SPEED PATH ──────────────────────┐
  │  ┌────────────────────┐               │  │  ┌──────────────────────┐         │
  │  │ cc-batch-pipeline  │               │  │  │ cc-social-eventstream│         │
  │  │   (Pipeline) [CF]  │               │  │  │  (Eventstream) [LC]  │         │
  │  └─────────┬──────────┘               │  │  └──────────┬───────────┘         │
  │            ▼                          │  │             ▼                     │
  │  ┌────────────────────┐               │  │  ┌──────────────────────┐         │
  │  │ cc-raw-lakehouse   │               │  │  │ cc-stream-eventhouse │         │
  │  │  (Lakehouse) [LC]  │               │  │  │  (Eventhouse) [LC]   │         │
  │  └─────────┬──────────┘               │  │  └──────────┬───────────┘         │
  │            ▼                          │  │             ▼                     │
  │  ┌────────────────────┐               │  │  ┌──────────────────────┐         │
  │  │ cc-transform-nb    │               │  │  │ cc-stream-kql        │         │
  │  │  (Notebook) [CF]   │               │  │  │ (KQL Queryset) [CF]  │         │
  │  └─────────┬──────────┘               │  │  └──────────┬───────────┘         │
  │            ▼                          │  │             ▼                     │
  │  ┌────────────────────┐               │  │  ┌──────────────────────┐         │
  │  │ cc-gold-warehouse  │               │  │  │ cc-rt-dashboard      │         │
  │  │  (Warehouse) [LC]  │               │  │  │ (RT Dashboard) [LC]  │         │
  │  └─────────┬──────────┘               │  │  └──────────────────────┘         │
  └────────────┼──────────────────────────┘  └───────────────────────────────────┘
               ▼
  ┌─ SERVING LAYER ──────────────────────────────────────────────────────────────┐
  │  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────────┐  │
  │  │ cc-campaign-sem    │─►│ cc-roi-report      │  │ cc-campaign-agent      │  │
  │  │ (Semantic Model)   │  │ (Report) [LC]      │  │ (Data Agent) [LC]      │  │
  │  │ [CF]               │  └────────────────────┘  │ (exec chatbot)         │  │
  │  └────────────────────┘                          └────────────────────────┘  │
  └──────────────────────────────────────────────────────────────────────────────┘
```

---

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Storage | Lakehouse + Warehouse + Eventhouse | Lambda: batch (LH→WH) + real-time (EH) |
| Ingestion | Pipeline (batch) + Eventstream (RT) | Code-first batch APIs + streaming social feeds |
| Processing | Notebook (batch) + KQL Queryset (RT) | Code-first Python transforms + KQL stream agg |
| Visualization | Report (batch ROI) + RT Dashboard (social) | Batch exploration + sub-second social monitoring |
| Semantic Model Query Mode | Direct Lake | Optimal for Warehouse/Lakehouse with no fallback |

### Items to Deploy

```yaml
items:
  - id: 1
    name: cc-raw-lakehouse
    type: Lakehouse
    skillset: LC
    depends_on: []
    purpose: Raw batch data from Analytics and AdWords APIs
  - id: 2
    name: cc-gold-warehouse
    type: Warehouse
    skillset: LC
    depends_on: []
    purpose: Curated gold layer for ROI reporting and regional metrics
  - id: 3
    name: cc-stream-eventhouse
    type: Eventhouse
    skillset: LC
    depends_on: []
    purpose: Real-time social sentiment and influencer content
  - id: 4
    name: cc-spark-environment
    type: Environment
    skillset: CF
    depends_on: [1]
    purpose: Spark/Python runtime for batch transform notebooks
  - id: 5
    name: cc-batch-pipeline
    type: DataPipeline
    skillset: CF
    depends_on: [1]
    purpose: Orchestrate batch ingestion from Analytics + AdWords APIs
  - id: 6
    name: cc-social-eventstream
    type: Eventstream
    skillset: LC
    depends_on: [3]
    purpose: Ingest real-time social media sentiment feeds
  - id: 7
    name: cc-transform-nb
    type: Notebook
    skillset: CF
    depends_on: [1, 4]
    purpose: Batch transforms, sentiment scoring, regional aggregation
  - id: 8
    name: cc-stream-kql
    type: KQLQueryset
    skillset: CF
    depends_on: [3]
    purpose: Real-time stream aggregations on social data
  - id: 9
    name: cc-campaign-sem
    type: SemanticModel
    skillset: CF
    depends_on: [2]
    purpose: Unified campaign model for ROI reporting + Data Agent
  - id: 10
    name: cc-rt-dashboard
    type: Dashboard
    skillset: LC
    depends_on: [3]
    purpose: Live social sentiment monitoring (sub-second)
  - id: 11
    name: cc-roi-report
    type: Report
    skillset: LC
    depends_on: [9]
    purpose: Interactive ROI and regional ad performance reports
  - id: 12
    name: cc-campaign-agent
    type: DataAgent
    skillset: LC
    depends_on: [9]
    purpose: Internal exec chatbot for self-service campaign Q&A
  - id: 13
    name: cc-alerts-activator
    type: Reflex
    skillset: LC
    depends_on: [3, 6]
    purpose: ROI threshold alerts for regional ad buy decisions
```

### Deployment Order

```yaml
waves:
  - id: 1
    name: Foundation
    items: [cc-raw-lakehouse, cc-gold-warehouse, cc-stream-eventhouse]
    parallel: true
  - id: 2
    name: Compute
    items: [cc-spark-environment]
    blocked_by: [1]
  - id: 3
    name: Ingestion
    items: [cc-batch-pipeline, cc-social-eventstream]
    blocked_by: [1]
    parallel: true
  - id: 4
    name: Transformation
    items: [cc-transform-nb, cc-stream-kql]
    blocked_by: [2, 3]
    parallel: true
  - id: 5
    name: Serving
    items: [cc-campaign-sem, cc-rt-dashboard]
    blocked_by: [1, 4]
    parallel: true
  - id: 6
    name: Consumption
    items: [cc-roi-report, cc-campaign-agent]
    blocked_by: [5]
    parallel: true
  - id: 7
    name: Monitoring
    items: [cc-alerts-activator]
    blocked_by: [3]
```

### Acceptance Criteria

```yaml
acceptance_criteria:
  - id: AC-1
    type: structural
    criterion: Three storage items exist (Lakehouse, Warehouse, Eventhouse)
    verify: REST API list items by type
    target: cc-raw-lakehouse, cc-gold-warehouse, cc-stream-eventhouse
  - id: AC-2
    type: structural
    criterion: Eventstream is created and bound to Eventhouse
    verify: REST API get Eventstream definition
    target: cc-social-eventstream
  - id: AC-3
    type: structural
    criterion: Pipeline is created with Copy activities for batch sources
    verify: REST API get Pipeline definition
    target: cc-batch-pipeline
  - id: AC-4
    type: structural
    criterion: Notebook exists with Environment attached
    verify: REST API get Notebook definition
    target: cc-transform-nb
  - id: AC-5
    type: structural
    criterion: KQL Queryset exists and references Eventhouse
    verify: REST API get KQL Queryset definition
    target: cc-stream-kql
  - id: AC-6
    type: structural
    criterion: Semantic Model exists with Direct Lake on Warehouse
    verify: REST API get Semantic Model definition
    target: cc-campaign-sem
  - id: AC-7
    type: structural
    criterion: Report exists and is bound to Semantic Model
    verify: REST API get Report definition
    target: cc-roi-report
  - id: AC-8
    type: structural
    criterion: Real-Time Dashboard exists and queries Eventhouse
    verify: REST API get Dashboard definition
    target: cc-rt-dashboard
  - id: AC-9
    type: structural
    criterion: Data Agent exists and is bound to Semantic Model
    verify: REST API get Data Agent item
    target: cc-campaign-agent
  - id: AC-10
    type: data_flow
    criterion: Activator exists with threshold rules configured
    verify: REST API get Activator definition
    target: cc-alerts-activator
```

## Alternatives Considered

| # | Decision | Option Rejected | Why Rejected |
|---|----------|-----------------|--------------|
| 1 | Task Flow | event-medallion | Streaming-heavy; batch analytics needs equal weight here |
| 2 | Task Flow | medallion (standalone) | No native real-time path for social sentiment speed |
| 3 | Storage | Lakehouse only (no Warehouse) | T-SQL gold layer better for BI/ROI reporting patterns |
| 4 | Ingestion | Dataflow Gen2 for batch | Code-first team prefers Pipeline + Notebook over Power Query |
| 5 | Chatbot | Custom app backend | Data Agent is GA, simpler, and meets internal exec use case |

## Trade-offs

| # | Trade-off | Benefit | Cost | Mitigation |
|---|-----------|---------|------|------------|
| 1 | Three storage engines | Optimal per workload | More items to manage | Lambda pattern keeps layers independent |
| 2 | Code-first processing | Full control, CI/CD-ready | Higher skill bar | Team is code-first by preference |
| 3 | Data Agent for chatbot | Quick deploy, no app code | Limited to read-only queries | Sufficient for exec Q&A use case |
| 4 | RT Dashboard vs Report | Sub-second social updates | Less interactive than Report | Report covers batch ROI separately |

## Deployment Strategy

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Workspace Approach | Single workspace | Minimal complexity per user request |
| Environments | Single (production) | Start simple, add Dev/PPE later |
| CI/CD Tool | fabric-cicd | Project standard |
| Parameterization | Environment Variables | Single-env, skip Variable Library |
| Branching Model | main-only | Single env, iterate fast |

## References

- Project folder: projects/campaign-command/
- Diagram: diagrams/lambda.md
- Validation: validation/lambda.md
- Overlay: diagrams/conversational-analytics.md

## Design Review

| Reviewer | Feedback Summary | Incorporated? | What Changed |
|----------|-----------------|---------------|--------------|
| /fabric-deploy | <!-- pending --> | | |
| /fabric-test | <!-- pending --> | | |
