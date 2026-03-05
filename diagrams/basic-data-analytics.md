# Basic Data Analytics Diagrams

## Deployment Flow

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
│           │   Report    │    │ Paginated Report│   │ Dashboard │                │
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
└─────────────────────────────────────────────────────────────────────────────────┘

Legend: [LC] = Low-Code/UI   [CF] = Code-First   [LC/CF] = Both supported
```

## Deployment Order

```
┌───────┬──────────────────┬──────────┬────────────────────────┬────────────────────┐
│ Order │ Item Type        │ Skillset │ Depends On             │ Required For       │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   1   │ Warehouse        │ [LC]     │ (none - foundation)    │ All ingestion,     │
│       │                  │          │                        │ Semantic Model     │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   2a  │ Copy Job         │ [LC]     │ Warehouse              │ Data in Warehouse  │
│   2b  │ Dataflow Gen2    │ [LC]     │ Warehouse              │ Data in Warehouse  │
│   2c  │ Pipeline         │ [LC/CF]  │ Warehouse              │ Data in Warehouse  │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   3   │ Semantic Model   │ [LC/CF]  │ Warehouse (populated)  │ Reports, Dashboard │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   4a  │ Report           │ [LC]     │ Semantic Model         │ Dashboard          │
│   4b  │ Paginated Report │ [LC]     │ Semantic Model         │ (optional)         │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   5   │ Dashboard        │ [LC]     │ Report(s)              │ (optional)         │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   6a  │ Scorecard        │ [LC]     │ Semantic Model         │ (optional)         │
│   6b  │ Activator        │ [LC]     │ Semantic Model OR      │ (optional)         │
│       │                  │          │ Report                 │                    │
└───────┴──────────────────┴──────────┴────────────────────────┴────────────────────┘
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
