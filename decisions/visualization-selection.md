---
id: visualization-selection
title: Visualization Type Selection
description: Choose the right visualization type based on interactivity needs, distribution format, and refresh requirements
triggers:
  - "report vs real-time dashboard"
  - "paginated report"
  - "real-time dashboard"
  - "real-time map"
  - "location tracking"
  - "scorecard vs report"
  - "which visualization"
  - "how to visualize data"
options:
  - id: report
    label: Power BI Report
    criteria:
      interactivity: high (filters, slicers, drill-through)
      distribution: web, mobile, embedded
      refresh: scheduled or real-time
      best_for: ["interactive analysis", "self-service BI", "exploration"]
  - id: paginated-report
    label: Paginated Report
    criteria:
      interactivity: parameters only
      distribution: PDF, print, export
      refresh: on-demand or scheduled
      best_for: ["operational reports", "invoices", "regulated reports"]
  - id: scorecard
    label: Metrics Scorecard
    criteria:
      interactivity: check-ins, status updates
      distribution: web, Teams
      refresh: manual or connected
      best_for: ["KPI tracking", "goal monitoring", "OKRs"]
  - id: real-time-dashboard
    label: Real-Time Dashboard
    criteria:
      interactivity: limited (focus on live data)
      distribution: web
      refresh: sub-second streaming
      best_for: ["live monitoring", "IoT dashboards", "operations centers"]
  - id: real-time-map
    label: Real-Time Map
    criteria:
      interactivity: pan, zoom, layer toggle
      distribution: web
      refresh: sub-second streaming
      best_for: ["location tracking", "geospatial monitoring", "fleet tracking"]
quick_decision: |
  Interactive exploration + filters → Power BI Report
  Pixel-perfect / printable / multi-page → Paginated Report
  Goal/KPI tracking + check-ins → Metrics Scorecard
  Live streaming data (sub-second) → Real-Time Dashboard
  Live geospatial/location data → Real-Time Map
---

# Visualization Type Selection

> Choose the right visualization type based on your interactivity needs, distribution requirements, and data refresh patterns.

## Quick Decision Tree

```
What's your PRIMARY visualization need?
│
├─► Interactive exploration with filters/slicers
│   └─► POWER BI REPORT
│
├─► Pixel-perfect, printable, multi-page
│   └─► PAGINATED REPORT
│
├─► Track goals/KPIs with status updates
│   └─► METRICS SCORECARD
│
├─► Live streaming data (sub-second refresh)
│   └─► REAL-TIME DASHBOARD
│
└─► Live location/geospatial data
    └─► REAL-TIME MAP
```

## Comparison Table

| Criteria | Report | Paginated | Scorecard | Real-Time Dashboard | Real-Time Map |
|----------|--------|-----------|-----------|---------------------|---------------|
| **Interactivity** | High | Parameters only | Check-ins | Limited | Pan/zoom/layers |
| **Skillset** | Low-Code [LC] | Low-Code [LC] | Low-Code [LC] | Low-Code [LC] | Low-Code [LC] |
| **Data Source** | Semantic Model | Direct or dataset | Manual/connected | Eventhouse stream | Eventhouse stream |
| **Refresh** | Scheduled/DirectQuery | On-demand | Manual/auto | Sub-second | Sub-second |
| **Export** | PBIX, PDF, PPT | PDF, Excel, Word | Limited | Screenshot | Screenshot |
| **Pages** | Multi-page canvas | Multi-page formatted | Goal-focused | Single dashboard | Single map |
| **Mobile** | ✅ Optimized | ✅ Responsive | ✅ Teams | ✅ Web | ✅ Web |
| **Embedding** | ✅ Full support | ✅ Embedded | Limited | ✅ Full support | ✅ Full support |

## When to Choose Each

### Choose POWER BI REPORT when:

- ✅ Users need **interactive exploration** (filters, slicers, drill-through)
- ✅ **Self-service BI** where users ask their own questions
- ✅ **Cross-filtering** between visuals is important
- ✅ Data needs vary by user (role-based views)
- ✅ You want **rich visualizations** (maps, custom visuals)
- ✅ Reports will be **embedded** in applications

**Example Use Cases:**
- Sales performance analysis
- Customer segmentation explorer
- Financial variance analysis
- Product analytics dashboard

### Choose PAGINATED REPORT when:

- ✅ Need **pixel-perfect, print-ready** output
- ✅ Reports span **multiple pages** (invoices, statements)
- ✅ **Regulatory or compliance** requirements for formatting
- ✅ Need **PDF/Excel export** as primary deliverable
- ✅ Data tables must show **all rows** (not aggregated)
- ✅ **Mail merge** style reports with parameters

**Example Use Cases:**
- Customer invoices and statements
- Regulatory compliance reports
- Detailed inventory lists
- Employee payroll reports
- Multi-page financial statements

### Choose METRICS SCORECARD when:

- ✅ Tracking **goals and KPIs** over time
- ✅ Need **status check-ins** from team members
- ✅ **OKR (Objectives & Key Results)** tracking
- ✅ Visual **goal progress** indicators
- ✅ Integration with **Microsoft Teams**

**Example Use Cases:**
- Quarterly sales targets
- OKR tracking and check-ins
- Project milestone monitoring
- Department KPI goals

### Choose REAL-TIME DASHBOARD when:

- ✅ Data arrives via **streaming** (Eventstream, Event Hubs)
- ✅ Need **sub-second refresh** for live monitoring
- ✅ **Operations center** or NOC displays
- ✅ Data source is **Eventhouse/KQL Database**
- ✅ Focus on **current state** over historical analysis

**Example Use Cases:**
- IoT sensor monitoring
- Live website traffic
- Factory floor dashboards
- Security operations center
- Trading floor displays

### Choose REAL-TIME MAP when:

- ✅ Data has **geospatial/location** component (lat/long)
- ✅ Need **live tracking** of moving assets
- ✅ Visualizing **geographic patterns** in streaming data
- ✅ Data source is **Eventhouse/KQL Database**
- ✅ Need [map layers and clustering](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/map/create-map)

**Example Use Cases:**
- Fleet/vehicle tracking
- Delivery driver locations
- IoT device geolocation
- Weather station networks
- Asset tracking across facilities

## Visualization Workflow Patterns

### Complete BI Solution

```
┌─────────────────────────────────────────────────────────────────┐
│                    TYPICAL BI WORKFLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Data ──► Semantic Model ──► Reports ──► Interactive analysis   │
│                   │              │                              │
│                   │              └─► Paginated Reports ──► PDF  │
│                   │                                             │
│                   └─► Scorecard ──► Goal tracking               │
│                                                                 │
│  + Real-Time Dashboard (if streaming data)                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Combining Visualization Types

| Scenario | Primary | Secondary | Why |
|----------|---------|-----------|-----|
| **Executive BI** | Report | Scorecard | Interactive + KPI tracking |
| **Operational BI** | Report | Paginated (export) | Interactive + printable |
| **Goal Tracking** | Scorecard | Report (context) | Goals + analysis |
| **Real-Time Ops** | Real-Time Dashboard | Report (history) | Live + historical |
| **Location Tracking** | Real-Time Map | Real-Time Dashboard | Geospatial + metrics |
| **Compliance** | Paginated | N/A | Print-ready required |

## Refresh Options by Type

| Type | Refresh Options | Latency |
|------|-----------------|---------|
| **Report** | Scheduled (hourly/daily), DirectQuery, Direct Lake | Minutes to hours |
| **Paginated** | On-demand, scheduled | On-demand |
| **Scorecard** | Manual check-ins, connected to data | Manual or real-time |
| **Real-Time Dashboard** | Continuous streaming | Sub-second |
| **Real-Time Map** | Continuous streaming | Sub-second |

## Distribution Options

| Type | Web | Mobile | Teams | Embedded | PDF Export |
|------|-----|--------|-------|----------|------------|
| **Report** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Paginated** | ✅ | ✅ | Limited | ✅ | ✅ Primary |
| **Scorecard** | ✅ | ✅ | ✅ Native | Limited | ❌ |
| **Real-Time Dashboard** | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Real-Time Map** | ✅ | ✅ | ✅ | ✅ | ❌ |

## Anti-Patterns

| Don't Do This | Why | Do This Instead |
|---------------|-----|-----------------|
| Use Report for print-ready invoices | Not pixel-perfect | Use Paginated Report |
| Use Real-Time Dashboard for historical data | Designed for streaming | Use Report |
| Use Paginated for self-service exploration | No interactivity | Use Report |
| Build KPI tracking in Report | No check-in workflow | Use Scorecard |
| Use Power BI map visuals for live tracking | Not real-time | Use Real-Time Map |

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
