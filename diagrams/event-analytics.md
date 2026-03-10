# Event Analytics Diagrams

## Deployment Flow

<!-- AGENT: Use _shared/registry/deployment-order.json for deployment order data. This visual diagram is for human reference. -->

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      EVENT ANALYTICS ARCHITECTURE DEPLOYMENT                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 1: FOUNDATION (Storage + Compute)                                        │
│  ════════════════════════════════════════                                       │
│  ┌──────────────┐         ┌──────────────┐                                     │
│  │  Eventhouse  │         │ Environment  │                                     │
│  │     [LC]     │         │    [CF]      │ ◄── Optional, for Spark/notebooks   │
│  └──────┬───────┘         └──────────────┘                                     │
│         │ (primary real-time store)                                             │
│         ▼                                                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 2: REAL-TIME INGESTION (Get + Track Data)                                │
│  ════════════════════════════════════════════════                               │
│  ┌─────────────────┐         ┌─────────────────┐                               │
│  │   Eventstream   │         │    Activator    │                               │
│  │   [LC] Stream   │────────►│   [LC] Alerts   │                               │
│  └────────┬────────┘         └─────────────────┘                               │
│           │                                                                     │
│           ▼                                                                     │
│  ┌─────────────────┐                                                           │
│  │   Eventhouse    │                                                           │
│  │  (KQL Database) │                                                           │
│  └────────┬────────┘                                                           │
│           │                                                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 3: BATCH INGESTION (Get Data)                                            │
│  ════════════════════════════════════                                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                 │
│  │    Copy Job     │  │  Dataflow Gen2  │  │    Pipeline     │                 │
│  │   [LC] Batch    │  │   [LC] Visual   │  │  [LC/CF] Orch   │                 │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘                 │
│           │                    │                     │                           │
│           └────────────────────┴─────────────────────┘                           │
│                                │                                                 │
│                                ▼                                                 │
│                     ┌─────────────────┐                                         │
│                     │   Eventhouse    │                                         │
│                     │  (KQL Database) │                                         │
│                     └────────┬────────┘                                         │
│                              │                                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 4: QUERY & ANALYSIS                                                      │
│  ════════════════════════════════════════════════════                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                 │
│  │  KQL Queryset   │  │    Notebook     │  │   Experiment    │                 │
│  │      [CF]       │  │      [CF]       │  │      [CF]       │                 │
│  │  (ad-hoc query) │  │  (data science) │  │  (ML training)  │                 │
│  └─────────────────┘  └─────────────────┘  └────────┬────────┘                 │
│                                                      │                           │
│                                               ┌──────▼────────┐                 │
│                                               │   ML Model    │                 │
│                                               │     [CF]      │                 │
│                                               └───────────────┘                 │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 5: VISUALIZATION                                                         │
│  ════════════════════════════════════════════════════                           │
│                                                                                 │
│       ┌─────────────────┐    ┌─────────────────┐                                  │
│       │  Real-Time      │    │     Report      │                                  │
│       │   Dashboard     │    │      [LC]       │                                  │
│       │     [LC]        │    │  (Power BI)     │                                  │
│       └─────────────────┘    └────────┬────────┘                                  │
│                                       │                                         │
│                                       ▼                                         │
│                              Interactive Analytics                              │
└─────────────────────────────────────────────────────────────────────────────────┘

Legend: [LC] = Low-Code/UI   [CF] = Code-First   [LC/CF] = Both supported
```

## Ingestion Path

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     EVENT ANALYTICS: INGESTION SELECTION                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─ Is your data real-time / streaming? ──────────────────────────────────────┐ │
│  │                                                                            │ │
│  │  YES ──► Eventstream [LC]                                                  │ │
│  │          • Event Hubs, Kafka, custom apps                                  │ │
│  │          • Sub-second latency                                              │ │
│  │          • Routes to Eventhouse automatically                              │ │
│  │                                                                            │ │
│  │  NO ──► Is it a simple data copy?                                          │ │
│  │          │                                                                 │ │
│  │          ├─ YES ──► Copy Job [LC]                                          │ │
│  │          │          • Fastest setup                                         │ │
│  │          │          • File or table copy                                    │ │
│  │          │                                                                 │ │
│  │          └─ NO ──► Need transformations?                                   │ │
│  │                    │                                                        │ │
│  │                    ├─ Visual ──► Dataflow Gen2 [LC]                         │ │
│  │                    │            • Power Query interface                     │ │
│  │                    │                                                        │ │
│  │                    └─ Orchestrated ──► Pipeline [LC/CF]                     │ │
│  │                                       • Multi-step workflows               │ │
│  │                                       • Complex dependencies               │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```
