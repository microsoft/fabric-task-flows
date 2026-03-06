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
  Small-medium + transforms needed → Dataflow Gen2
  Small-medium + no transforms → Copy Job
  Large + code-first team → Pipeline + Notebook
  Large + orchestration needed → Pipeline (Copy activity)
  Complex orchestration (any volume) → Pipeline
  No connector exists + code-first → Notebook (standalone)
---

# Ingestion Method Selection

> Choose the right method to get data into Microsoft Fabric. Start with the **4 V's assessment** to understand your data profile, then use the decision tree and comparison table to pick the right tool.

## The 4 V's Assessment

Before choosing an ingestion method, assess your project across four dimensions:

| Dimension | Question | Options | Guides To |
|-----------|----------|---------|-----------|
| **Volume** | How much data? | Small–medium (< 1 GB) → Dataflow Gen2 · Large–very large (> 1 GB) → Notebooks, Copy Job, Pipeline (Copy activity) | Tool selection below |
| **Velocity** | How fast? | Real-time → Eventstream, Mirroring · Always-live → Shortcut, Fabric Link · Batch → Pipeline, Dataflow Gen2, Copy Job | Decision tree below |
| **Variety** | What types? | Sources: DBs, files, APIs, SaaS · Shapes: structured, semi-structured (CSV/JSON), unstructured (logs/media) · Landing: see [Storage Selection](storage-selection.md) | Variety section below |
| **Versatility** | What skills? | Low-code: Pipelines, Dataflow Gen2, Eventstream, Copy Job · Code-first: Notebooks | [Skillset Selection](skillset-selection.md) |

### 4 V's Quick-Reference Matrix

| Tool | Volume | Velocity | Variety (Sources) | Versatility |
|------|--------|----------|-------------------|-------------|
| **Copy Job** | Small → Large | Batch | 100+ connectors (DBs, files, APIs) | Low-code [LC] |
| **Dataflow Gen2** | Small → Medium | Batch | 150+ connectors (DBs, files, SaaS) | Low-code [LC] |
| **Pipeline** | Any | Batch | Activities + connectors + Notebooks | Low-code + Code [LC/CF] |
| **Notebook** | Large → Very Large | Batch | Custom code (any source) | Code-first [CF] |
| **Eventstream** | Any (streaming) | Real-time | Event Hubs, Kafka, custom apps | Low-code [LC] |
| **Mirroring** | Any | Continuous CDC | Azure SQL, Cosmos DB, Snowflake, SQL Server 2025 | Low-code [LC] |
| **Shortcut** | Any | Always live (zero-copy) | ADLS Gen2, S3, GCS, cross-workspace Fabric items | Low-code [LC] |
| **Fabric Link** | Any | Continuous sync | Dataverse (Dynamics 365, Power Platform) | Low-code [LC] |

## Quick Decision Tree

```
Is your data ALREADY in a cloud store or another Fabric workspace?
│
├─► YES (ADLS Gen2, S3, GCS, or another Lakehouse) ─► SHORTCUT
│
└─► NO (data needs to be moved into Fabric)
    │
    ├─► Is the source DATAVERSE (Dynamics 365 / Power Platform)?
    │   │
    │   └─► YES ────────────────────────────► FABRIC LINK
    │
    ├─► Is your data arriving in REAL-TIME (streaming)?
    │   │
    │   └─► YES ────────────────────────────► EVENTSTREAM
    │
    ├─► Do you need to REPLICATE an entire database continuously?
    │   │
    │   └─► YES ────────────────────────────► MIRRORING
    │
    └─► NO (batch / scheduled)
        │
        ├─► What VOLUME of data?
        │   │
        │   ├─► Small–medium (< 1 GB per load)
        │   │   │
        │   │   ├─► Need transformations? ───► DATAFLOW GEN2
        │   │   │
        │   │   └─► No transforms needed ───► COPY JOB
        │   │
        │   └─► Large–very large (> 1 GB per load)
        │       │
        │       ├─► Code-first team ────────► PIPELINE + Notebook
        │       │
        │       ├─► Need orchestration ─────► PIPELINE (with Copy activity)
        │       │
        │       └─► Simple one-to-one copy ─► COPY JOB
        │
        ├─► No connector exists + code-first team?
        │   │
        │   └─► YES ────────────────────────► NOTEBOOK (standalone)
        │
        └─► Need COMPLEX ORCHESTRATION regardless of volume?
            │
            └─► YES ────────────────────────► PIPELINE
```

## Comparison Table

| Criteria | Copy Job | Dataflow Gen2 | Pipeline | Notebook | Eventstream | Mirroring | Shortcut | Fabric Link |
|----------|----------|---------------|----------|----------|-------------|-----------|----------|-------------|
| **Volume** | Small → Large | Small → Medium | Any | Large → Very Large | Any (streaming) | Any | Any | Any |
| **Velocity** | Batch | Batch | Batch | Batch | Real-time streaming | Continuous CDC | Always live | Continuous sync |
| **Variety** | 100+ connectors | 150+ connectors | Activities + connectors | Custom code (any) | Event sources | Database-specific | ADLS, S3, GCS, OneLake | Dataverse only |
| **Versatility** | Low-Code [LC] | Low-Code [LC] | Low-Code + Code [LC/CF] | Code-First [CF] | Low-Code [LC] | Low-Code [LC] | Low-Code [LC] | Low-Code [LC] |
| **Transformation** | None | Power Query (M) | Orchestrates others | Full code (Python/Spark) | Stream processing | None | None | None |
| **Scheduling** | Built-in schedule | Built-in schedule | Advanced scheduling | Via Pipeline | Continuous | Automatic | N/A (always live) | Automatic |
| **Error Handling** | Basic retry | Basic retry | Advanced (conditions, retry) | Custom code | Dead-letter queues | Automatic retry | N/A | Automatic retry |
| **Incremental Load** | ✅ Supported | ✅ Supported | ✅ Advanced patterns | ✅ Custom code | N/A (streaming) | ✅ Built-in CDC | N/A (live reference) | ✅ Built-in sync |
| **Complexity** | Low | Low-Medium | Medium-High | High | Medium | Low | Very Low | Low |

## When to Choose Each

### Choose COPY JOB when:

- ✅ You need **simple data movement** without transformation
- ✅ Source data is already in the right format
- ✅ You want **quick setup** with minimal configuration
- ✅ One-to-one copy from source to destination
- ✅ Built-in **incremental refresh** is sufficient
- ✅ No complex orchestration needed

**Example Use Cases:**
- Copy files from Azure Blob to Lakehouse
- Load CSV/Parquet from external storage
- Simple database table extraction

### Choose DATAFLOW GEN2 when:

- ✅ You need **visual, no-code transformations**
- ✅ Business users will maintain the data flows
- ✅ Transformations are **Power Query compatible** (filter, merge, pivot, etc.)
- ✅ You want a **familiar Excel/Power BI** experience
- ✅ Data cleansing and shaping before loading

**Example Use Cases:**
- Clean and reshape data before loading to warehouse
- Merge multiple sources into single destination
- Apply business rules during ETL
- Unpivot or pivot data structures

### Choose PIPELINE when:

- ✅ You need **complex orchestration** with multiple steps
- ✅ Workflows require **conditional logic** (if/else, loops)
- ✅ You need to **call notebooks, Spark jobs, or other items**
- ✅ **Error handling** with custom retry and failure paths
- ✅ **Parameterized** runs with different configurations
- ✅ Dependencies between multiple data processing steps

**Example Use Cases:**
- Medallion architecture orchestration (Bronze → Silver → Gold)
- Conditional data loading based on source availability
- Trigger notebooks after data lands
- Complex ETL with multiple destinations

### Choose EVENTSTREAM when:

- ✅ Data arrives in **real-time** (IoT sensors, logs, clicks)
- ✅ You need **sub-minute data freshness**
- ✅ Source is **streaming** (Event Hubs, Kafka, custom apps)
- ✅ You want **stream processing** (filtering, routing, windowing)
- ✅ Destination is **Eventhouse, Lakehouse, or KQL Database**

**Example Use Cases:**
- IoT sensor data ingestion
- Application log streaming
- Real-time clickstream analytics
- Live event monitoring

### Choose MIRRORING when:

- ✅ You need to **replicate an entire database** to OneLake
- ✅ Source is Azure SQL, Cosmos DB, Snowflake, or SQL Server 2025
- ✅ You want **CDC (Change Data Capture)** without custom code
- ✅ **Near real-time sync** of operational data
- ✅ No transformation needed (raw replication)

**Example Use Cases:**
- Sync Azure SQL Database to Lakehouse for analytics
- Replicate Cosmos DB for cross-region or analytics
- Mirror Snowflake data into Fabric

### Choose SHORTCUT when:

- ✅ Data **already lives** in ADLS Gen2, S3, GCS, or another Fabric workspace
- ✅ You want **zero-copy access** — no data movement, no duplication
- ✅ You need to **share data across workspaces** without copying
- ✅ You want data to be **always live** — no schedule, no sync lag
- ✅ Destination is **Lakehouse** (Files or Tables section)

**Example Use Cases:**
- Reference existing Delta tables in ADLS Gen2 from a Lakehouse
- Share a Gold layer across multiple consumer workspaces
- Access S3 Parquet files without copying into OneLake
- Create a Bronze layer that points to an external data lake

### Choose FABRIC LINK when:

- ✅ Source is **Dataverse** (Dynamics 365, Power Platform apps)
- ✅ You want **continuous sync** of Dataverse tables to OneLake
- ✅ You need **zero-ETL** — no pipeline or dataflow to build
- ✅ Data should land as **Delta tables in a Lakehouse**
- ✅ Setup is from **Power Platform admin center** (not Fabric)

**Example Use Cases:**
- Analyze Dynamics 365 Sales data alongside financial reports
- Build Power BI dashboards on Dataverse CRM data in Fabric
- Combine Power Platform app data with other Fabric sources

### Choose NOTEBOOK (standalone) when:

- ✅ **No built-in connector exists** for your source
- ✅ You need **custom API ingestion** (REST, GraphQL, proprietary)
- ✅ Source requires **complex authentication** or parsing logic
- ✅ Your team is **code-first** (Python, PySpark, Scala)
- ✅ You need ingestion + transformation in a **single step**

**Example Use Cases:**
- Pull data from a proprietary REST API with custom auth
- Web scraping or screen-scraping legacy systems
- Complex file parsing (nested JSON, multi-sheet Excel, XML with namespaces)
- Ingest + transform in one pass for code-first teams

## Combining Ingestion Methods

### Common Patterns

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

### Pipeline Orchestration Example

```
Pipeline: Medallion_ETL
│
├─ Activity 1: Copy Job (source → Bronze)
│
├─ Activity 2: Notebook (Bronze → Silver transformation)
│
├─ Activity 3: Notebook (Silver → Gold aggregation)
│
└─ Activity 4: Semantic Model refresh (optional)
```

## Variety — What Types of Data?

Understanding the **variety** of your data sources, shapes, and landing targets helps narrow down which tools fit.

### Source Types

| Source Category | Examples | Best Tool |
|----------------|----------|-----------|
| **Databases** | SQL Server, Oracle, MySQL, PostgreSQL | Copy Job, Pipeline, Mirroring |
| **Files** | CSV, Parquet, JSON, Excel, XML | Copy Job, Dataflow Gen2 |
| **APIs** | REST endpoints, OData feeds | Dataflow Gen2, Pipeline + Notebook |
| **SaaS Apps** | Salesforce, Dynamics 365, SharePoint | Dataflow Gen2 (built-in connectors) |
| **Streaming** | Event Hubs, Kafka, IoT Hub, custom apps | Eventstream |
| **Cloud Storage** | ADLS Gen2, S3, GCS | Shortcut (zero-copy) or Copy Job |
| **Dataverse** | Dynamics 365, Power Platform apps | Fabric Link |
| **Cross-workspace** | Other Fabric Lakehouses | Shortcut |

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

### No One-Size-Fits-All

Every project has a unique combination of Volume, Velocity, Variety, and Versatility. Choose ingestion tools based on **your specific requirements** — not industry trends or tool preferences. A Copy Job that solves the problem is better than a Notebook that impresses nobody.

### Keep it Simple

Start with the **simplest tool** that meets requirements. Add complexity only when justified:

| If this works... | Don't use this instead... | Unless you need... |
|------------------|--------------------------|-------------------|
| Copy Job | Pipeline with Copy Activity | Conditional logic, error routing, multi-step |
| Dataflow Gen2 | Notebook with Spark | > 1 GB transforms, custom code, ML features |
| Built-in schedule | Pipeline scheduling | Dependencies between multiple items |
| Mirroring | Pipeline + CDC patterns | Transformation during replication |
| Shortcut | Copy Job or Pipeline | Transformation, snapshots, or non-Lakehouse target |
| Fabric Link | Dataflow Gen2 with Dataverse connector | Custom transforms during sync |

### Consider Team Skills

Match tools to your team's capabilities and invest in training strategically:

- **T-SQL team** → Pipeline + Copy Activity + Warehouse stored procs (leverage existing skills)
- **Python/Spark team** → Pipeline + Notebook (maximum flexibility)
- **Business analysts** → Dataflow Gen2 (Power Query is familiar from Excel/Power BI)
- **Mixed team** → Pipeline as orchestrator, with Dataflow Gen2 AND Notebook activities

See [Skillset Selection](skillset-selection.md) for the full Versatility assessment.

### Optimize and Monitor

Build observability into your ingestion from day one — don't bolt it on later:

- **Measure** — Track ingestion duration, row counts, and data freshness per run
- **Alert** — Use Activator or Pipeline failure notifications to catch issues early
- **Diagnose** — Log source-to-destination lineage so you can trace data quality issues
- **Baseline** — Establish normal run times before optimizing; you can't improve what you don't measure

## Anti-Patterns

| Don't Do This | Why | Do This Instead |
|---------------|-----|-----------------|
| Use Eventstream for batch data | Overhead, complexity for batch | Use Copy Job or Dataflow Gen2 |
| Build transformations in Pipeline activities | Hard to maintain | Use Dataflow Gen2 or Notebook |
| Use Dataflow Gen2 for > 1 GB transforms | Performance limits at scale | Use Notebook or Pipeline + Copy |
| Use Copy Job when need complex joins | No transformation support | Use Dataflow Gen2 |
| Skip Pipeline for multi-step ETL | Error handling, dependencies | Use Pipeline for orchestration |
| Over-engineer small data with Notebooks | Unnecessary complexity | Use Dataflow Gen2 or Copy Job |
| Skip monitoring setup | Silent failures, data freshness drift | Add Activator alerts from day one |
| Copy data that's already in ADLS/S3/GCS | Unnecessary duplication and cost | Use Shortcut for zero-copy access |
| Build ETL pipeline for Dataverse data | Unnecessary when Fabric Link exists | Use Fabric Link for zero-ETL sync |
| Use Shortcut when you need snapshots | Shortcuts are always live, no versioning | Use Copy Job for point-in-time copies |

## Related Decisions

- [Storage Selection](storage-selection.md) — Choose landing target (Variety dimension)
- [Processing Selection](processing-selection.md) — Transform data after ingestion
- [Skillset Selection](skillset-selection.md) — Code-First vs Low-Code (Versatility dimension)
- [Visualization Selection](visualization-selection.md) — How to present ingested data
