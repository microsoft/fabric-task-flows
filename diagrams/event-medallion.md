# Event Medallion Diagrams

## Deployment Flow

<!-- AGENT: Skip to "## Deployment Order" for structured item/wave data. The visual diagram below is for human reference. -->

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      EVENT MEDALLION ARCHITECTURE DEPLOYMENT                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 1: FOUNDATION (Real-Time Storage)                                        │
│  ════════════════════════════════════════                                       │
│  ┌──────────────┐                                                               │
│  │  Eventhouse  │ ◄── Must deploy FIRST - contains KQL databases                │
│  │     [LC]     │                                                               │
│  └──────┬───────┘                                                               │
│         │ (auto-creates KQL Database)                                           │
│         ▼                                                                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                       │
│  │ KQL Database │    │ KQL Database │    │ KQL Database │                       │
│  │   (Bronze)   │───►│   (Silver)   │───►│    (Gold)    │                       │
│  └──────────────┘    └──────────────┘    └──────────────┘                       │
│         │                                                                       │
│         ▼                                                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 2: INGESTION (Get Data)                                                  │
│  ════════════════════════════════                                               │
│  Real-time + Batch ingestion paths:                                             │
│                                                                                 │
│  ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐   │
│  │   Eventstream   │         │    Copy Job     │         │    Pipeline     │   │
│  │   [LC] Stream   │         │   [LC] Batch    │         │  [LC/CF] Orch   │   │
│  └────────┬────────┘         └────────┬────────┘         └────────┬────────┘   │
│           │                           │                           │             │
│           └───────────────────────────┴───────────────────────────┘             │
│                                       │                                         │
│                                       ▼                                         │
│                            ┌───────────────────┐                                │
│                            │ KQL Database Bronze│                               │
│                            │    (raw events)    │                               │
│                            └─────────┬─────────┘                                │
│                                      │                                          │
│                                      ▼                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 3: TRANSFORMATION (KQL Processing)                                       │
│  ════════════════════════════════════════════════════                           │
│                            ┌───────────────────┐                                │
│                            │    KQL Queryset   │ ◄── Materialized views,        │
│                            │       [CF]        │     update policies            │
│                            └─────────┬─────────┘                                │
│                                      │                                          │
│  ┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐        │
│  │  KQL DB Bronze    │───►│   KQL DB Silver   │───►│   KQL DB Gold     │        │
│  │   (raw events)    │    │    (enriched)     │    │   (aggregated)    │        │
│  └───────────────────┘    └───────────────────┘    └─────────┬─────────┘        │
│                                                              │                  │
│                                                              ▼                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 4: VISUALIZATION                                                         │
│  ════════════════════════════════════════════════════                           │
│                                                                                 │
│                    ┌─────────────────┐    ┌─────────────────┐                   │
│                    │  Real-Time      │    │     Report      │                   │
│                    │   Dashboard     │    │      [LC]       │                   │
│                    │     [LC]        │    │  (Power BI)     │                   │
│                    └────────┬────────┘    └────────┬────────┘                   │
│                             │                      │                            │
│                             └──────────┬───────────┘                            │
│                                        │                                        │
│                                        ▼                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 5: MONITORING (Track Data)                                               │
│  ════════════════════════════════════                                           │
│                            ┌───────────────────┐                                │
│                            │    Activator      │ ◄── Event-driven alerts        │
│                            │      [LC]         │                                │
│                            └───────────────────┘                                │
└─────────────────────────────────────────────────────────────────────────────────┘

Legend: [LC] = Low-Code/UI   [CF] = Code-First   [LC/CF] = Both supported
```

## Deployment Order

```
┌───────┬──────────────────┬──────────┬────────────────────────┬────────────────────┐
│ Order │ Item Type        │ Skillset │ Depends On             │ Required For       │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   1   │ Eventhouse       │ [LC]     │ (none - foundation)    │ KQL Databases      │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   2a  │ Eventstream      │ [LC]     │ Eventhouse             │ Real-time data     │
│   2b  │ Copy Job         │ [LC]     │ Eventhouse             │ Batch data         │
│   2c  │ Pipeline         │ [LC/CF]  │ Eventhouse             │ Orchestrated data  │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   3   │ KQL Queryset     │ [CF]     │ Eventhouse, data       │ Transformations    │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   4a  │ Real-Time Dash   │ [LC]     │ KQL Database           │ Live monitoring    │
│   4b  │ Report           │ [LC]     │ KQL Database           │ Historical views   │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   5   │ Activator        │ [LC]     │ Eventstream OR KQL     │ (optional alerts)  │
└───────┴──────────────────┴──────────┴────────────────────────┴────────────────────┘
```

## Medallion Layer Decision

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                   EVENT MEDALLION: REAL-TIME VS BATCH                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─ Is your data streaming in real-time? ─────────────────────────────────────┐ │
│  │                                                                            │ │
│  │  YES ──► Use Eventstream to ingest to Bronze                               │ │
│  │          • Event Hubs, Kafka, IoT Hub                                      │ │
│  │          • Sub-second latency                                              │ │
│  │                                                                            │ │
│  │  NO ──► Use Copy Job or Pipeline for batch loads                           │ │
│  │         • Files, databases                                                 │ │
│  │         • Scheduled refreshes                                              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─ Layer Purposes in Event Medallion ────────────────────────────────────────┐ │
│  │                                                                            │ │
│  │  BRONZE: Raw events as received                                            │ │
│  │  SILVER: Cleansed, deduplicated, enriched                                  │ │
│  │  GOLD: Aggregated metrics, materialized views                              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```
