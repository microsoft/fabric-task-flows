# Translytical Diagrams

## Deployment Flow

<!-- AGENT: Skip to "## Deployment Order" for structured item/wave data. The visual diagram below is for human reference. -->

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      TRANSLYTICAL ARCHITECTURE DEPLOYMENT                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 1: FOUNDATION (Transactional Storage)                                    │
│  ════════════════════════════════════════════                                   │
│  ┌───────────────────┐                                                          │
│  │   SQL Database    │ ◄── OLTP-capable storage with transactions               │
│  │      [LC]         │                                                          │
│  │  (read + write)   │                                                          │
│  └─────────┬─────────┘                                                          │
│            │                                                                    │
│            ▼                                                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 2: SEMANTIC LAYER                                                        │
│  ════════════════════════════════════════════                                   │
│  ┌───────────────────┐                                                          │
│  │   Semantic Model  │ ◄── Connect to SQL Database for analytics                │
│  │     [LC/CF]       │                                                          │
│  └─────────┬─────────┘                                                          │
│            │                                                                    │
│            ▼                                                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 3: VISUALIZATION (With Writeback)                                        │
│  ════════════════════════════════════════════                                   │
│  ┌───────────────────┐                                                          │
│  │      Report       │ ◄── Power BI report with writeback capabilities          │
│  │       [LC]        │                                                          │
│  │  ✏️ Data Entry    │                                                          │
│  │  ✏️ Writeback     │                                                          │
│  └─────────┬─────────┘                                                          │
│            │                                                                    │
│            │  (user actions)                                                    │
│            ▼                                                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 4: DEVELOPMENT (Actions & Functions)                                     │
│  ════════════════════════════════════════════                                   │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                        User Data Functions                                │  │
│  │                            [CF]                                           │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │  │
│  │  │  Write to SQL   │  │ Send Notifs     │  │ Trigger Workflow│            │  │
│  │  │  (INSERT/UPDATE)│  │ (Email/Teams)   │  │ (Power Automate)│            │  │
│  │  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘            │  │
│  │           │                    │                    │                     │  │
│  │           └────────────────────┴────────────────────┘                     │  │
│  │                               │                                           │  │
│  │                               ▼                                           │  │
│  │                    ┌───────────────────┐                                  │  │
│  │                    │   SQL Database    │◄─── Data writeback               │  │
│  │                    │   (updated)       │                                  │  │
│  │                    └───────────────────┘                                  │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘

Legend: [LC] = Low-Code/UI   [CF] = Code-First   ✏️ = Writeback enabled
```

## Deployment Order

```
┌───────┬──────────────────┬──────────┬────────────────────────┬────────────────────┐
│ Order │ Item Type        │ Skillset │ Depends On             │ Required For       │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   1   │ SQL Database     │ [LC]     │ (none - foundation)    │ Semantic Model,    │
│       │                  │          │                        │ User Data Functions│
│   1   │ Variable Library │ [LC]     │ (depends on: none)     │ Stage-specific config (if multi-env) │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   2   │ Semantic Model   │ [LC/CF]  │ SQL Database           │ Report             │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   3   │ Report           │ [LC]     │ Semantic Model         │ User interactions  │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   4   │ User Data Funcs  │ [CF]     │ SQL Database           │ Writeback actions  │
└───────┴──────────────────┴──────────┴────────────────────────┴────────────────────┘
```

## Writeback Scenarios

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      TRANSLYTICAL: WRITEBACK SCENARIOS                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  DATA ENTRY                                                                     │
│  ═══════════                                                                    │
│  • Budget planning in reports                                                   │
│  • Forecast adjustments                                                         │
│  • Commentary and annotations                                                   │
│  • Manual overrides                                                             │
│                                                                                 │
│  OPERATIONAL ACTIONS                                                            │
│  ═══════════════════                                                            │
│  • Approve/reject workflows                                                     │
│  • Update record status                                                         │
│  • Trigger downstream processes                                                 │
│  • Send notifications                                                           │
│                                                                                 │
│  FEEDBACK LOOPS                                                                 │
│  ══════════════                                                                 │
│  • Model corrections                                                            │
│  • Data quality flags                                                           │
│  • User preferences                                                             │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```
