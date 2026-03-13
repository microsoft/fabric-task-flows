# Medallion Diagrams

## Deployment Flow

<!-- AGENT: Use _shared/registry/deployment-order.json for deployment order data. This visual diagram is for human reference. -->

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
│                                      ▼                                          │
│                             ┌─────────────┐                                     │
│                             │   Report    │                                     │
│                             │    [LC]     │                                     │
│                             └─────────────┘                                     │
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

> **Gold Layer Decision:** See [Storage Selection](../decisions/storage-selection.md#gold-layer-decision) for Lakehouse vs Warehouse comparison.
