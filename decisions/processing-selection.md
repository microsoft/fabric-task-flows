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
---

# Processing Method Selection

> Choose the right method to transform and process data based on your interactivity needs, scheduling requirements, and team skills.

## Quick Decision Tree

```
What's your PRIMARY use case?
│
├─► Interactive exploration / development
│   │
│   ├─► Python/Spark code ───────────────────► NOTEBOOK
│   │
│   ├─► KQL (time-series) ───────────────────► KQL QUERYSET
│   │
│   └─► Visual / no-code ────────────────────► DATAFLOW GEN2
│
└─► Production / scheduled processing
    │
    ├─► Spark/Python transformations
    │   │
    │   ├─► Need parameters, CI/CD ──────────► SPARK JOB DEFINITION
    │   │
    │   └─► Simple scheduled notebook ───────► NOTEBOOK (via Pipeline)
    │
    ├─► T-SQL transformations (Warehouse) ───► STORED PROCEDURES
    │
    ├─► KQL materialized views ──────────────► KQL QUERYSET (update policies)
    │
    └─► Power Query transformations ─────────► DATAFLOW GEN2
```

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

## When to Choose Each

### Choose NOTEBOOK when:

- ✅ You need **interactive, cell-by-cell development**
- ✅ **Exploratory analysis** before production code
- ✅ **Machine learning** development and experimentation
- ✅ Complex transformations requiring **debugging**
- ✅ You want **visualizations** inline with code
- ✅ **Ad-hoc analysis** that may become scheduled later

**Example Use Cases:**
- Medallion Bronze → Silver → Gold transformations
- ML feature engineering and model training
- Data quality analysis and profiling
- Complex joins and aggregations with debugging

**Production Pattern:**
```
Notebook (development) → Pipeline (scheduling) → Monitoring
```

### Choose SPARK JOB DEFINITION when:

- ✅ Job is **production-ready** and tested
- ✅ You need **formal parameterization** for different environments
- ✅ **CI/CD pipelines** will deploy the job
- ✅ No interactive debugging needed
- ✅ **Scheduled execution** without Pipeline overhead
- ✅ Reusable job across multiple schedules/triggers

**Example Use Cases:**
- Scheduled ETL jobs running on cron
- Parameterized data processing (dev/test/prod)
- CI/CD deployed Spark applications
- Batch aggregation jobs

**When to Promote Notebook → Spark Job Definition:**
```
Development Complete → Tests Pass → Remove Debug Code → Create Spark Job Def
```

### Choose DATAFLOW GEN2 when:

- ✅ **Business users** will maintain transformations
- ✅ Transformations are **Power Query compatible**
- ✅ You want **visual, drag-and-drop** data prep
- ✅ No Spark/Python skills available
- ✅ Data volumes are **small to medium**
- ✅ Quick ETL without environment setup

**Example Use Cases:**
- Business user data cleansing
- Department-level data prep
- Excel-style transformations (pivot, unpivot, merge)
- Quick prototypes before notebook development

### Choose KQL QUERYSET when:

- ✅ Data is in **Eventhouse or KQL Database**
- ✅ Processing **time-series data** (logs, IoT, telemetry)
- ✅ Need **real-time aggregations** via update policies
- ✅ Team knows **KQL (Kusto Query Language)**
- ✅ Creating **materialized views** for dashboards

**Example Use Cases:**
- Real-time event aggregations
- Log analysis and pattern detection
- IoT sensor data processing
- Time-windowed analytics

### Choose STORED PROCEDURES when:

- ✅ Data is in **Warehouse**
- ✅ Team is experienced with **T-SQL**
- ✅ Need **SQL-based transformations** with ACID
- ✅ Traditional **data warehouse patterns** (SCD, merge, etc.)
- ✅ Want to leverage **SQL Server skills**

**Example Use Cases:**
- Slowly Changing Dimensions (SCD Type 2)
- MERGE operations for upserts
- SQL-based aggregations to gold tables
- Legacy DW pattern migration

## Processing Workflow Patterns

### Medallion Architecture Processing

| Layer | Recommended Method | Rationale |
|-------|-------------------|-----------|
| Bronze → Silver | Notebook OR Spark Job | Complex cleansing, deduplication |
| Silver → Gold | Notebook OR Spark Job | Aggregations, business logic |
| Gold maintenance | Stored Procedures (if Warehouse) | SQL-based updates |

### Development to Production Path

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROCESSING LIFECYCLE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. EXPLORE         2. DEVELOP           3. PRODUCTION         │
│  ───────────        ──────────           ────────────          │
│  Notebook           Notebook             Spark Job Def         │
│  (ad-hoc cells)     (structured code)    (parameterized)       │
│                                          OR                     │
│                                          Pipeline + Notebook    │
│                                                                 │
│  ► Quick iteration  ► Unit tests         ► Scheduled           │
│  ► Visualizations   ► Error handling     ► Monitored           │
│  ► Debug            ► Parameterization   ► CI/CD deployed      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

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
