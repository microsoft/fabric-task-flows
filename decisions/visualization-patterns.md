# Visualization Patterns Reference

Quick decision tree and comparison table: [visualization-selection.md](visualization-selection.md).

---

## When to Choose Each

| Type | Choose when |
|------|------------|
| **Report** | Interactive exploration (filters/slicers/drill-through), self-service BI, cross-filtering, role-based views, embedding |
| **Paginated** | Pixel-perfect print-ready output, multi-page (invoices/statements), compliance formatting, PDF/Excel export as primary deliverable, show all rows |
| **Scorecard** | Goal/KPI tracking, status check-ins, OKR tracking, Teams integration |
| **RT Dashboard** | Streaming data (Eventstream/Event Hubs), sub-second refresh, Eventhouse/KQL source, current-state monitoring |
| **RT Map** | Geospatial/lat-long data, live asset tracking, Eventhouse/KQL source, [map layers/clustering](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/map/create-map) |

---

## Combining Visualization Types

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
