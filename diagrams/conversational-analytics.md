# Conversational Analytics Diagrams

## Deployment Flow

<!-- AGENT: Skip to "## Deployment Order" for structured item/wave data. The visual diagram below is for human reference. -->

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                   CONVERSATIONAL ANALYTICS DEPLOYMENT                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 1: FOUNDATION (Storage)                                                  │
│  ════════════════════════════════                                               │
│  ┌───────────────────────────┐                                                  │
│  │  Lakehouse OR Warehouse  │ ◄── Prerequisite: deploy via another task flow   │
│  │       [LC/CF]            │     (e.g., medallion, basic-data-analytics)       │
│  └────────────┬─────────────┘                                                  │
│               │                                                                │
│               ▼                                                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 2: SEMANTIC LAYER (Model Data)                                           │
│  ════════════════════════════════════                                           │
│  ┌─────────────────┐                                                            │
│  │  Semantic Model │ ◄── Defines the query surface the agent will use          │
│  │    [LC/CF]      │                                                            │
│  └────────┬────────┘                                                            │
│           │                                                                    │
│           ▼                                                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 3: AGENT DEPLOYMENT (Deploy Agent)                                       │
│  ════════════════════════════════════════                                       │
│  ┌─────────────────┐                                                            │
│  │   Data Agent    │ ◄── Portal-only: configure in Fabric workspace UI         │
│  │    [Portal]     │     Bind to Semantic Model, set access controls            │
│  └────────┬────────┘                                                            │
│           │                                                                    │
│           ▼                                                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 4: OPTIONAL GOVERNANCE                                                   │
│  ════════════════════════════                                                  │
│  ┌─────────────────┐         ┌─────────────────┐                                │
│  │    Ontology     │         │    Activator    │                                │
│  │    [Portal]     │         │      [LC]       │                                │
│  │ (Business       │         │ (Usage alerts)  │                                │
│  │  vocabulary)    │         │                 │                                │
│  └─────────────────┘         └─────────────────┘                                │
└─────────────────────────────────────────────────────────────────────────────────┘

Legend: [LC] = Low-Code/UI   [CF] = Code-First   [LC/CF] = Both   [Portal] = Fabric Portal only
```

## Deployment Order

```
┌───────┬──────────────────┬──────────┬────────────────────────┬────────────────────┐
│ Order │ Item Type        │ Skillset │ Depends On             │ Required For       │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   1   │ Lakehouse or     │ [LC/CF]  │ (none - foundation)    │ Semantic Model     │
│       │ Warehouse        │          │ Deploy via another     │                    │
│       │                  │          │ task flow if needed    │                    │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   2   │ Semantic Model   │ [LC/CF]  │ Storage (populated)    │ Data Agent         │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   3   │ Data Agent       │ [Portal] │ Semantic Model         │ (end-user access)  │
│       │                  │          │ ⚠ Portal-only: create  │                    │
│       │                  │          │ in Fabric workspace UI │                    │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   4a  │ Ontology         │ [Portal] │ (optional)             │ (optional)         │
│       │                  │          │ ⚠ Portal-only          │                    │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   4b  │ Activator        │ [LC]     │ Data Agent or          │ (optional)         │
│       │                  │          │ Semantic Model         │                    │
└───────┴──────────────────┴──────────┴────────────────────────┴────────────────────┘
```

## Integration with Other Task Flows

Conversational analytics is an **overlay pattern** — it adds an AI consumption layer on top of existing data pipelines:

| Underlying Task Flow | What It Provides | What This Flow Adds |
|---|---|---|
| basic-data-analytics | Warehouse + ingestion + Semantic Model | Data Agent on top of existing Semantic Model |
| medallion | Lakehouse layers + curated Gold zone | Data Agent querying the Gold semantic layer |
| data-analytics-sql-endpoint | Lakehouse + SQL analytics | Data Agent for natural language SQL queries |
| Any flow with Semantic Model | Structured, modeled data | Natural language access for non-technical users |
