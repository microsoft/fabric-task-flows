# Translytical Diagrams

## Deployment Flow

<!-- AGENT: Use _shared/registry/deployment-order.json for deployment order data. This visual diagram is for human reference. -->

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
