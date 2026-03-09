---
project: campaign-command
task_flow: lambda
phase: final
status: final
created: 2026-03-09
last_updated: 2026-03-09
design_review:
  engineer: approved
  tester: approved
items: 14
acceptance_criteria: 13
manual_steps: 2
deployment_waves: 6
blockers:
  critical: []
  medium: []
next_phase: test-plan
---

# Architecture Handoff — FINAL

**Project:** Campaign Command
**Task flow:** lambda + conversational-analytics (overlay)
**Date:** 2026-03-09
**Status:** FINAL — Review complete. Ready for test plan and sign-off.

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
    name: cc-stream-kqldb
    type: KQLDatabase
    skillset: LC
    depends_on: [3]
    purpose: KQL Database within Eventhouse for stream queries
  - id: 5
    name: cc-spark-environment
    type: Environment
    skillset: CF
    depends_on: [1]
    purpose: Spark/Python runtime for batch transform notebooks
  - id: 6
    name: cc-batch-pipeline
    type: DataPipeline
    skillset: CF
    depends_on: [1]
    purpose: Orchestrate batch ingestion from Analytics + AdWords APIs
  - id: 7
    name: cc-social-eventstream
    type: Eventstream
    skillset: LC
    depends_on: [4]
    purpose: Ingest real-time social media sentiment feeds
  - id: 8
    name: cc-transform-nb
    type: Notebook
    skillset: CF
    depends_on: [1, 5]
    purpose: Batch transforms, sentiment scoring, regional aggregation
  - id: 9
    name: cc-stream-kql
    type: KQLQueryset
    skillset: CF
    depends_on: [4]
    purpose: Real-time stream aggregations on social data
  - id: 10
    name: cc-campaign-sem
    type: SemanticModel
    skillset: CF
    depends_on: [2]
    purpose: Unified campaign model for ROI reporting + Data Agent
  - id: 11
    name: cc-rt-dashboard
    type: Dashboard
    skillset: LC
    depends_on: [4]
    purpose: Live social sentiment monitoring (sub-second)
  - id: 12
    name: cc-roi-report
    type: Report
    skillset: LC
    depends_on: [10]
    purpose: Interactive ROI and regional ad performance reports
  - id: 13
    name: cc-campaign-agent
    type: DataAgent
    skillset: LC
    depends_on: [10]
    purpose: Internal exec chatbot for self-service campaign Q&A
  - id: 14
    name: cc-alerts-activator
    type: Reflex
    skillset: LC
    depends_on: [4, 7]
    purpose: ROI threshold alerts for regional ad buy decisions
```

### Deployment Order

```yaml
waves:
  - id: 1
    name: Foundation
    items: [cc-raw-lakehouse, cc-gold-warehouse, cc-stream-eventhouse, cc-stream-kqldb]
    parallel: true
  - id: 2
    name: Compute + Ingestion
    items: [cc-spark-environment, cc-batch-pipeline, cc-social-eventstream]
    blocked_by: [1]
    parallel: true
  - id: 3
    name: Transformation
    items: [cc-transform-nb, cc-stream-kql]
    blocked_by: [2]
    parallel: true
  - id: 4
    name: Serving
    items: [cc-campaign-sem, cc-rt-dashboard]
    blocked_by: [1, 3]
    parallel: true
  - id: 5
    name: Consumption
    items: [cc-roi-report, cc-campaign-agent]
    blocked_by: [4]
    parallel: true
  - id: 6
    name: Monitoring
    items: [cc-alerts-activator]
    blocked_by: [2]
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
    criterion: KQL Database exists within Eventhouse
    verify: REST API list KQL Databases filtered by Eventhouse
    target: cc-stream-kqldb
  - id: AC-3
    type: structural
    criterion: Environment exists and is published
    verify: REST API get Environment item, check publish status
    target: cc-spark-environment
  - id: AC-4
    type: structural
    criterion: Eventstream is created and bound to KQL Database
    verify: REST API get Eventstream definition
    target: cc-social-eventstream
  - id: AC-5
    type: structural
    criterion: Pipeline is created with Copy activities for batch sources
    verify: REST API get Pipeline definition
    target: cc-batch-pipeline
  - id: AC-6
    type: structural
    criterion: Notebook exists with Environment attached
    verify: REST API get Notebook definition
    target: cc-transform-nb
  - id: AC-7
    type: structural
    criterion: KQL Queryset exists and references KQL Database
    verify: REST API get KQL Queryset definition
    target: cc-stream-kql
  - id: AC-8
    type: structural
    criterion: Semantic Model exists with Direct Lake mode via TMDL expression
    verify: REST API get Semantic Model definition, check expression property
    target: cc-campaign-sem
  - id: AC-9
    type: structural
    criterion: Report exists and is bound to Semantic Model
    verify: REST API get Report definition
    target: cc-roi-report
  - id: AC-10
    type: structural
    criterion: Real-Time Dashboard exists and queries KQL Database
    verify: REST API get Dashboard definition
    target: cc-rt-dashboard
  - id: AC-11
    type: structural
    criterion: Data Agent exists and is bound to Semantic Model
    verify: REST API get Data Agent item
    target: cc-campaign-agent
  - id: AC-12
    type: data_flow
    criterion: Activator exists with threshold rules configured
    verify: REST API get Activator definition
    target: cc-alerts-activator
  - id: AC-13
    type: manual
    criterion: Semantic Model Direct Lake connection manually configured
    verify: Verify first refresh succeeds after manual connection setup
    target: cc-campaign-sem
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

| Finding | Severity | Action Taken |
|---------|----------|--------------|
| F-1: Merge Environment into ingestion wave | Yellow | Merged Waves 2+3 → "Compute + Ingestion" (6 waves total) |
| F-2: Semantic Model needs manual Direct Lake config | Yellow | Added AC-13 as manual verification step |
| F-5: Missing KQL Database item | Yellow | Added cc-stream-kqldb (item 3b) in Wave 1 |
| T-1: No AC for Environment | Yellow | Added AC-3 for Environment existence/published |
| T-2: AC-6 Direct Lake not specific enough | Yellow | Updated AC-8 to verify via TMDL expression property |
| T-5: No AC for KQL Database | Yellow | Added AC-2 for KQL Database within Eventhouse |

| Reviewer | Feedback Summary | Incorporated? | What Changed |
|----------|-----------------|---------------|--------------|
| /fabric-deploy | 3 yellows: wave merge, manual step, missing KQL DB | Yes | Waves 7→6, added KQL DB, added manual AC |
| /fabric-test | 3 yellows: missing Environment AC, AC specificity, KQL DB AC | Yes | Added 3 ACs, refined verification methods |
