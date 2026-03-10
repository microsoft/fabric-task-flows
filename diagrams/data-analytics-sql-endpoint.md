# Data Analytics SQL Endpoint Diagrams

## Deployment Flow

<!-- AGENT: Use _shared/registry/deployment-order.json for deployment order data. This visual diagram is for human reference. -->

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│              DATA ANALYTICS USING SQL ANALYTICS ENDPOINT DEPLOYMENT             │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 1: FOUNDATION (Storage)                                                  │
│  ════════════════════════════════                                               │
│  ┌─────────────┐    ┌───────────────────────┐                                   │
│  │  Lakehouse  │───►│ SQL analytics endpoint│ ◄── Auto-provisioned with         │
│  │    [LC]     │    │       [auto]          │     Lakehouse; not deployed        │
│  └──────┬──────┘    └───────────┬───────────┘     separately                    │
│         │                      │                                                │
│         ▼                      │                                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 2: DATA PROCESSING (Prepare)                                             │
│  ════════════════════════════════════                                           │
│  Choose ONE or BOTH based on workflow:                                          │
│                                                                                 │
│  ┌─────────────────────┐              ┌─────────────────────┐                   │
│  │      Notebook       │      OR      │ Spark Job Definition│                   │
│  │   [CF] Interactive  │              │   [CF] Scheduled    │                   │
│  └────────┬────────────┘              └────────┬────────────┘                   │
│           │                                    │                                │
│           └────────────────┬───────────────────┘                                │
│                            │                                                    │
│                            ▼                                                    │
│                   ┌─────────────────┐                                           │
│                   │    Lakehouse    │                                           │
│                   │ (Delta tables)  │                                           │
│                   └────────┬────────┘                                           │
│                            │                                                    │
│                            ▼                                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 3: SEMANTIC LAYER (Store)                                                │
│  ════════════════════════════════                                               │
│                   ┌───────────────────────┐                                     │
│                   │   Semantic Model      │ ◄── Built on SQL analytics endpoint │
│                   │      [LC/CF]          │                                     │
│                   └────────┬──────────────┘                                     │
│                            │                                                    │
│           ┌────────────────┼────────────────────┐                               │
│           ▼                ▼                    ▼                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 4: VISUALIZATION (Visualize)                                             │
│  ════════════════════════════════════                                           │
│  ┌───────────┐   ┌─────────────────┐   ┌─────────────────┐                      │
│  │  Report   │   │ Paginated Report│   │   Scorecard     │                      │
│  │   [LC]    │   │      [LC]       │   │     [LC]        │                      │
│  └───────────┘   └─────────────────┘   └─────────────────┘                      │
└─────────────────────────────────────────────────────────────────────────────────┘

Legend: [LC] = Low-Code/UI   [CF] = Code-First   [LC/CF] = Both supported
```

## Data Processing Decision

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    WHICH DATA PROCESSING ITEM TO USE?                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─ What type of data processing do you need? ────────────────────────────────┐ │
│  │                                                                            │ │
│  │  Ad-hoc exploration ──► Notebook [CF]                                      │ │
│  │                          • Interactive PySpark/SQL                          │ │
│  │                          • Exploratory data analysis                       │ │
│  │                          • Best for development and prototyping            │ │
│  │                                                                            │ │
│  │  Scheduled batch processing ──► Spark Job Definition [CF]                  │ │
│  │                                  • Automated production runs               │ │
│  │                                  • Parameterized execution                 │ │
│  │                                  • Best for recurring ETL                  │ │
│  │                                                                            │ │
│  │  Both ──► Use Notebook for development, then convert to                    │ │
│  │           Spark Job Definition for production                              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─ Query method for semantic model? ─────────────────────────────────────────┐ │
│  │                                                                            │ │
│  │  T-SQL preferred ──► Use SQL analytics endpoint (auto-provisioned)         │ │
│  │                                                                            │ │
│  │  Spark preferred ──► Query Lakehouse Delta tables directly                 │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```
