# Medallion Diagrams

## Deployment Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        MEDALLION ARCHITECTURE DEPLOYMENT                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 1: FOUNDATION (Storage Layers)                                          │
│  ════════════════════════════════════════                                       │
│  Deploy Bronze and Silver layers, then CHOOSE Gold layer type:                  │
│                                                                                 │
│  ┌──────────────┐    ┌──────────────┐         ┌──────────────────────────────┐  │
│  │   Lakehouse  │───►│   Lakehouse  │───►     │  GOLD LAYER DECISION         │  │
│  │   (Bronze)   │    │   (Silver)   │    ┌────┤  Choose ONE based on needs:  │  │
│  │    [LC]      │    │    [LC]      │    │    └──────────────────────────────┘  │
│  └──────┬───────┘    └──────────────┘    │                                      │
│         │                                ▼                                      │
│         │    ┌───────────────────────────────────────────────────────────────┐  │
│         │    │  ┌─────────────────────┐    OR    ┌─────────────────────┐     │  │
│         │    │  │   Lakehouse Gold    │          │   Warehouse Gold    │     │  │
│         │    │  │       [LC]          │          │       [LC]          │     │  │
│         │    │  └─────────────────────┘          └─────────────────────┘     │  │
│         │    │                                                               │  │
│         │    │  DIFFERENTIATORS:                                             │  │
│         │    │  ┌─────────────────────────────┬─────────────────────────────┐│  │
│         │    │  │        LAKEHOUSE            │        WAREHOUSE            ││  │
│         │    │  ├─────────────────────────────┼─────────────────────────────┤│  │
│         │    │  │ • Read-only via Spark/SQL   │ • Full Read/Write T-SQL     ││  │
│         │    │  │ • Delta Lake format         │ • Relational tables         ││  │
│         │    │  │ • Best for ML/Data Science  │ • Best for BI/Reporting     ││  │
│         │    │  │ • Spark-native workloads    │ • Traditional DW workloads  ││  │
│         │    │  │ • Schema-on-read flexible   │ • Schema-on-write enforced  ││  │
│         │    │  │ • Time travel & versioning  │ • T-SQL stored procedures   ││  │
│         │    │  │ • Lower compute cost        │ • Optimized query engine    ││  │
│         │    │  └─────────────────────────────┴─────────────────────────────┘│  │
│         │    └───────────────────────────────────────────────────────────────┘  │
│         ▼                                                                       │
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
│  PHASE 3: INGESTION (Get Data → Bronze)                                         │
│  ════════════════════════════════════════                                       │
│  Choose ingestion method(s):                                                    │
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌────────────┐ │
│  │    Copy Job     │  │  Dataflow Gen2  │  │    Pipeline     │  │ Eventstream│ │
│  │   [LC] Batch    │  │  [LC] Transform │  │  [LC/CF] Orch   │  │[LC] Stream │ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  └─────┬──────┘ │
│           │                    │                    │                 │         │
│           └────────────────────┴────────────────────┴─────────────────┘         │
│                                       │                                         │
│                                       ▼                                         │
│                            ┌───────────────────┐                                │
│                            │  Lakehouse Bronze │                                │
│                            │    (raw data)     │                                │
│                            └─────────┬─────────┘                                │
│                                      │                                          │
│                                      ▼                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 4: TRANSFORMATION (Bronze → Silver → Gold)                               │
│  ════════════════════════════════════════════════════                           │
│  Choose transformation method:                                                  │
│                                                                                 │
│  ┌─────────────────────┐              ┌─────────────────────┐                   │
│  │      Notebook       │      OR      │  Spark Job Def      │                   │
│  │   [CF] Interactive  │              │   [CF] Scheduled    │                   │
│  └──────────┬──────────┘              └──────────┬──────────┘                   │
│             │                                    │                              │
│             └────────────────┬───────────────────┘                              │
│                              │                                                  │
│                              ▼                                                  │
│  ┌───────────────────┐    ┌───────────────────┐    ┌───────────────────────┐    │
│  │  Lakehouse Bronze │───►│  Lakehouse Silver │───►│   Gold Layer          │    │
│  │    (raw data)     │    │   (cleansed)      │    │  (Lakehouse OR        │    │
│  └───────────────────┘    └───────────────────┘    │   Warehouse)          │    │
│                                                    └───────────┬───────────┘    │
│                                                                │                │
│                                                                ▼                │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 5: SEMANTIC LAYER & VISUALIZATION                                        │
│  ════════════════════════════════════════════════════                           │
│                            ┌───────────────────┐                                │
│                            │   Semantic Model  │ ◄── Built on Gold layer        │
│                            │     [LC/CF]       │     (Lakehouse or Warehouse)   │
│                            └─────────┬─────────┘                                │
│                                      │                                          │
│                    ┌─────────────────┴─────────────────┐                        │
│                    ▼                                   ▼                        │
│           ┌─────────────┐                      ┌─────────────┐                  │
│           │   Report    │                      │  Dashboard  │                  │
│           │    [LC]     │                      │    [LC]     │                  │
│           └─────────────┘                      └─────────────┘                  │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 6: MACHINE LEARNING (Optional)                                           │
│  ════════════════════════════════════════════════════                           │
│                            ┌───────────────────┐                                │
│                            │    Experiment     │ ◄── Uses Gold layer data       │
│                            │      [CF]         │                                │
│                            └─────────┬─────────┘                                │
│                                      │                                          │
│                                      ▼                                          │
│                            ┌───────────────────┐                                │
│                            │     ML Model      │                                │
│                            │      [CF]         │                                │
│                            └───────────────────┘                                │
└─────────────────────────────────────────────────────────────────────────────────┘

Legend: [LC] = Low-Code/UI   [CF] = Code-First   [LC/CF] = Both supported
```

## Deployment Order

```
┌───────┬──────────────────┬──────────┬────────────────────────┬────────────────────┐
│ Order │ Item Type        │ Skillset │ Depends On             │ Required For       │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   1a  │ Lakehouse Bronze │ [LC]     │ (none - foundation)    │ Ingestion, Silver  │
│   1b  │ Lakehouse Silver │ [LC]     │ (none - foundation)    │ Gold layer         │
│   1c  │ Lakehouse Gold   │ [LC]     │ (none - foundation)    │ Semantic Model, ML │
│       │ ──OR──           │          │                        │ (CHOOSE ONE)       │
│   1c  │ Warehouse Gold   │ [LC]     │ (none - foundation)    │ Semantic Model, BI │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   2   │ Environment      │ [CF]     │ Lakehouses             │ Notebooks, Spark   │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   3a  │ Copy Job         │ [LC]     │ Bronze Lakehouse       │ Raw data ingestion │
│   3b  │ Dataflow Gen2    │ [LC]     │ Bronze Lakehouse       │ Raw data ingestion │
│   3c  │ Pipeline         │ [LC/CF]  │ Bronze Lakehouse       │ Orchestrated load  │
│   3d  │ Eventstream      │ [LC]     │ Bronze Lakehouse       │ Streaming data     │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   4a  │ Notebook         │ [CF]     │ Environment, Bronze    │ Transformations    │
│   4b  │ Spark Job Def    │ [CF]     │ Environment, Bronze    │ Scheduled jobs     │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   5   │ Semantic Model   │ [LC/CF]  │ Gold Lakehouse OR      │ Reports            │
│       │                  │          │ Gold Warehouse         │                    │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   6a  │ Report           │ [LC]     │ Semantic Model         │ Dashboard          │
│   6b  │ Dashboard        │ [LC]     │ Report(s)              │ (optional)         │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   7a  │ Experiment       │ [CF]     │ Gold Lakehouse, Env    │ ML Model           │
│   7b  │ ML Model         │ [CF]     │ Experiment             │ (optional)         │
└───────┴──────────────────┴──────────┴────────────────────────┴────────────────────┘
```

## Gold Layer Decision

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         MEDALLION LAYER PURPOSES                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  BRONZE (Raw)                                                                   │
│  ══════════════                                                                 │
│  • Raw data as-is from source                                                   │
│  • Append-only, immutable                                                       │
│  • Full history preserved                                                       │
│  • Schema: source schema (may vary)                                             │
│                                                                                 │
│  SILVER (Cleansed)                                                              │
│  ══════════════════                                                             │
│  • Validated, deduplicated                                                      │
│  • Standardized schemas                                                         │
│  • Business keys applied                                                        │
│  • Conformed dimensions                                                         │
│                                                                                 │
│  GOLD (Business-Ready) - CHOOSE: Lakehouse OR Warehouse                        │
│  ════════════════════════════════════════════════════════                       │
│  • Aggregated, enriched                                                         │
│  • Business-level entities                                                      │
│  • Optimized for consumption                                                    │
│  • Ready for BI and ML                                                          │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ GOLD LAYER DECISION GUIDE:                                              │    │
│  │                                                                         │    │
│  │ Choose LAKEHOUSE Gold when:          Choose WAREHOUSE Gold when:        │    │
│  │ • Spark/Python-based consumption     • T-SQL is primary query language  │    │
│  │ • Machine learning workloads         • Traditional BI reporting         │    │
│  │ • Need Delta Lake features           • Need stored procedures/views     │    │
│  │ • Read-heavy analytical queries      • Read/Write transactional access  │    │
│  │ • Schema flexibility required        • Strict schema enforcement        │    │
│  │ • Data science team primary users    • Business analysts primary users  │    │
│  │ • Cost optimization priority         • Query performance priority       │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```
