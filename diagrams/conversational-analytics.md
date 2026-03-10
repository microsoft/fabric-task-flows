# Conversational Analytics Diagrams

## Deployment Flow

<!-- AGENT: Use _shared/registry/deployment-order.json for deployment order data. This visual diagram is for human reference. -->

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
│  │   Data Agent    │ ◄── Configure and bind to Semantic Model                  │
│  │      [LC]       │     Set access controls, greeting prompts                 │
│  └────────┬────────┘                                                            │
│           │                                                                    │
│           ▼                                                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 4: OPTIONAL GOVERNANCE                                                   │
│  ════════════════════════════                                                  │
│  ┌─────────────────┐         ┌─────────────────┐                                │
│  │    Ontology     │         │    Activator    │                                │
│  │      [LC]       │         │      [LC]       │                                │
│  │ (Business       │         │ (Usage alerts)  │                                │
│  │  vocabulary)    │         │                 │                                │
│  └─────────────────┘         └─────────────────┘                                │
└─────────────────────────────────────────────────────────────────────────────────┘

Legend: [LC] = Low-Code/UI   [CF] = Code-First   [LC/CF] = Both
```

## Integration with Other Task Flows

Conversational analytics is an **overlay pattern** — it adds an AI consumption layer on top of existing data pipelines:

| Underlying Task Flow | What It Provides | What This Flow Adds |
|---|---|---|
| basic-data-analytics | Warehouse + ingestion + Semantic Model | Data Agent on top of existing Semantic Model |
| medallion | Lakehouse layers + curated Gold zone | Data Agent querying the Gold semantic layer |
| data-analytics-sql-endpoint | Lakehouse + SQL analytics | Data Agent for natural language SQL queries |
| Any flow with Semantic Model | Structured, modeled data | Natural language access for non-technical users |
