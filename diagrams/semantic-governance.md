# Semantic Governance Diagrams

## Deployment Flow

<!-- AGENT: Use _shared/registry/deployment-order.json for deployment order data. This visual diagram is for human reference. -->

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      SEMANTIC GOVERNANCE DEPLOYMENT                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 1: FOUNDATION (Storage)                                                  │
│  ════════════════════════════════                                               │
│  ┌─────────────┐                                                                │
│  │  Lakehouse  │ ◄── Central metadata store; may already exist                 │
│  │   [LC/CF]   │     from another task flow                                    │
│  └──────┬──────┘                                                                │
│         │                                                                       │
│         ▼                                                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 2: SEMANTIC LAYER                                                        │
│  ════════════════════════                                                      │
│  ┌─────────────────┐                                                            │
│  │  Semantic Model │ ◄── Defines measures, relationships, business logic       │
│  │    [LC/CF]      │     Binds governance vocabulary to physical data          │
│  └────────┬────────┘                                                            │
│           │                                                                    │
│           ▼                                                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 3: ONTOLOGY (Define Vocabulary)                                          │
│  ═════════════════════════════════════                                          │
│  ┌─────────────────┐                                                            │
│  │    Ontology     │ ◄── Define business terms, domains,                       │
│  │      [LC]       │     and relationships                                     │
│  └────────┬────────┘                                                            │
│           │                                                                    │
│           ▼                                                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 4: KNOWLEDGE GRAPH (Build Graph)                                         │
│  ══════════════════════════════════════                                         │
│  ┌─────────────────┐         ┌─────────────────┐                                │
│  │   Graph Model   │ ──────► │ Graph Queryset  │                                │
│  │      [LC]       │         │    [Portal]     │                                │
│  │ (Entity/edge    │         │ (Query graph    │                                │
│  │  definitions)   │         │  relationships) │                                │
│  └─────────────────┘         └─────────────────┘                                │
│           │                          │                                          │
│           └──────────┬───────────────┘                                          │
│                      ▼                                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 5: CONSUMPTION (Optional)                                                │
│  ═══════════════════════════════                                               │
│  ┌─────────────────┐         ┌─────────────────┐                                │
│  │   Data Agent    │         │     Report      │                                │
│  │      [LC]       │         │      [LC]       │                                │
│  │ (Chat over      │         │ (Governance     │                                │
│  │  governed data) │         │  dashboards)    │                                │
│  └─────────────────┘         └─────────────────┘                                │
└─────────────────────────────────────────────────────────────────────────────────┘

Legend: [LC] = Low-Code/UI   [CF] = Code-First   [LC/CF] = Both   [Portal] = Fabric Portal only (Graph Queryset)
```

## Integration with Other Task Flows

Semantic governance is a **governance layer** that enhances existing data pipelines with enterprise vocabulary and knowledge graph capabilities:

| Underlying Task Flow | What It Provides | What This Flow Adds |
|---|---|---|
| medallion | Curated Gold zone with semantic model | Business vocabulary, knowledge graph over Gold data |
| basic-data-analytics | Warehouse with semantic model | Governed business terms, lineage context |
| data-analytics-sql-endpoint | SQL analytics with semantic model | Unified vocabulary across SQL endpoints |
| Any flow with data governance needs | Structured data | Enterprise-wide semantic consistency |

## External Integration

| External Tool | Integration Pattern | Purpose |
|---|---|---|
| Microsoft Purview | Catalog sync via Purview hub | Classification, lineage, data catalog |
| Power BI | Semantic Model endorsement | Certified datasets with governed vocabulary |
| Azure OpenAI | Ontology-informed prompts | AI that understands business terminology |
