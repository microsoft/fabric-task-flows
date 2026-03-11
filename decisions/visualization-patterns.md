# Visualization Patterns Reference

Detailed guidance for choosing between visualization types, combining them, and avoiding common anti-patterns. For the quick decision tree and comparison table, see [visualization-selection.md](visualization-selection.md).

---

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

---

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
