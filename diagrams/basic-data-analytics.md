# Basic Data Analytics Diagrams

## Deployment Flow

<!-- AGENT: Use _shared/registry/deployment-order.json for deployment order data. This visual diagram is for human reference. -->

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        BASIC DATA ANALYTICS DEPLOYMENT                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 1: FOUNDATION (Storage)                                                  │
│  ════════════════════════════════                                               │
│  ┌─────────────┐                                                                │
│  │  Warehouse  │ ◄── Must deploy FIRST - all other items depend on this         │
│  │    [LC]     │                                                                │
│  └──────┬──────┘                                                                │
│         │                                                                       │
│         ▼                                                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 2: INGESTION (Get Data)                                                  │
│  ════════════════════════════════                                               │
│  Choose ONE path based on user skillset:                                        │
│                                                                                 │
│  ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐   │
│  │    Copy Job     │   OR    │  Dataflow Gen2  │   OR    │    Pipeline     │   │
│  │   [LC] Basic    │         │  [LC] Transform │         │  [LC/CF] Orch   │   │
│  └────────┬────────┘         └────────┬────────┘         └────────┬────────┘   │
│           │                           │                           │             │
│           └───────────────────────────┴───────────────────────────┘             │
│                                       │                                         │
│                                       ▼                                         │
│                              ┌─────────────────┐                                │
│                              │    Warehouse    │                                │
│                              │   (populated)   │                                │
│                              └────────┬────────┘                                │
│                                       │                                         │
│                                       ▼                                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 3: SEMANTIC LAYER (Visualize)                                            │
│  ════════════════════════════════════                                           │
│                              ┌─────────────────┐                                │
│                              │  Semantic Model │ ◄── Requires Warehouse data    │
│                              │    [LC/CF]      │                                │
│                              └────────┬────────┘                                │
│                                       │                                         │
│                    ┌──────────────────┼──────────────────┐                      │
│                    ▼                  ▼                  ▼                      │
│           ┌─────────────┐    ┌─────────────────┐   ┌───────────┐                │
│           │   Report    │    │ Paginated Report│   │ Scorecard │                │
│           │    [LC]     │    │      [LC]       │   │   [LC]    │                │
│           └─────────────┘    └─────────────────┘   └───────────┘                │
│                                       │                                         │
│                                       ▼                                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 4: MONITORING (Track Data)                                               │
│  ════════════════════════════════════                                           │
│                    ┌──────────────────┴──────────────────┐                      │
│                    ▼                                     ▼                      │
│           ┌─────────────────┐                   ┌─────────────────┐             │
│           │    Scorecard    │                   │    Activator    │             │
│           │      [LC]       │                   │      [LC]       │             │
│           │  (KPI Tracking) │                   │ (Alert Actions) │             │
│           └─────────────────┘                   └─────────────────┘             │
│                                       │                                         │
│                                       ▼                                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 5: AI & GOVERNANCE (Optional)                                            │
│  ════════════════════════════════════                                           │
│                    ┌──────────────────┴──────────────────┐                      │
│                    ▼                                     ▼                      │
│           ┌─────────────────┐                   ┌─────────────────┐             │
│           │   Data Agent    │                   │    Ontology     │             │
│           │      [LC]       │                   │      [LC]       │             │
│           │  (NL Queries)   │                   │ (Business Terms)│             │
│           └─────────────────┘                   └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────────┘

Legend: [LC] = Low-Code/UI   [CF] = Code-First   [LC/CF] = Both supported
```

## Ingestion Path

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         WHICH INGESTION ITEM TO USE?                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─ Do you need data transformation? ─────────────────────────────────────────┐ │
│  │                                                                            │ │
│  │  NO ──► Copy Job [LC]                                                      │ │
│  │         • Simple file/table copy                                           │ │
│  │         • Fastest to configure                                             │ │
│  │         • Minimal learning curve                                           │ │
│  │                                                                            │ │
│  │  YES ──► Need orchestration of multiple steps?                             │ │
│  │          │                                                                 │ │
│  │          ├─ NO ──► Dataflow Gen2 [LC]                                      │ │
│  │          │         • Power Query transformations                           │ │
│  │          │         • Visual data shaping                                   │ │
│  │          │         • Best for business analysts                            │ │
│  │          │                                                                 │ │
│  │          └─ YES ──► Pipeline [LC/CF]                                       │ │
│  │                     • Multi-activity workflows                             │ │
│  │                     • Conditional logic, loops                             │ │
│  │                     • Can embed Copy + Dataflow activities                 │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```
