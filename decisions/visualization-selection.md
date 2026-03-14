---
id: visualization-selection
title: Visualization Type Selection
---

# Visualization Type Selection

> Choose visualization type by interactivity needs, distribution, and refresh patterns.
>
> **⚠️ Terminology:** Users often say "dashboard" when they mean an interactive Power BI **Report**. In Fabric, a "Dashboard" is ONLY a **Real-Time Dashboard** — an RTI item connected to a KQL Database for sub-second streaming data. Map "dashboard" in batch contexts to **Report**.

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

See [visualization-patterns.md](visualization-patterns.md) for per-type criteria, workflow patterns, and anti-patterns.

## Semantic Model Considerations

### Query Mode Comparison

| Query Mode | Best For | Data Freshness | Performance | Visualization Support |
|------------|----------|---------------|-------------|----------------------|
| **Import** | Small-medium data (< 1 GB), scheduled refresh | Minutes to hours (on refresh) | Fastest (in-memory) | Report, Paginated, Scorecard |
| **DirectQuery** | Large data, near real-time needs | Seconds (live query) | Slower (queries source on every interaction) | Report (with [automatic page refresh](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-automatic-page-refresh)) |
| **Direct Lake** | Any Fabric source with Delta tables in OneLake, large data + fast queries | Near real-time (reads Delta directly) | Fast (columnar in-memory from Parquet) | Report |
| **Composite** | Mix of hot (Import) + large (DirectQuery/Direct Lake) | Varies by table | Mixed | Report |

### When to Choose Direct Lake

Recommended for Fabric data sources — reads Delta/Parquet directly from OneLake (near-import performance, near-real-time freshness).

| Fabric Source | Direct Lake Support | OneLake Path |
|--------------|-------------------|--------------------------|
| **Lakehouse** | ✅ Native | Delta tables direct |
| **Warehouse** | ✅ Native | Delta/Parquet direct |
| **SQL Database** | ✅ Via mirroring | Auto-mirrored to Delta |
| **Eventhouse / KQL Database** | ✅ Via OneLake availability | Enable OneLake availability |
| **Mirrored Databases** (Azure SQL, Cosmos DB, Snowflake) | ✅ Via mirroring | Mirrored to OneLake |

**Direct Lake variants:**

| Variant | Status | Sources | DirectQuery Fallback |
|---------|--------|---------|---------------------|
| **On SQL endpoints** | GA | Lakehouse, Warehouse | ✅ Yes (on security/views) |
| **On OneLake** | Preview | Any Fabric source with Delta | ❌ No fallback |

**Choose Direct Lake when:**
- ✅ Data is in a **Fabric source with Delta tables in OneLake**
- ✅ Need **fast queries** without scheduled imports
- ✅ Dataset is **large** (GBs to TBs) — avoids Import memory limits
- ✅ Data freshness matters — Delta changes reflected quickly

**Optimize Direct Lake:**
- Pre-aggregate into periodic snapshot FACT tables (daily/weekly/monthly grain)
- Remove high-cardinality columns (raw timestamps, GUIDs) — use date keys, category codes
- Use Liquid Clustering on columns used in Power BI filters/slicers
- Separate transaction tables (drill-through) from snapshot tables (primary dashboards)

**Direct Lake limitations:**
- Requires **Delta tables in OneLake** — external sources must first be mirrored/ingested
- **On SQL endpoints** falls back to DirectQuery on security/views ([fallback](https://learn.microsoft.com/fabric/fundamentals/direct-lake-overview#fallback)); **On OneLake** does NOT
- No calculated columns or Power Query transforms — all prep must be upstream
- [Capacity guardrails](https://learn.microsoft.com/fabric/fundamentals/direct-lake-overview#fabric-capacity-requirements) based on SKU (max rows, max file size per table)

### Version Control for Semantic Models

Use **TMDL** to version-control Semantic Model definitions in git. Export from Power BI Desktop, commit, and review via PRs. Tools: [Tabular Editor 3](https://tabulareditor.com/), [DAX Studio](https://daxstudio.org/), Fabric Web Editor.

> **Note:** Real-Time Dashboard and Real-Time Map connect directly to Eventhouse/KQL Database, not through semantic models.

## Related Decisions

- [Storage Selection](storage-selection.md)
- [Processing Selection](processing-selection.md)
- [Skillset Selection](skillset-selection.md)
