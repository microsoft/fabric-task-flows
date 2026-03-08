# Event Analytics Diagrams

## Deployment Flow

<!-- AGENT: Skip to "## Deployment Order" for structured item/wave data. The visual diagram below is for human reference. -->

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
│       ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│       │  Real-Time      │    │     Report      │    │   Dashboard     │         │
│       │   Dashboard     │    │      [LC]       │    │     [LC]        │         │
│       │     [LC]        │    │  (Power BI)     │    │ (combined view) │         │
│       └─────────────────┘    └────────┬────────┘    └─────────────────┘         │
│                                       │                                         │
│                                       ▼                                         │
│                              Interactive Analytics                              │
└─────────────────────────────────────────────────────────────────────────────────┘

Legend: [LC] = Low-Code/UI   [CF] = Code-First   [LC/CF] = Both supported
```

## Deployment Order

```
┌───────┬──────────────────┬──────────┬────────────────────────┬──────────────────────────────┐
│ Order │ Item Type        │ Skillset │ Depends On             │ Required For                 │
├───────┼──────────────────┼──────────┼────────────────────────┼──────────────────────────────┤
│   1   │ Eventhouse       │ [LC]     │ (none - foundation)    │ All ingestion, queries, dash │
├───────┼──────────────────┼──────────┼────────────────────────┼──────────────────────────────┤
│  1b   │ Environment      │ [CF]     │ (optional)             │ Notebooks                    │
│  1b   │ Variable Library │ [LC]     │ (depends on: none)     │ Stage-specific config (if multi-env) │
├───────┼──────────────────┼──────────┼────────────────────────┼──────────────────────────────┤
│  2a   │ Eventstream      │ [LC]     │ Eventhouse             │ Real-time data ingestion     │
│  2b   │ Copy Job         │ [LC]     │ Eventhouse             │ Batch data ingestion         │
│  2c   │ Dataflow Gen2    │ [LC]     │ Eventhouse             │ Batch data ingestion         │
│  2d   │ Pipeline         │ [LC/CF]  │ Eventhouse             │ Orchestrated ingestion       │
├───────┼──────────────────┼──────────┼────────────────────────┼──────────────────────────────┤
│   3   │ Activator        │ [LC]     │ Eventstream / Evthouse │ Alert actions                │
├───────┼──────────────────┼──────────┼────────────────────────┼──────────────────────────────┤
│  4a   │ KQL Queryset     │ [CF]     │ Eventhouse             │ Ad-hoc analysis              │
│  4b   │ Notebook         │ [CF]     │ Eventhouse, Environmt  │ Data science                 │
│  4c   │ Experiment       │ [CF]     │ Eventhouse, Environmt  │ ML training                  │
│  4d   │ ML Model         │ [CF]     │ Experiment             │ Predictions                  │
├───────┼──────────────────┼──────────┼────────────────────────┼──────────────────────────────┤
│  5a   │ Real-Time Dash   │ [LC]     │ Eventhouse             │ Live monitoring              │
│  5b   │ Report           │ [LC]     │ Eventhouse / Sem Model │ Analytics                    │
│  5c   │ Dashboard        │ [LC]     │ Report(s)              │ Combined view                │
└───────┴──────────────────┴──────────┴────────────────────────┴──────────────────────────────┘
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
