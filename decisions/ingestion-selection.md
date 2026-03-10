---
id: ingestion-selection
title: Ingestion Method Selection
description: Choose the right data ingestion method based on the 4 V's — Volume, Velocity, Variety, and Versatility — plus transformation needs and orchestration requirements
triggers:
  - "copy job vs pipeline"
  - "dataflow vs pipeline"
  - "how to ingest data"
  - "eventstream vs copy job"
  - "batch vs streaming"
  - "data ingestion"
  - "4 V's"
  - "data movement strategy"
  - "volume velocity variety"
  - "shortcut vs copy job"
  - "ADLS Gen2"
  - "S3 data"
  - "existing data lake"
  - "zero-copy"
  - "data virtualization"
  - "Dataverse"
  - "Dynamics 365 data"
  - "Fabric Link"
  - "Link to Fabric"
  - "Power Platform data"
options:
  - id: copy-job
    label: Copy Job
    criteria:
      data_pattern: batch
      transformation: none (copy as-is)
      skillset: low-code
      orchestration: standalone or pipeline
      volume: small to large
      best_for: ["simple data movement", "scheduled refresh", "one-to-one copy"]
  - id: dataflow-gen2
    label: Dataflow Gen2
    criteria:
      data_pattern: batch
      transformation: Power Query (M)
      skillset: low-code
      orchestration: standalone or pipeline
      volume: small to medium
      best_for: ["visual transformations", "data cleansing", "business user ETL"]
  - id: pipeline
    label: Data Pipeline
    criteria:
      data_pattern: batch
      transformation: orchestration (calls other items)
      skillset: low-code and code-first
      orchestration: full orchestration engine
      volume: any
      best_for: ["complex workflows", "conditional logic", "multi-step ETL"]
  - id: eventstream
    label: Eventstream
    criteria:
      data_pattern: real-time streaming
      transformation: stream processing
      skillset: low-code
      orchestration: continuous
      volume: any (streaming)
      best_for: ["IoT", "logs", "real-time events", "Kafka"]
  - id: mirroring
    label: Mirroring
    criteria:
      data_pattern: continuous replication
      transformation: none (replicate as-is)
      skillset: low-code
      orchestration: automatic
      volume: any
      best_for: ["database replication", "CDC", "operational data sync"]
  - id: shortcut
    label: OneLake Shortcut
    criteria:
      data_pattern: zero-copy virtualization
      transformation: none (reference in place)
      skillset: low-code
      orchestration: none (always live)
      volume: any
      best_for: ["existing data lake", "ADLS Gen2", "S3", "GCS", "cross-workspace sharing"]
  - id: fabric-link
    label: Fabric Link (Dataverse)
    criteria:
      data_pattern: continuous sync
      transformation: none (sync as-is to Delta)
      skillset: low-code
      orchestration: automatic
      volume: any
      best_for: ["Dataverse analytics", "Dynamics 365 reporting", "Power Platform data"]
quick_decision: |
  Real-time streaming → Eventstream
  Database replication (CDC) → Mirroring
  Dataverse / Dynamics 365 source → Fabric Link
  Data already in ADLS/S3/GCS/OneLake → Shortcut
  Sensor/IoT data (proprietary formats) → Eventstream (streaming) or Notebook (batch)
  Small-medium + transforms needed → Dataflow Gen2
  Small-medium + no transforms → Copy Job
  Large + code-first team → Pipeline + Notebook
  Large + orchestration needed → Pipeline (Copy activity)
  Complex orchestration (any volume) → Pipeline
  No connector exists + code-first → Notebook (standalone)
---

# Ingestion Method Selection

> Choose the right method to get data into Microsoft Fabric. Start with the **4 V's assessment** to understand your data profile, then use the reference matrix and tool guide to pick the right tool.
>
> **Agents:** Resolve from `quick_decision` in frontmatter first. Only read body for edge cases.

## The 4 V's Assessment

Before choosing an ingestion method, assess your project across four dimensions:

| Dimension | Question | Options | Guides To |
|-----------|----------|---------|-----------|
| **Volume** | How much data? | Small–medium (< 1 GB) → Dataflow Gen2 · Large–very large (> 1 GB) → Notebooks, Copy Job, Pipeline (Copy activity) | Tool selection below |
| **Velocity** | How fast? | Real-time → Eventstream, Mirroring · Always-live → Shortcut, Fabric Link · Batch → Pipeline, Dataflow Gen2, Copy Job | Tool selection below |
| **Variety** | What types? | Sources: DBs, files, APIs, SaaS, sensors · Shapes: structured, semi-structured, unstructured · Landing: see [Storage Selection](storage-selection.md) | Variety section below |
| **Versatility** | What skills? | Low-code: Pipelines, Dataflow Gen2, Eventstream, Copy Job · Code-first: Notebooks | [Skillset Selection](skillset-selection.md) |

### Reference Matrix

| Tool | Volume | Velocity | Variety (Sources) | Versatility | Transformation | Scheduling | Complexity |
|------|--------|----------|-------------------|-------------|----------------|------------|------------|
| **Copy Job** | Small → Large | Batch | 100+ connectors (DBs, files, APIs) | Low-code [LC] | None | Built-in | Low |
| **Dataflow Gen2** | Small → Medium | Batch | 150+ connectors (DBs, files, SaaS) | Low-code [LC] | Power Query (M) | Built-in | Low-Medium |
| **Pipeline** | Any | Batch | Activities + connectors + Notebooks | Low-code + Code [LC/CF] | Orchestrates others | Advanced | Medium-High |
| **Notebook** | Large → Very Large | Batch | Custom code (any source) | Code-first [CF] | Full code (Python/Spark) | Via Pipeline | High |
| **Eventstream** | Any (streaming) | Real-time | Event Hubs, Kafka, custom apps, IoT | Low-code [LC] | Stream processing | Continuous | Medium |
| **Mirroring** | Any | Continuous CDC | Azure SQL, Azure SQL MI, Cosmos DB, Snowflake, Databricks, SQL Server 2025, MySQL (preview), PostgreSQL (preview) | Low-code [LC] | None | Automatic | Low |
| **Shortcut** | Any | Always live (zero-copy) | ADLS Gen2, S3, GCS, cross-workspace Fabric items | Low-code [LC] | None | N/A (always live) | Very Low |
| **Fabric Link** | Any | Continuous sync | Dataverse (Dynamics 365, Power Platform) | Low-code [LC] | None | Automatic | Low |

## When to Choose Each

| Tool | Choose When | Example Use Cases |
|------|------------|-------------------|
| **Copy Job** | Simple data movement, no transforms, quick setup, one-to-one copy | Copy Blob→Lakehouse, CSV/Parquet load, simple DB extraction |
| **Dataflow Gen2** | Visual no-code transforms, business user ETL, Power Query compatible | Cleanse+reshape before load, merge sources, pivot/unpivot |
| **Pipeline** | Complex orchestration, conditional logic, multi-step ETL, error handling | Medallion orchestration, trigger notebooks, parameterized runs |
| **Notebook** | Custom API ingestion, proprietary formats, sensor/IoT parsing, code-first team | REST API with custom auth, wearable sensor data, video/media processing, web scraping |
| **Eventstream** | Real-time streaming, sub-minute freshness, IoT sensors (streaming), logs | IoT ingestion, application logs, clickstream, live monitoring |
| **Mirroring** | Replicate entire database, CDC without code, near-real-time sync | Azure SQL→Lakehouse, Cosmos DB replication, Snowflake mirror |
| **Shortcut** | Data already in ADLS/S3/GCS/OneLake, zero-copy, cross-workspace sharing | Reference existing Delta tables, share Gold layer, multi-cloud access |
| **Fabric Link** | Dataverse source (Dynamics 365, Power Platform), zero-ETL sync | Dynamics 365 analytics, Power Platform data in Fabric |

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

## Variety — What Types of Data?

### Source Types

| Source Category | Examples | Best Tool |
|----------------|----------|-----------|
| **Databases** | SQL Server, Azure SQL MI, Oracle, MySQL, PostgreSQL | Copy Job, Pipeline, Mirroring |
| **Files** | CSV, Parquet, JSON, Excel, XML | Copy Job, Dataflow Gen2 |
| **APIs** | REST endpoints, OData feeds | Dataflow Gen2, Pipeline + Notebook |
| **Sensors / IoT** | Wearables, GPS, telemetry, proprietary protocols | Eventstream (streaming) or Notebook (batch) |
| **SaaS Apps** | Salesforce, Dynamics 365, SharePoint | Dataflow Gen2 (built-in connectors) |
| **Streaming** | Event Hubs, Kafka, IoT Hub, custom apps | Eventstream |
| **Cloud / Cross-workspace / Multi-cloud** | ADLS Gen2, S3, GCS, OneLake, Databricks | Shortcut (zero-copy) |
| **Dataverse** | Dynamics 365, Power Platform apps | Fabric Link |

### Data Shapes

| Shape | Examples | Considerations |
|-------|----------|---------------|
| **Structured** | Relational tables, typed CSV | Any tool works — Copy Job is simplest |
| **Semi-structured** | JSON, CSV with variable schemas, XML | Dataflow Gen2 (flatten/parse) or Notebook (schema-on-read) |
| **Unstructured** | Logs, media, documents | Notebook (custom parsing) or Pipeline + Notebook |

### Landing Targets

Where data lands determines which ingestion tools are compatible:

| Ingestion Method | Lakehouse | Warehouse | Eventhouse | SQL Database | CosmosDB |
|------------------|-----------|-----------|------------|--------------|----------|
| **Copy Job** | ✅ | ✅ | ❌ | ✅ | ❌ |
| **Dataflow Gen2** | ✅ | ✅ | ❌ | ✅ | ❌ |
| **Pipeline** | ✅ | ✅ | ✅ (via activities) | ✅ | ✅ (via activities) |
| **Notebook** | ✅ | ✅ (via T-SQL) | ❌ | ✅ (via T-SQL) | ✅ (via SDK) |
| **Eventstream** | ✅ | ❌ | ✅ | ❌ | ❌ |
| **Mirroring** | ✅ (output) | ❌ | ❌ | Source only | Source only |
| **Shortcut** | ✅ (Files or Tables) | ❌ | ❌ | ❌ | ❌ |
| **Fabric Link** | ✅ (Delta tables) | ❌ | ❌ | ❌ | ❌ |

See [Storage Selection](storage-selection.md) for choosing the right landing target based on your use case.

## Guiding Principles

### Consider Team Skills

Match tools to your team's capabilities:

- **T-SQL team** → Pipeline + Copy Activity + Warehouse stored procs
- **Python/Spark team** → Pipeline + Notebook (maximum flexibility)
- **Business analysts** → Dataflow Gen2 (Power Query is familiar from Excel/Power BI)
- **Mixed team** → Pipeline as orchestrator, with Dataflow Gen2 AND Notebook activities

See [Skillset Selection](skillset-selection.md) for the full Versatility assessment.

### Optimize and Monitor

Build observability into your ingestion from day one:

- **Measure** — Track ingestion duration, row counts, and data freshness per run
- **Alert** — Use Activator or Pipeline failure notifications to catch issues early
- **Diagnose** — Log source-to-destination lineage so you can trace data quality issues
- **Baseline** — Establish normal run times before optimizing

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

- [Storage Selection](storage-selection.md) — Choose landing target (Variety dimension)
- [Processing Selection](processing-selection.md) — Transform data after ingestion
- [Skillset Selection](skillset-selection.md) — Code-First vs Low-Code (Versatility dimension)
- [Visualization Selection](visualization-selection.md) — How to present ingested data
