---
id: ingestion-selection
title: Ingestion Method Selection
---

# Ingestion Method Selection

> **Agents:** Use `decision-resolver.py` — do NOT read this file unless resolver returns ambiguous.

## Reference Matrix

| Tool | Volume | Velocity | Variety (Sources) | Transformation | Scheduling | Complexity |
|------|--------|----------|-------------------|----------------|------------|------------|
| **Copy Job** | Small → Large | Batch | 100+ connectors (DBs, files, APIs) | None | Built-in | Low |
| **Dataflow Gen2** | Small → Medium | Batch | 150+ connectors (DBs, files, SaaS) | Power Query (M) | Built-in | Low-Medium |
| **Pipeline** | Any | Batch | Activities + connectors + Notebooks | Orchestrates others | Advanced | Medium-High |
| **Notebook** | Large → Very Large | Batch | Custom code (any source) | Full code (Python/Spark) | Via Pipeline | High |
| **Eventstream** | Any (streaming) | Real-time | Event Hubs, Kafka, custom apps, IoT | Stream processing | Continuous | Medium |
| **Mirroring** | Any | Continuous CDC | Azure SQL, Azure SQL MI, Cosmos DB, Snowflake, Databricks, SQL Server 2025, MySQL (preview), PostgreSQL (preview) | None | Automatic | Low |
| **Shortcut** | Any | Always live (zero-copy) | ADLS Gen2, S3, GCS, cross-workspace Fabric items | None | N/A (always live) | Very Low |
| **Fabric Link** | Any | Continuous sync | Dataverse (Dynamics 365, Power Platform) | None | Automatic | Low |

## Combining Ingestion Methods

| Pattern | Ingestion Method | Orchestration |
|---------|------------------|---------------|
| **Simple batch load** | Copy Job alone | Built-in schedule |
| **Batch with transformation** | Dataflow Gen2 | Built-in schedule |
| **Orchestrated batch ETL** | Pipeline → Copy + Notebook | Pipeline schedule |
| **Real-time + batch (Lambda)** | Eventstream + Copy Job | Separate schedules |
| **Database replication** | Mirroring | Automatic |
| **Zero-copy data lake access** | Shortcut | None (always live) |
| **Dataverse / Dynamics 365** | Fabric Link | Automatic |
| **Custom source (no connector)** | Notebook (standalone) | Via Pipeline or manual |
| **Sensor/IoT batch (proprietary)** | Notebook (standalone) | Via Pipeline or manual |
| **Platform migration** | Copy Job + Pipeline (phased cutover) | Pipeline schedule |

## Anti-Patterns

| Don't Do This | Why | Do This Instead |
|---------------|-----|-----------------|
| Use Eventstream for batch data | Overhead, complexity for batch | Use Copy Job or Dataflow Gen2 |
| Build transformations in Pipeline activities | Hard to maintain | Use Dataflow Gen2 or Notebook |
| Use Dataflow Gen2 for > 1 GB transforms | Performance limits at scale | Use Notebook or Pipeline + Copy |
| Use Copy Job when you need complex joins | No transformation support | Use Dataflow Gen2 |
| Over-engineer small data with Notebooks | Unnecessary complexity | Use Dataflow Gen2 or Copy Job |
| Copy data already in ADLS/S3/GCS | Unnecessary duplication and cost | Use Shortcut for zero-copy access |
| Build ETL pipeline for Dataverse data | Unnecessary when Fabric Link exists | Use Fabric Link for zero-ETL sync |
| Use Shortcut when you need snapshots | Shortcuts are always live, no versioning | Use Copy Job for point-in-time copies |
| Skip monitoring setup | Silent failures, data freshness drift | Add Activator alerts from day one |

## Related Decisions

- [Storage Selection](storage-selection.md)
- [Processing Selection](processing-selection.md)
- [Skillset Selection](skillset-selection.md)
- [Visualization Selection](visualization-selection.md)
