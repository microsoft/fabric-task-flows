# Architecture

## Overview

Campaign Command uses a **Lambda architecture** with a **Conversational Analytics overlay** to process marketing data at two velocities: batch (Google Analytics, AdWords) and real-time (social media sentiment). An exec-facing Data Agent provides self-service campaign Q&A.

## System Diagram

```
  Google Analytics ──┐                    Social Media APIs
  AdWords API ───────┤                           │
                     ▼                           ▼
              ┌─────────────┐           ┌──────────────────┐
              │  Pipeline   │           │   Eventstream    │
              └──────┬──────┘           └────────┬─────────┘
                     ▼                           ▼
              ┌─────────────┐           ┌──────────────────┐
              │  Lakehouse  │           │   Eventhouse     │
              │   (raw)     │           │  + KQL Database  │
              └──────┬──────┘           └────────┬─────────┘
                     ▼                           ▼
              ┌─────────────┐           ┌──────────────────┐
              │  Notebook   │           │  KQL Queryset    │
              └──────┬──────┘           └────────┬─────────┘
                     ▼                           ▼
              ┌─────────────┐           ┌──────────────────┐
              │  Warehouse  │           │  RT Dashboard    │
              │   (gold)    │           └──────────────────┘
              └──────┬──────┘
                     ▼
              ┌─────────────┐     ┌─────────────┐
              │Semantic Model│────►│   Report    │
              └──────┬──────┘     └─────────────┘
                     ▼
              ┌─────────────┐
              │ Data Agent  │  (exec chatbot)
              └─────────────┘
```

## Items

| Item | Type | Purpose | Wave |
|------|------|---------|------|
| cc_raw_lakehouse | Lakehouse | Raw batch data landing zone | 1 |
| cc_gold_warehouse | Warehouse | Curated gold layer for BI | 1 |
| cc_stream_eventhouse | Eventhouse | Real-time social sentiment | 1 |
| cc_stream_kqldb | KQL Database | Stream queries within Eventhouse | 1 |
| cc_spark_environment | Environment | Spark/Python runtime | 2 |
| cc_batch_pipeline | Data Pipeline | Batch ingestion orchestration | 2 |
| cc_social_eventstream | Eventstream | Real-time social media feeds | 2 |
| cc_transform_nb | Notebook | Batch transforms + sentiment scoring | 3 |
| cc_stream_kql | KQL Queryset | Real-time stream aggregations | 3 |
| cc_campaign_sem | Semantic Model | Unified campaign model (Direct Lake) | 4 |
| cc_rt_dashboard | RT Dashboard | Live social sentiment monitoring | 4 |
| cc_roi_report | Report | Interactive ROI + regional analysis | 5 |
| cc_campaign_agent | Data Agent | Internal exec self-service Q&A | 5 |
| cc_alerts_activator | Activator | ROI threshold alerts | 6 |

## Data Flow

1. **Batch path:** Google Analytics + AdWords APIs → Pipeline → Lakehouse (raw) → Notebook (transform) → Warehouse (gold) → Semantic Model → Report + Data Agent
2. **Speed path:** Social media APIs → Eventstream → Eventhouse/KQL DB → KQL Queryset → Real-Time Dashboard
3. **Monitoring:** Activator watches both paths for ROI threshold alerts

## Deployment Strategy

| Aspect | Choice |
|--------|--------|
| Workspace approach | Single workspace |
| Environments | Single (production) |
| CI/CD tool | fabric-cicd |
| Parameterization | Environment Variables |
| Branching model | main-only |

## Configuration Summary

| Item | Setting | Rationale |
|------|---------|-----------|
| cc_raw_lakehouse | Default | Raw batch landing zone |
| cc_gold_warehouse | Default | T-SQL gold layer for BI |
| cc_campaign_sem | Direct Lake | Optimal query performance |
| cc_social_eventstream | Underscore naming | Eventstream rejects hyphens |
