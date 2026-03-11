---
id: processing-selection
title: Processing Method Selection
description: Choose the right data processing method based on interactivity needs, scheduling requirements, and team workflow
triggers:
  - "notebook vs spark job"
  - "how to process data"
  - "transformation method"
  - "spark job definition"
  - "dataflow vs notebook"
  - "code vs low-code processing"
options:
  - id: notebook
    label: Notebook
    criteria:
      mode: interactive development
      skillset: code-first
      scheduling: via pipeline or manual
      best_for: ["exploration", "ad-hoc analysis", "ML development", "complex transformations"]
  - id: spark-job-definition
    label: Spark Job Definition
    criteria:
      mode: production scheduled
      skillset: code-first
      scheduling: built-in or pipeline
      best_for: ["scheduled ETL", "production pipelines", "parameterized jobs"]
  - id: dataflow-gen2
    label: Dataflow Gen2
    criteria:
      mode: visual design
      skillset: low-code
      scheduling: built-in or pipeline
      best_for: ["business user ETL", "Power Query transformations", "simple data prep"]
  - id: kql-queryset
    label: KQL Queryset
    criteria:
      mode: interactive or materialized
      skillset: code-first (KQL)
      scheduling: via update policies
      best_for: ["time-series analysis", "real-time aggregations", "log analytics"]
  - id: stored-procedures
    label: Stored Procedures (Warehouse)
    criteria:
      mode: T-SQL scripts
      skillset: code-first (SQL)
      scheduling: via pipeline
      best_for: ["SQL-based transformations", "Warehouse processing", "traditional DW patterns"]
quick_decision: |
  Interactive + Python/Spark → Notebook
  Interactive + KQL → KQL Queryset
  Interactive + visual/no-code → Dataflow Gen2
  Production Spark + CI/CD → Spark Job Definition
  Production Spark + simple schedule → Notebook (via Pipeline)
  Production T-SQL → Stored Procedures
  Production KQL → KQL Queryset (update policies)
  Production Power Query → Dataflow Gen2
---

# Processing Method Selection

> Choose the right method to transform and process data based on your interactivity needs, scheduling requirements, and team skills.

## Comparison Table

| Criteria | Notebook | Spark Job Def | Dataflow Gen2 | KQL Queryset | Stored Procs |
|----------|----------|---------------|---------------|--------------|--------------|
| **Mode** | Interactive | Scheduled | Visual | Interactive/Auto | Script |
| **Skillset** | Code-First [CF] | Code-First [CF] | Low-Code [LC] | Code-First [CF] | Code-First [CF] |
| **Language** | Python, Spark SQL, Scala | Python, Spark SQL, Scala | Power Query M | KQL | T-SQL |
| **Scheduling** | Via Pipeline | Built-in + Pipeline | Built-in | Update Policies | Via Pipeline |
| **Parameters** | Cell inputs | Formal parameters | Limited | Query params | Procedure args |
| **Git Integration** | ✅ Full | ✅ Full | Limited | ✅ Full | ✅ Full |
| **Debugging** | ✅ Interactive | ❌ Log-based | Limited | ✅ Interactive | ❌ Log-based |
| **Best Scale** | Dev → Prod | Production | Small-Medium | Time-series | Medium-Large |

## Processing Workflow Patterns

### Medallion Architecture Processing

| Layer | Recommended Method | Rationale |
|-------|-------------------|-----------|
| Bronze → Silver | Notebook OR Spark Job | Complex cleansing, deduplication |
| Silver → Gold | Notebook OR Spark Job | Aggregations, business logic |
| Gold maintenance | Stored Procedures (if Warehouse) | SQL-based updates |

### Combining Processing Methods

| Pattern | Processing Combination | Use Case |
|---------|------------------------|----------|
| **Code-First ETL** | Notebook → Spark Job Def | Full Spark-based pipeline |
| **Hybrid ETL** | Dataflow Gen2 + Notebook | Ingest with DFG2, transform with Notebook |
| **SQL + Spark** | Notebook + Stored Procs | Spark for heavy lifting, SQL for final merge |
| **Real-time + Batch** | KQL Queryset + Notebook | Real-time aggs + historical analysis |

## Environment Requirements

| Processing Method | Requires Environment? | Notes |
|-------------------|----------------------|-------|
| Notebook | ✅ Yes | Spark Environment for libraries |
| Spark Job Definition | ✅ Yes | Same environment as notebooks |
| Dataflow Gen2 | ❌ No | Self-contained compute |
| KQL Queryset | ❌ No | Eventhouse compute |
| Stored Procedures | ❌ No | Warehouse compute |

## Anti-Patterns

| Don't Do This | Why | Do This Instead |
|---------------|-----|-----------------|
| Use Notebook for simple Power Query transforms | Overkill, slower setup | Use Dataflow Gen2 |
| Debug in Spark Job Definitions | No interactive debugging | Debug in Notebook first |
| Use Stored Procs for ML training | T-SQL not designed for ML | Use Notebook with Python |
| Run heavy Spark jobs in Dataflow Gen2 | Not optimized for Spark | Use Notebook or Spark Job Def |

## Related Decisions

- [Storage Selection](storage-selection.md) - Where to store processed data
- [Ingestion Selection](ingestion-selection.md) - How data arrives before processing
- [Skillset Selection](skillset-selection.md) - Code-First vs Low-Code capabilities
