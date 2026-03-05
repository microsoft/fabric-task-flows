---
id: ingestion-selection
title: Ingestion Method Selection
description: Choose the right data ingestion method based on data arrival pattern, transformation needs, and orchestration requirements
triggers:
  - "copy job vs pipeline"
  - "dataflow vs pipeline"
  - "how to ingest data"
  - "eventstream vs copy job"
  - "batch vs streaming"
  - "data ingestion"
options:
  - id: copy-job
    label: Copy Job
    criteria:
      data_pattern: batch
      transformation: none (copy as-is)
      skillset: low-code
      orchestration: standalone or pipeline
      best_for: ["simple data movement", "scheduled refresh", "one-to-one copy"]
  - id: dataflow-gen2
    label: Dataflow Gen2
    criteria:
      data_pattern: batch
      transformation: Power Query (M)
      skillset: low-code
      orchestration: standalone or pipeline
      best_for: ["visual transformations", "data cleansing", "business user ETL"]
  - id: pipeline
    label: Data Pipeline
    criteria:
      data_pattern: batch
      transformation: orchestration (calls other items)
      skillset: low-code and code-first
      orchestration: full orchestration engine
      best_for: ["complex workflows", "conditional logic", "multi-step ETL"]
  - id: eventstream
    label: Eventstream
    criteria:
      data_pattern: real-time streaming
      transformation: stream processing
      skillset: low-code
      orchestration: continuous
      best_for: ["IoT", "logs", "real-time events", "Kafka"]
  - id: mirroring
    label: Mirroring
    criteria:
      data_pattern: continuous replication
      transformation: none (replicate as-is)
      skillset: low-code
      orchestration: automatic
      best_for: ["database replication", "CDC", "operational data sync"]
---

# Ingestion Method Selection

> Choose the right method to get data into Microsoft Fabric based on your data arrival pattern, transformation needs, and orchestration requirements.

## Quick Decision Tree

```
Is your data arriving in REAL-TIME (streaming)?
│
├─► YES ──────────────────────────────────────► EVENTSTREAM
│
└─► NO (batch/scheduled)
    │
    ├─► Do you need to REPLICATE an entire database continuously?
    │   │
    │   └─► YES ──────────────────────────────► MIRRORING
    │
    └─► NO
        │
        ├─► Do you need TRANSFORMATIONS during ingestion?
        │   │
        │   ├─► YES, visual/Power Query ──────► DATAFLOW GEN2
        │   │
        │   └─► YES, complex/code-based ──────► PIPELINE + Notebook
        │
        └─► NO, just copy data as-is
            │
            ├─► Simple one-to-one copy ───────► COPY JOB
            │
            └─► Need orchestration/conditions ► PIPELINE (with Copy activity)
```

## Comparison Table

| Criteria | Copy Job | Dataflow Gen2 | Pipeline | Eventstream | Mirroring |
|----------|----------|---------------|----------|-------------|-----------|
| **Data Pattern** | Batch | Batch | Batch | Real-time streaming | Continuous CDC |
| **Transformation** | None | Power Query (M) | Orchestrates others | Stream processing | None |
| **Skillset** | Low-Code [LC] | Low-Code [LC] | Low-Code + Code [LC/CF] | Low-Code [LC] | Low-Code [LC] |
| **Scheduling** | Built-in schedule | Built-in schedule | Advanced scheduling | Continuous | Automatic |
| **Connectors** | 100+ sources | 150+ sources | Activities + connectors | Event sources | Database-specific |
| **Error Handling** | Basic retry | Basic retry | Advanced (conditions, retry) | Dead-letter queues | Automatic retry |
| **Incremental Load** | ✅ Supported | ✅ Supported | ✅ Advanced patterns | N/A (streaming) | ✅ Built-in CDC |
| **Complexity** | Low | Low-Medium | Medium-High | Medium | Low |

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
- ✅ Source is Azure SQL, Cosmos DB, or Snowflake
- ✅ You want **CDC (Change Data Capture)** without custom code
- ✅ **Near real-time sync** of operational data
- ✅ No transformation needed (raw replication)

**Example Use Cases:**
- Sync Azure SQL Database to Lakehouse for analytics
- Replicate Cosmos DB for cross-region or analytics
- Mirror Snowflake data into Fabric

## Combining Ingestion Methods

### Common Patterns

| Pattern | Ingestion Method | Orchestration |
|---------|------------------|---------------|
| **Simple batch load** | Copy Job alone | Built-in schedule |
| **Batch with transformation** | Dataflow Gen2 | Built-in schedule |
| **Orchestrated batch ETL** | Pipeline → Copy + Notebook | Pipeline schedule |
| **Real-time + batch (Lambda)** | Eventstream + Copy Job | Separate schedules |
| **Database replication** | Mirroring | Automatic |

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

## Destination Compatibility

| Ingestion Method | Lakehouse | Warehouse | Eventhouse | SQL Database |
|------------------|-----------|-----------|------------|--------------|
| **Copy Job** | ✅ | ✅ | ❌ | ✅ |
| **Dataflow Gen2** | ✅ | ✅ | ❌ | ✅ |
| **Pipeline** | ✅ | ✅ | ✅ (via activities) | ✅ |
| **Eventstream** | ✅ | ❌ | ✅ | ❌ |
| **Mirroring** | ✅ (output) | ❌ | ❌ | Source only |

## Anti-Patterns

| Don't Do This | Why | Do This Instead |
|---------------|-----|-----------------|
| Use Eventstream for batch data | Overhead, complexity for batch | Use Copy Job or Dataflow Gen2 |
| Build transformations in Pipeline activities | Hard to maintain | Use Dataflow Gen2 or Notebook |
| Use Copy Job when need complex joins | No transformation support | Use Dataflow Gen2 |
| Skip Pipeline for multi-step ETL | Error handling, dependencies | Use Pipeline for orchestration |

## Related Decisions

- [Storage Selection](storage-selection.md) - Choose destination storage type
- [Processing Selection](processing-selection.md) - Transform data after ingestion
- [Skillset Selection](skillset-selection.md) - Code-First vs Low-Code capabilities
