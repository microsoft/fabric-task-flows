---
id: visualization-selection
title: Visualization Type Selection
---

# Visualization Type Selection

> Choose the right visualization type based on your interactivity needs, distribution requirements, and data refresh patterns.
>
> **⚠️ Terminology:** Users often say "dashboard" when they mean an interactive Power BI **Report**. In Fabric, a "Dashboard" is ONLY a **Real-Time Dashboard** — an RTI item connected to a KQL Database for sub-second streaming data. When users ask for "dashboards" in a batch context, map to **Report**. Only use Real-Time Dashboard when the architecture includes Eventhouse/Eventstream.

## Comparison Table

| Criteria | Report | Paginated | Scorecard | Real-Time Dashboard | Real-Time Map |
|----------|--------|-----------|-----------|---------------------|---------------|
| **Interactivity** | High | Parameters only | Check-ins | Limited | Pan/zoom/layers |
| **Data Source** | Semantic Model | Direct or dataset | Manual/connected | Eventhouse stream | Eventhouse stream |
| **Refresh** | Scheduled/DirectQuery | On-demand | Manual/auto | Sub-second | Sub-second |
| **Export** | PBIX, PDF, PPT | PDF, Excel, Word | Limited | Screenshot | Screenshot |
| **Pages** | Multi-page canvas | Multi-page formatted | Goal-focused | Single dashboard | Single map |
| **Mobile** | ✅ Optimized | ✅ Responsive | ✅ Teams | ✅ Web | ✅ Web |
| **Embedding** | ✅ Full support | ✅ Embedded | Limited | ✅ Full support | ✅ Full support |

## Detailed Guidance

See [visualization-patterns.md](visualization-patterns.md) for:
- **When to Choose Each** — detailed criteria and example use cases per type
- **Workflow Patterns** — combining visualization types for common scenarios
- **Refresh & Distribution Options** — per-type capability tables
- **Anti-Patterns** — common mistakes and better alternatives

## Semantic Model Considerations

### Query Mode Comparison

| Query Mode | Best For | Data Freshness | Performance | Visualization Support |
|------------|----------|---------------|-------------|----------------------|
| **Import** | Small-medium data (< 1 GB), scheduled refresh | Minutes to hours (on refresh) | Fastest (in-memory) | Report, Paginated, Scorecard |
| **DirectQuery** | Large data, near real-time needs | Seconds (live query) | Slower (queries source on every interaction) | Report (with [automatic page refresh](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-automatic-page-refresh)) |
| **Direct Lake** | Any Fabric source with Delta tables in OneLake, large data + fast queries | Near real-time (reads Delta directly) | Fast (columnar in-memory from Parquet) | Report |
| **Composite** | Mix of hot (Import) + large (DirectQuery/Direct Lake) | Varies by table | Mixed | Report |

### When to Choose Direct Lake

Direct Lake is the **recommended mode for Semantic Models on Fabric data sources** — it reads Delta/Parquet files directly from OneLake without importing data, giving near-import performance with near-real-time freshness.

**The key principle:** Any Fabric compute engine that makes its data available in OneLake as Delta tables can leverage Direct Lake. This includes:

| Fabric Source | Direct Lake Support | How Data Reaches OneLake |
|--------------|-------------------|--------------------------|
| **Lakehouse** | ✅ Native | Delta tables stored directly in OneLake |
| **Warehouse** | ✅ Native | Tables stored as Delta/Parquet in OneLake |
| **SQL Database** | ✅ Via mirroring | Automatic mirroring replicates to OneLake in Delta format |
| **Eventhouse / KQL Database** | ✅ Via OneLake availability | Enable OneLake availability to expose data as Delta tables |
| **Mirrored Databases** (Azure SQL, Cosmos DB, Snowflake) | ✅ Via mirroring | Fabric mirroring replicates external sources to OneLake |

**Two Direct Lake variants:**
- **Direct Lake on SQL endpoints** (GA) — Works with Lakehouse and Warehouse. Falls back to DirectQuery when needed (e.g., SQL-based security, views).
- **Direct Lake on OneLake** (Preview) — Works with ANY Fabric source with Delta tables. No DirectQuery fallback. Enable via tenant setting.

**Choose Direct Lake when:**
- ✅ Data is in a **Fabric source with Delta tables in OneLake** (Lakehouse, Warehouse, SQL Database, Eventhouse, or mirrored database)
- ✅ You need **fast query performance** without scheduled imports
- ✅ Dataset is **large** (GBs to TBs) — avoids Import memory limits
- ✅ Data freshness matters — changes in Delta tables are reflected quickly

**Optimize Direct Lake performance (from Microsoft's petabyte-scale experience):**
- **Pre-aggregate into periodic snapshots** — Create daily/weekly/monthly grain FACT tables instead of querying raw transaction-level data. This dramatically reduces the data volume Direct Lake must scan.
- **Remove high-cardinality dimensions** — Columns with millions of unique values (e.g., raw timestamps, GUIDs) hurt Direct Lake performance. Replace with lower-cardinality alternatives (date keys, category codes).
- **Use Liquid Clustering** — Cluster Delta tables on the columns most frequently used in Power BI filters and slicers.
- **Separate transaction and snapshot tables** — Keep detailed transaction FACs for drill-through but build primary dashboards on pre-aggregated periodic snapshots.

**Direct Lake limitations:**
- Requires data stored as **Delta tables in OneLake** — external sources not in Fabric must first be mirrored or ingested
- **Direct Lake on SQL endpoints** falls back to DirectQuery when SQL-based security or views are detected (["fallback" behavior](https://learn.microsoft.com/fabric/fundamentals/direct-lake-overview#fallback)); **Direct Lake on OneLake** does NOT fall back
- Calculated columns and Power Query transforms are not supported — all data preparation must be done upstream (Spark, T-SQL, pipelines, dataflows)
- Requires [Fabric capacity](https://learn.microsoft.com/fabric/fundamentals/direct-lake-overview#fabric-capacity-requirements) with guardrails based on SKU (max rows, max file size per table)

### Version Control for Semantic Models

Use **TMDL (Tabular Model Definition Language)** to version-control Semantic Model definitions in git. All relationship and measure changes should go through Pull Requests:

- Export: Power BI Desktop → Save as TMDL → commit to git
- Tools: [Tabular Editor 3](https://tabulareditor.com/), [DAX Studio](https://daxstudio.org/), Fabric Web Editor
- Review: All TMDL changes via PRs ensure model integrity across team contributions

> **Note:** Real-Time Dashboard and Real-Time Map connect directly to Eventhouse/KQL Database, not through semantic models. For sub-second streaming, use Real-Time Dashboard (metrics) or Real-Time Map (geospatial) with Eventhouse. For near real-time on Power BI Reports, use DirectQuery with automatic page refresh.

## Related Decisions

- [Storage Selection](storage-selection.md) - Where visualization data comes from
- [Processing Selection](processing-selection.md) - How to prepare data for visualization
- [Skillset Selection](skillset-selection.md) - Code-First vs Low-Code capabilities
