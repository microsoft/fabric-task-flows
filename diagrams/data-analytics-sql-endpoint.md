# Data Analytics SQL Endpoint Diagrams

## Deployment Flow

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
│  ┌───────────┐   ┌───────────┐   ┌─────────────────┐   ┌─────────────────┐     │
│  │  Report   │   │ Dashboard │   │ Paginated Report│   │   Scorecard     │     │
│  │   [LC]    │   │   [LC]    │   │      [LC]       │   │     [LC]        │     │
│  └───────────┘   └───────────┘   └─────────────────┘   └─────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────────┘

Legend: [LC] = Low-Code/UI   [CF] = Code-First   [LC/CF] = Both supported
```

## Deployment Order

```
┌───────┬────────────────────────┬──────────┬────────────────────────────┬────────────────────────┐
│ Order │ Item Type              │ Skillset │ Depends On                 │ Required For           │
├───────┼────────────────────────┼──────────┼────────────────────────────┼────────────────────────┤
│   1   │ Lakehouse              │ [LC]     │ (none - foundation)        │ SQL analytics endpoint │
│       │                        │          │                            │ (auto), All processing │
├───────┼────────────────────────┼──────────┼────────────────────────────┼────────────────────────┤
│   1a  │ SQL analytics endpoint │ [auto]   │ Lakehouse (auto-created)   │ Semantic Model         │
├───────┼────────────────────────┼──────────┼────────────────────────────┼────────────────────────┤
│   2a  │ Notebook               │ [CF]     │ Lakehouse                  │ Delta tables           │
│   2b  │ Spark Job Definition   │ [CF]     │ Lakehouse                  │ Delta tables           │
├───────┼────────────────────────┼──────────┼────────────────────────────┼────────────────────────┤
│   3   │ Semantic Model         │ [LC/CF]  │ SQL analytics endpoint     │ Reports                │
│       │                        │          │ (Lakehouse)                │                        │
├───────┼────────────────────────┼──────────┼────────────────────────────┼────────────────────────┤
│   4a  │ Report                 │ [LC]     │ Semantic Model             │ (optional)             │
│   4b  │ Dashboard              │ [LC]     │ Report(s)                  │ (optional)             │
│   4c  │ Paginated Report       │ [LC]     │ Semantic Model             │ (optional)             │
│   4d  │ Scorecard              │ [LC]     │ Semantic Model             │ (optional)             │
└───────┴────────────────────────┴──────────┴────────────────────────────┴────────────────────────┘
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
