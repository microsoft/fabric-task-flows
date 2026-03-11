---
id: processing-selection
title: Processing Method Selection
---

# Processing Method Selection

> Choose the right method to transform and process data based on your interactivity needs, scheduling requirements, and team skills.

## Comparison Table

| Criteria | Notebook | Spark Job Def | Dataflow Gen2 | KQL Queryset | Stored Procs |
|----------|----------|---------------|---------------|--------------|--------------|
| **Mode** | Interactive | Scheduled | Visual | Interactive/Auto | Script |
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
