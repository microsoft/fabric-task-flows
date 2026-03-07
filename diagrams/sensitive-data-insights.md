# Sensitive Data Insights Diagrams

## Deployment Flow

<!-- AGENT: Skip to "## Deployment Order" for structured item/wave data. The visual diagram below is for human reference. -->

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
│                    ┌─────────┴─────────┐                                        │
│                    ▼                   ▼                                        │
│           ┌─────────────┐      ┌─────────────┐                                  │
│           │   Report    │      │  Dashboard  │                                  │
│           │    [LC]     │      │    [LC]     │                                  │
│           └─────────────┘      └─────────────┘                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

Legend: [LC] = Low-Code/UI   [CF] = Code-First   🔐 = Security control
```

## Deployment Order

```
┌───────┬──────────────────┬──────────┬────────────────────────┬────────────────────┐
│ Order │ Item Type        │ Skillset │ Depends On             │ Required For       │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   1a  │ Lakehouse (raw)  │ [LC]     │ (none - foundation)    │ Ingestion          │
│   1b  │ Lakehouse (mask) │ [LC]     │ (none - foundation)    │ Anonymized data    │
│   1c  │ Warehouse        │ [LC]     │ (none - foundation)    │ Aggregated layer   │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   2   │ Environment      │ [CF]     │ Lakehouses             │ Notebooks, Spark   │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   3a  │ Copy Job         │ [LC]     │ Lakehouse (raw)        │ Raw data           │
│   3b  │ Dataflow Gen2    │ [LC]     │ Lakehouse (raw)        │ Masked ingestion   │
│   3c  │ Pipeline         │ [LC/CF]  │ Lakehouse (raw)        │ Orchestrated load  │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   4a  │ Notebook         │ [CF]     │ Environment, Lakehouse │ Masking logic      │
│   4b  │ Spark Job Def    │ [CF]     │ Environment, Lakehouse │ Scheduled masking  │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   5   │ Semantic Model   │ [LC/CF]  │ Warehouse              │ Secured reports    │
├───────┼──────────────────┼──────────┼────────────────────────┼────────────────────┤
│   6a  │ Report           │ [LC]     │ Semantic Model         │ Dashboard          │
│   6b  │ Dashboard        │ [LC]     │ Report(s)              │ (optional)         │
└───────┴──────────────────┴──────────┴────────────────────────┴────────────────────┘
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
