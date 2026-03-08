# Semantic Governance Diagrams

## Deployment Flow

<!-- AGENT: Skip to "## Deployment Order" for structured item/wave data. The visual diagram below is for human reference. -->

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
│  │    Ontology     │ ◄── Portal-only: define business terms, domains,          │
│  │    [Portal]     │     and relationships in Fabric workspace UI              │
│  └────────┬────────┘                                                            │
│           │                                                                    │
│           ▼                                                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 4: KNOWLEDGE GRAPH (Build Graph)                                         │
│  ══════════════════════════════════════                                         │
│  ┌─────────────────┐         ┌─────────────────┐                                │
│  │   Graph Model   │ ──────► │ Graph Queryset  │                                │
│  │    [Portal]     │         │    [Portal]     │                                │
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
│  │    [Portal]     │         │      [LC]       │                                │
│  │ (Chat over      │         │ (Governance     │                                │
│  │  governed data) │         │  dashboards)    │                                │
│  └─────────────────┘         └─────────────────┘                                │
└─────────────────────────────────────────────────────────────────────────────────┘

Legend: [LC] = Low-Code/UI   [CF] = Code-First   [LC/CF] = Both   [Portal] = Fabric Portal only
```

## Deployment Order

```
┌───────┬──────────────────┬──────────┬────────────────────────┬────────────────────┐
│ Order │ Item Type        │ Skillset │ Depends On             │ Required For       │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   1   │ Lakehouse        │ [LC/CF]  │ (none - foundation)    │ Semantic Model,    │
│       │                  │          │ May already exist from │ Graph Model        │
│       │                  │          │ another task flow      │                    │
│   1   │ Variable Library │ [LC]     │ (depends on: none)     │ Stage-specific config (if multi-env) │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   2   │ Semantic Model   │ [LC/CF]  │ Lakehouse (or          │ Ontology,          │
│       │                  │          │ Warehouse/SQL DB)      │ Data Agent         │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   3   │ Ontology         │ [Portal] │ Semantic Model         │ Graph Model        │
│       │                  │          │ ⚠ Portal-only: create  │                    │
│       │                  │          │ in Fabric workspace UI │                    │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   4   │ Graph Model      │ [Portal] │ Ontology               │ Graph Queryset     │
│       │                  │          │ ⚠ Portal-only          │                    │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   5   │ Graph Queryset   │ [Portal] │ Graph Model            │ (consumption)      │
│       │                  │          │ ⚠ Portal-only          │                    │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   6a  │ Data Agent       │ [Portal] │ Semantic Model +       │ (optional)         │
│       │                  │          │ Ontology               │                    │
│       │                  │          │ ⚠ Portal-only          │                    │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   6b  │ Report           │ [LC]     │ Semantic Model         │ (optional)         │
│       │                  │          │                        │ Governance         │
│       │                  │          │                        │ dashboards         │
└───────┴──────────────────┴──────────┴────────────────────────┴────────────────────┘
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
