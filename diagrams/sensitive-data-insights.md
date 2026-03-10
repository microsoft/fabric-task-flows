# Sensitive Data Insights Diagrams

## Deployment Flow

<!-- AGENT: Use _shared/registry/deployment-order.json for deployment order data. This visual diagram is for human reference. -->

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    SENSITIVE DATA INSIGHTS DEPLOYMENT                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 1: FOUNDATION (Secured Storage)                                          │
│  ════════════════════════════════════════                                       │
│  Deploy storage with strict access controls:                                    │
│                                                                                 │
│  ┌─────────────────┐                 ┌─────────────────┐                        │
│  │   Lakehouse     │────────────────►│   Warehouse     │                        │
│  │  (Raw + Masked) │                 │  (Aggregated)   │                        │
│  │     [LC]        │                 │     [LC]        │                        │
│  │  ⚠️ RLS/CLS     │                 │  ⚠️ RLS/CLS     │                        │
│  └────────┬────────┘                 └─────────────────┘                        │
│           │                                                                     │
│           ▼                                                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 2: COMPUTE ENVIRONMENT (Isolated)                                        │
│  ════════════════════════════════════════                                       │
│  ┌──────────────┐                                                               │
│  │ Environment  │ ◄── Configure with restricted network access                  │
│  │    [CF]      │                                                               │
│  └──────┬───────┘                                                               │
│         │                                                                       │
│         ▼                                                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 3: SECURE INGESTION                                                      │
│  ════════════════════════════════                                               │
│  Use managed identities, encrypt in transit:                                    │
│                                                                                 │
│  ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐   │
│  │    Copy Job     │   OR    │  Dataflow Gen2  │   OR    │    Pipeline     │   │
│  │   [LC] Basic    │         │  [LC] Masked    │         │  [LC/CF] Orch   │   │
│  │  🔐 Encrypt     │         │  🔐 Transform   │         │  🔐 Controlled  │   │
│  └────────┬────────┘         └────────┬────────┘         └────────┬────────┘   │
│           │                           │                           │             │
│           └───────────────────────────┴───────────────────────────┘             │
│                                       │                                         │
│                                       ▼                                         │
│                            ┌───────────────────┐                                │
│                            │     Lakehouse     │                                │
│                            │  (with masking)   │                                │
│                            └─────────┬─────────┘                                │
│                                      │                                          │
│                                      ▼                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 4: SECURE TRANSFORMATION                                                 │
│  ════════════════════════════════════════════════════                           │
│  Apply data masking, PII redaction, tokenization:                               │
│                                                                                 │
│  ┌─────────────────────┐              ┌─────────────────────┐                   │
│  │      Notebook       │      OR      │  Spark Job Def      │                   │
│  │   [CF] Masking      │              │   [CF] Scheduled    │                   │
│  │   🔐 PII Redaction  │              │   🔐 Anonymization  │                   │
│  └──────────┬──────────┘              └──────────┬──────────┘                   │
│             │                                    │                              │
│             └────────────────┬───────────────────┘                              │
│                              │                                                  │
│                              ▼                                                  │
│                    ┌───────────────────┐                                        │
│                    │     Lakehouse     │                                        │
│                    │   (anonymized)    │                                        │
│                    └─────────┬─────────┘                                        │
│                              │                                                  │
│                              ▼                                                  │
│                    ┌───────────────────┐                                        │
│                    │     Warehouse     │                                        │
│                    │   (aggregated)    │                                        │
│                    └─────────┬─────────┘                                        │
│                              │                                                  │
│                              ▼                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 5: SECURE VISUALIZATION                                                  │
│  ════════════════════════════════════════════════════                           │
│  Apply Row-Level Security (RLS) and Object-Level Security (OLS):                │
│                                                                                 │
│                    ┌───────────────────┐                                        │
│                    │   Semantic Model  │                                        │
│                    │     [LC/CF]       │                                        │
│                    │   🔐 RLS/OLS      │                                        │
│                    └─────────┬─────────┘                                        │
│                              │                                                  │
│                              ▼                                                  │
│                     ┌─────────────┐                                              │
│                     │   Report    │                                              │
│                     │    [LC]     │                                              │
│                     └─────────────┘                                              │
└─────────────────────────────────────────────────────────────────────────────────┘

Legend: [LC] = Low-Code/UI   [CF] = Code-First   🔐 = Security control
```

## Security Decision

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    SENSITIVE DATA: SECURITY CONTROLS                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─ What type of data protection do you need? ────────────────────────────────┐ │
│  │                                                                            │ │
│  │  Row-Level Security ──► RLS in Semantic Model                              │ │
│  │                         • Filter rows by user identity                     │ │
│  │                                                                            │ │
│  │  Column-Level Security ──► CLS in Warehouse / OLS in Semantic Model        │ │
│  │                            • Hide columns from unauthorized users          │ │
│  │                                                                            │ │
│  │  Data Masking ──► Notebook transformation                                  │ │
│  │                   • Hash, tokenize, or redact PII                          │ │
│  │                                                                            │ │
│  │  Aggregation ──► Warehouse (no row-level detail)                           │ │
│  │                  • Only show aggregated metrics                            │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```
