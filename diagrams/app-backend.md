# App Backend Diagrams

## Deployment Flow

<!-- AGENT: Skip to "## Deployment Order" for structured item/wave data. The visual diagram below is for human reference. -->

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       APP BACKEND ARCHITECTURE DEPLOYMENT                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 1: FOUNDATION (Transactional Storage)                                    │
│  ════════════════════════════════════════════                                   │
│  ┌───────────────────┐     OR     ┌───────────────────┐                         │
│  │   SQL Database    │            │   Cosmos DB       │                         │
│  │      [LC]         │            │      [LC]         │                         │
│  │  (relational)     │            │  (NoSQL/document) │                         │
│  └─────────┬─────────┘            └─────────┬─────────┘                         │
│            │                                │                                   │
│            └────────────┬───────────────────┘                                   │
│                         │                                                       │
│                         ▼                                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 1b: CONFIGURATION (Optional)                                             │
│  ════════════════════════════════════════════                                   │
│  ┌───────────────────┐                                                          │
│  │ Variable Library  │ ◄── Stage-specific config (Dev/PPE/Prod)                 │
│  │      [LC]         │     Item references, connection params                   │
│  └─────────┬─────────┘                                                          │
│            │                                                                    │
│            ▼                                                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 2: API LAYER                                                             │
│  ════════════════════════════════════════════                                   │
│  ┌───────────────────┐         ┌───────────────────┐                            │
│  │   GraphQL API     │         │  User Data Funcs  │                            │
│  │      [LC]         │         │      [CF]         │                            │
│  │  (auto-schema)    │         │  (REST endpoints) │                            │
│  │  reads from DB    │         │  reads + writes   │                            │
│  └─────────┬─────────┘         └─────────┬─────────┘                            │
│            │                             │                                      │
│            └──────────┬──────────────────┘                                      │
│                       │                                                         │
│                       ▼                                                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 3: ANALYTICS (Optional)                                                  │
│  ════════════════════════════════════════════                                   │
│  ┌───────────────────┐                                                          │
│  │  Semantic Model   │ ◄── Connect to DB (auto-mirrored to OneLake)             │
│  │     [LC/CF]       │                                                          │
│  └─────────┬─────────┘                                                          │
│            │                                                                    │
│            ▼                                                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 4: CONSUMPTION (Optional)                                                │
│  ════════════════════════════════════════════                                   │
│  ┌───────────────────┐         ┌───────────────────┐                            │
│  │      Report       │         │    Data Agent     │                            │
│  │       [LC]        │         │      [LC]         │                            │
│  │  admin dashboard  │         │  conversational   │                            │
│  └───────────────────┘         └───────────────────┘                            │
│                                                                                 │
│  ┌───────────────────┐                                                          │
│  │    Ontology       │ ◄── Cross-domain vocabulary (optional)                   │
│  │      [LC]         │                                                          │
│  └───────────────────┘                                                          │
└─────────────────────────────────────────────────────────────────────────────────┘

Legend: [LC] = Low-Code/UI   [CF] = Code-First   [LC/CF] = Either
```

## Deployment Order

```
┌───────┬──────────────────┬──────────┬────────────────────────┬────────────────────┐
│ Order │ Item Type        │ Skillset │ Depends On             │ Required For       │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│  1a   │ SQL Database     │ [LC]     │ (none — foundation)    │ GraphQL API,       │
│       │  OR Cosmos DB    │          │                        │ User Data Functions│
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│  1b   │ Variable Library │ [LC]     │ (none — optional)      │ Stage config       │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│  2a   │ GraphQL API      │ [LC]     │ SQL Database/Cosmos DB │ App reads          │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│  2b   │ User Data Funcs  │ [CF]     │ SQL Database/Cosmos DB │ App writes, logic  │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│  3    │ Semantic Model   │ [LC/CF]  │ SQL Database/Cosmos DB │ Report             │
│       │                  │          │ (via OneLake mirror)   │                    │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│  4a   │ Report           │ [LC]     │ Semantic Model         │ Admin dashboard    │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│  4b   │ Data Agent       │ [LC]     │ SQL Database/Cosmos DB │ Conversational AI  │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│  4c   │ Ontology         │ [LC]     │ Semantic Model         │ Cross-domain vocab │
└───────┴──────────────────┴──────────┴────────────────────────┴────────────────────┘
```

## Storage Decision: SQL Database vs Cosmos DB

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      STORAGE: SQL DATABASE vs COSMOS DB                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Choose SQL DATABASE when:              Choose COSMOS DB when:                  │
│  ═══════════════════════               ═══════════════════════                  │
│  • Relational data model               • Semi-structured / document data        │
│  • ACID transactions required           • Schema-less / evolving data models    │
│  • T-SQL / stored procedures            • AI workloads (vector search, RAG)     │
│  • Foreign key constraints              • Limitless auto-scaling needed          │
│  • Existing Azure SQL apps              • NoSQL API compatibility               │
│  • CRUD with strict schema              • High-concurrency serving layer         │
│                                                                                 │
│  Both provide:                                                                  │
│  • Automatic OneLake mirroring (Delta format)                                   │
│  • Cross-database queries with other Fabric items                               │
│  • GraphQL API support                                                          │
│  • Power BI / Semantic Model integration                                        │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```
