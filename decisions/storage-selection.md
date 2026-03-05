---
id: storage-selection
title: Storage Type Selection
description: Choose the right storage type based on query language, schema approach, and workload patterns
triggers:
  - "lakehouse vs warehouse"
  - "where to store data"
  - "storage choice"
  - "eventhouse vs lakehouse"
  - "which database"
options:
  - id: lakehouse
    label: Lakehouse
    criteria:
      query_language: ["Spark", "Python", "SQL (read-only via endpoint)"]
      schema_approach: schema-on-read
      data_format: Delta Lake (Parquet)
      best_for: ["ML/Data Science", "exploratory analysis", "large-scale processing"]
      access_pattern: read-heavy
      cost_profile: lower compute cost
  - id: warehouse
    label: Warehouse
    criteria:
      query_language: ["T-SQL"]
      schema_approach: schema-on-write
      data_format: relational tables
      best_for: ["BI/Reporting", "stored procedures", "traditional DW"]
      access_pattern: read-write transactional
      cost_profile: optimized query engine
  - id: eventhouse
    label: Eventhouse
    criteria:
      query_language: ["KQL (Kusto Query Language)"]
      schema_approach: schema-on-write (optimized for time-series)
      data_format: columnar time-series
      best_for: ["real-time analytics", "IoT", "logs", "telemetry"]
      access_pattern: append-heavy, time-windowed queries
      cost_profile: optimized for high-volume ingestion
  - id: sql-database
    label: SQL Database
    criteria:
      query_language: ["T-SQL"]
      schema_approach: schema-on-write (ACID)
      data_format: relational tables
      best_for: ["transactional apps", "operational data", "writeback"]
      access_pattern: OLTP read-write
      cost_profile: transaction-optimized
  - id: postgresql
    label: PostgreSQL
    criteria:
      query_language: ["PostgreSQL SQL"]
      schema_approach: schema-on-write
      data_format: relational tables
      best_for: ["open-source compatibility", "app backends", "geospatial"]
      access_pattern: OLTP read-write
      cost_profile: flexible scaling
---

# Storage Type Selection

> Choose the right Fabric storage type based on your query language, schema requirements, and workload patterns.

## Quick Decision Guide

```
What's your PRIMARY query language?
│
├─► Spark/Python ──────────────────► LAKEHOUSE
│
├─► T-SQL (analytics) ─────────────► WAREHOUSE
│
├─► T-SQL (transactional) ─────────► SQL DATABASE
│
├─► KQL (time-series) ─────────────► EVENTHOUSE
│
└─► PostgreSQL ────────────────────► POSTGRESQL
```

## Comparison Table

| Criteria | Lakehouse | Warehouse | Eventhouse | SQL Database | PostgreSQL |
|----------|-----------|-----------|------------|--------------|------------|
| **Query Language** | Spark, Python, SQL (read-only) | T-SQL | KQL | T-SQL | PostgreSQL SQL |
| **Schema Approach** | Schema-on-read | Schema-on-write | Schema-on-write | Schema-on-write | Schema-on-write |
| **Data Format** | Delta Lake (Parquet) | Relational tables | Columnar time-series | Relational tables | Relational tables |
| **Best For** | ML, Data Science, exploration | BI, Reporting, stored procs | Real-time, IoT, logs | Transactional apps, writeback | Open-source, geospatial |
| **Access Pattern** | Read-heavy analytics | Read-write analytical | Append-heavy, time-windowed | OLTP read-write | OLTP read-write |
| **Time Travel** | ✅ Built-in versioning | ❌ No | ✅ Retention policies | ❌ No | ❌ No |
| **Stored Procedures** | ❌ No | ✅ T-SQL procs | ❌ No | ✅ T-SQL procs | ✅ PL/pgSQL |
| **Real-Time Ingestion** | Via Eventstream | Limited | ✅ Native | Limited | Limited |
| **Semantic Model** | ✅ Direct Lake mode | ✅ Direct Lake / Import / DirectQuery | ✅ DirectQuery | ✅ DirectQuery (via OneLake mirroring: Direct Lake) | ✅ DirectQuery |

## When to Choose Each

### Choose LAKEHOUSE when:

- ✅ Your team works primarily with **Spark, Python, or PySpark**
- ✅ You need **schema flexibility** for iterative development
- ✅ **Machine learning** and data science are primary use cases
- ✅ You want **Delta Lake features** (time travel, ACID transactions on files)
- ✅ Data volumes are large and **read-heavy**
- ✅ You prefer **lower compute costs** over query optimization
- ✅ You need to query **semi-structured data** (JSON, nested structures)

### Choose WAREHOUSE when:

- ✅ Your team is experienced with **T-SQL**
- ✅ You need **stored procedures, views, and functions**
- ✅ **BI reporting** is the primary consumption pattern
- ✅ You require **strict schema enforcement** from the start
- ✅ You need **read-write access** for data manipulation
- ✅ **Query performance** is more important than storage cost
- ✅ Business analysts are primary users (familiar with SQL Server)

### Choose EVENTHOUSE when:

- ✅ Data is **time-series** (IoT sensors, logs, telemetry, clickstreams)
- ✅ You need **sub-second query latency** on recent data
- ✅ **Real-time dashboards** are required
- ✅ Data arrives via **streaming** (Eventstream, Event Hubs)
- ✅ You're comfortable with **KQL (Kusto Query Language)**
- ✅ **High-volume ingestion** (millions of events per second)
- ✅ Queries focus on **time-windowed aggregations**

### Choose SQL DATABASE when:

- ✅ You need **OLTP transactional** capabilities
- ✅ Applications will **write data back** to the database
- ✅ You need **referential integrity** with foreign keys
- ✅ Use case is **operational/transactional** (not just analytics)
- ✅ You're building **translytical** patterns (operational + analytical)
- ✅ Power BI reports need **writeback** functionality

### Choose POSTGRESQL when:

- ✅ You need **open-source SQL** compatibility
- ✅ Application already uses **PostgreSQL**
- ✅ You need **geospatial queries** (PostGIS)
- ✅ Team prefers **PostgreSQL ecosystem** tools
- ✅ You want **flexible deployment** options

## Common Patterns

### Medallion Architecture (Bronze → Silver → Gold)

| Layer | Recommended Storage | Rationale |
|-------|---------------------|-----------|
| Bronze | Lakehouse | Raw data, schema flexibility, Delta Lake versioning |
| Silver | Lakehouse | Transformation flexibility, Spark processing |
| Gold | **Lakehouse OR Warehouse** | See [Gold Layer Decision](#gold-layer-decision) |

### Gold Layer Decision

```
┌─────────────────────────────────────────────────────────────────┐
│                    GOLD LAYER DECISION                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Choose LAKEHOUSE Gold when:    Choose WAREHOUSE Gold when:     │
│  • Spark/Python consumption     • T-SQL is primary language     │
│  • ML workloads on Gold data    • BI reporting focus            │
│  • Need Delta Lake features     • Need stored procedures        │
│  • Read-only SQL is sufficient  • Need read/write T-SQL         │
│  • Cost optimization priority   • Query performance priority    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Lambda Architecture (Batch + Real-Time)

| Path | Recommended Storage | Rationale |
|------|---------------------|-----------|
| Batch Layer | Lakehouse | Large-scale Spark processing |
| Speed Layer | Eventhouse | Real-time KQL analytics |
| Serving Layer | Warehouse OR Lakehouse | Depends on query language preference |

### Real-Time Analytics

| Pattern | Recommended Storage | Rationale |
|---------|---------------------|-----------|
| IoT/Sensor data | Eventhouse | Time-series optimized, KQL |
| Log analytics | Eventhouse | High-volume append, retention policies |
| Real-time dashboards | Eventhouse | Sub-second queries |

### Operational BI (Writeback)

| Pattern | Recommended Storage | Rationale |
|---------|---------------------|-----------|
| Data entry from reports | SQL Database | Transactional writeback |
| Feedback loops | SQL Database | OLTP + analytics |

## Anti-Patterns

| Don't Do This | Why | Do This Instead |
|---------------|-----|-----------------|
| Use Warehouse for ML training | T-SQL not optimized for ML | Use Lakehouse with Spark |
| Use Lakehouse for stored procedures | Not supported | Use Warehouse |
| Use SQL Database for large analytics | OLTP not optimized for analytics | Use Lakehouse or Warehouse |
| Use Eventhouse for batch-only data | Overhead without time-series benefit | Use Lakehouse |

## Related Decisions

- [Ingestion Selection](ingestion-selection.md) - How to get data into your chosen storage
- [Processing Selection](processing-selection.md) - How to transform data
- [Skillset Selection](skillset-selection.md) - Code-First vs Low-Code capabilities
