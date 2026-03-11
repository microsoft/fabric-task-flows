---
id: storage-selection
title: Storage Type Selection
---

# Storage Type Selection

> Choose the right Fabric storage type based on your query language, schema requirements, and workload patterns.

## Comparison Table

| Criteria | Lakehouse | Warehouse | Eventhouse | SQL Database | Cosmos DB | PostgreSQL |
|----------|-----------|-----------|------------|--------------|-----------|------------|
| **Query Language** | Spark, Python, SQL (read-only) | T-SQL | KQL | T-SQL | NoSQL API, SQL-like | PostgreSQL SQL |
| **Schema Approach** | Schema-on-read | Schema-on-write | Schema-on-write | Schema-on-write | Schema-less (document) | Schema-on-write |
| **Data Format** | Delta Lake (Parquet) | Relational tables | Columnar time-series | Relational tables | JSON documents | Relational tables |
| **Best For** | ML, Data Science, exploration | BI, Reporting, stored procs | Real-time, IoT, logs | Transactional apps, writeback | Semi-structured, AI/vector, high-concurrency | Open-source, geospatial |
| **Access Pattern** | Read-heavy analytics | Read-write analytical | Append-heavy, time-windowed | OLTP read-write | Read-write, document | OLTP read-write |
| **Time Travel** | ✅ Built-in versioning | ❌ No | ✅ Retention policies | ❌ No | ❌ No | ❌ No |
| **Stored Procedures** | ❌ No | ✅ T-SQL procs | ❌ No | ✅ T-SQL procs | ❌ No (use UDFs instead) | ✅ PL/pgSQL |
| **Real-Time Ingestion** | Via Eventstream | Limited | ✅ Native | Limited | Limited | Limited |
| **Semantic Model** | ✅ Direct Lake mode | ✅ Direct Lake / Import / DirectQuery | ✅ DirectQuery | ✅ DirectQuery (via OneLake mirroring: Direct Lake) | ✅ Direct Lake (via OneLake mirror) | ✅ DirectQuery |

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
