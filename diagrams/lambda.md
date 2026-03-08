# Lambda Diagrams

## Deployment Flow

<!-- AGENT: Skip to "## Deployment Order" for structured item/wave data. The visual diagram below is for human reference. -->

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        LAMBDA ARCHITECTURE DEPLOYMENT                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 1: FOUNDATION (Dual Storage)                                            │
│  ════════════════════════════════════════                                       │
│  Deploy BOTH batch and real-time foundations:                                   │
│                                                                                 │
│  ┌─ BATCH LAYER ─────────────────────┐    ┌─ SPEED LAYER ────────────────────┐ │
│  │  ┌───────────┐    ┌───────────┐   │    │  ┌───────────────┐               │ │
│  │  │ Lakehouse │───►│ Warehouse │   │    │  │  Eventhouse   │               │ │
│  │  │   [LC]    │    │   [LC]    │   │    │  │     [LC]      │               │ │
│  │  └───────────┘    └───────────┘   │    │  └───────────────┘               │ │
│  └───────────────────────────────────┘    └──────────────────────────────────┘ │
│         │                                            │                          │
│         ▼                                            ▼                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 2: COMPUTE ENVIRONMENT                                                   │
│  ════════════════════════════════════════                                       │
│  ┌──────────────┐                                                               │
│  │ Environment  │ ◄── Required for Notebooks & Spark Jobs                       │
│  │    [CF]      │                                                               │
│  └──────┬───────┘                                                               │
│         │                                                                       │
│         ▼                                                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 3: INGESTION (Dual Paths)                                                │
│  ════════════════════════════════                                               │
│                                                                                 │
│  ┌─ BATCH INGESTION ─────────────────┐    ┌─ REAL-TIME INGESTION ────────────┐ │
│  │  ┌─────────────┐  ┌─────────────┐ │    │  ┌─────────────────┐             │ │
│  │  │  Copy Job   │  │  Pipeline   │ │    │  │   Eventstream   │             │ │
│  │  │    [LC]     │  │  [LC/CF]    │ │    │  │      [LC]       │             │ │
│  │  └──────┬──────┘  └──────┬──────┘ │    │  └────────┬────────┘             │ │
│  │         └────────┬───────┘        │    │           │                      │ │
│  │                  ▼                │    │           ▼                      │ │
│  │         ┌─────────────┐           │    │  ┌─────────────────┐             │ │
│  │         │  Lakehouse  │           │    │  │   Eventhouse    │             │ │
│  │         └─────────────┘           │    │  └─────────────────┘             │ │
│  └───────────────────────────────────┘    └──────────────────────────────────┘ │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 4: TRANSFORMATION                                                        │
│  ════════════════════════════════════════════════════                           │
│                                                                                 │
│  ┌─ BATCH PROCESSING ────────────────┐    ┌─ STREAM PROCESSING ──────────────┐ │
│  │  ┌─────────────┐  ┌─────────────┐ │    │  ┌─────────────────┐             │ │
│  │  │  Notebook   │  │ Spark Job   │ │    │  │   KQL Queryset  │             │ │
│  │  │    [CF]     │  │ Def [CF]    │ │    │  │      [CF]       │             │ │
│  │  └──────┬──────┘  └──────┬──────┘ │    │  └────────┬────────┘             │ │
│  │         └────────┬───────┘        │    │           │                      │ │
│  │                  ▼                │    │           ▼                      │ │
│  │  ┌───────────┐   ┌───────────┐    │    │  ┌─────────────────┐             │ │
│  │  │ Lakehouse │──►│ Warehouse │    │    │  │   Eventhouse    │             │ │
│  │  │ (curated) │   │  (gold)   │    │    │  │   (hot data)    │             │ │
│  │  └───────────┘   └───────────┘    │    │  └─────────────────┘             │ │
│  └───────────────────────────────────┘    └──────────────────────────────────┘ │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 5: SERVING LAYER (Unified View)                                          │
│  ════════════════════════════════════════════════════                           │
│                                                                                 │
│  ┌─ BATCH VIEWS ─────────────────────┐    ┌─ REAL-TIME VIEWS ────────────────┐ │
│  │  ┌───────────────┐                │    │  ┌─────────────────┐             │ │
│  │  │ Semantic Model│                │    │  │  Real-Time      │             │ │
│  │  │   [LC/CF]     │                │    │  │  Dashboard [LC] │             │ │
│  │  └───────┬───────┘                │    │  └────────┬────────┘             │ │
│  │          │                        │    │           │                      │ │
│  │          ▼                        │    │           │                      │ │
│  │  ┌─────────────┐  ┌─────────────┐ │    │           │                      │ │
│  │  │   Report    │  │  Dashboard  │ │    │           │                      │ │
│  │  │    [LC]     │  │    [LC]     │ │    │           │                      │ │
│  │  └─────────────┘  └─────────────┘ │    │           │                      │ │
│  └───────────────────────────────────┘    └──────────────────────────────────┘ │
│                   │                                   │                         │
│                   └─────────────┬─────────────────────┘                         │
│                                 ▼                                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 6: MONITORING & ML                                                       │
│  ════════════════════════════════════════════════════                           │
│                                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │  Activator  │    │ Experiment  │    │  ML Model   │    │  Notebook   │      │
│  │    [LC]     │    │    [CF]     │    │    [CF]     │    │ (scoring)   │      │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘      │
└─────────────────────────────────────────────────────────────────────────────────┘

Legend: [LC] = Low-Code/UI   [CF] = Code-First   [LC/CF] = Both supported
```

## Deployment Order

```
┌───────┬──────────────────┬──────────┬────────────────────────┬────────────────────┐
│ Order │ Item Type        │ Skillset │ Depends On             │ Required For       │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   1a  │ Lakehouse        │ [LC]     │ (none - foundation)    │ Batch processing   │
│   1b  │ Warehouse        │ [LC]     │ (none - foundation)    │ Batch gold layer   │
│   1c  │ Eventhouse       │ [LC]     │ (none - foundation)    │ Real-time layer    │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   2   │ Environment      │ [CF]     │ Lakehouse              │ Notebooks, Spark   │
│   2   │ Variable Library │ [LC]     │ (depends on: none)     │ Stage-specific config (if multi-env) │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   3a  │ Copy Job         │ [LC]     │ Lakehouse              │ Batch ingestion    │
│   3b  │ Dataflow Gen2    │ [LC]     │ Lakehouse              │ Batch + transform  │
│   3c  │ Pipeline         │ [LC/CF]  │ Lakehouse              │ Orchestration      │
│   3d  │ Eventstream      │ [LC]     │ Eventhouse             │ Real-time ingest   │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   4a  │ Notebook         │ [CF]     │ Environment, Lakehouse │ Batch transforms   │
│   4b  │ Spark Job Def    │ [CF]     │ Environment, Lakehouse │ Scheduled batch    │
│   4c  │ KQL Queryset     │ [CF]     │ Eventhouse             │ Stream transforms  │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   5a  │ Semantic Model   │ [LC/CF]  │ Warehouse/Lakehouse    │ Batch reports      │
│   5b  │ Real-Time Dash   │ [LC]     │ Eventhouse             │ Live monitoring    │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   6a  │ Report           │ [LC]     │ Semantic Model         │ Dashboard          │
│   6b  │ Dashboard        │ [LC]     │ Reports                │ (optional)         │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   7a  │ Activator        │ [LC]     │ Eventstream/Reports    │ Alerts             │
│   7b  │ Experiment       │ [CF]     │ Lakehouse, Environment │ ML Model           │
│   7c  │ ML Model         │ [CF]     │ Experiment             │ Predictions        │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   7d  │ Data Agent       │ [LC]     │ Warehouse, Lakehouse,  │ (optional)         │
│       │                  │          │ OR Semantic Model      │                    │
│   7e  │ Ontology         │ [LC]     │ Semantic Model         │ (optional)         │
└───────┴──────────────────┴──────────┴────────────────────────┴────────────────────┘
```

## Lambda Decision

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       LAMBDA: WHEN TO USE EACH LAYER                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─ SPEED LAYER (Real-Time) ──────────────────────────────────────────────────┐ │
│  │  Use when:                                                                 │ │
│  │  • Data freshness < 1 minute required                                      │ │
│  │  • Live dashboards needed                                                  │ │
│  │  • Real-time alerting                                                      │ │
│  │  • IoT, clickstream, logs                                                  │ │
│  │                                                                            │ │
│  │  Items: Eventstream → Eventhouse → KQL Queryset → Real-Time Dashboard      │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─ BATCH LAYER (Historical) ─────────────────────────────────────────────────┐ │
│  │  Use when:                                                                 │ │
│  │  • Complex transformations needed                                          │ │
│  │  • Historical analysis required                                            │ │
│  │  • ML training on full dataset                                             │ │
│  │  • Data freshness hours/days acceptable                                    │ │
│  │                                                                            │ │
│  │  Items: Copy Job/Pipeline → Lakehouse → Notebook → Warehouse → Report      │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─ SERVING LAYER (Unified) ──────────────────────────────────────────────────┐ │
│  │  Combine both views for complete picture:                                  │ │
│  │  • Dashboard with batch + real-time tiles                                  │ │
│  │  • Activator monitoring both layers                                        │ │
│  │  • ML models scoring real-time data                                        │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```
