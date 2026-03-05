# ADR-005: Visualization Selection

## Status

Accepted

**Date:** 2026-03-05  
**Deciders:** fabric-architect agent + user confirmation

## Context

The fraud detection operations team needs to monitor transaction patterns and fraud alerts in real-time. Key requirements:

- **Live updates** without manual refresh for active monitoring
- **Time-series visualization** of transaction volume and fraud rates
- **Alerting integration** for immediate response to high-risk transactions
- **KQL compatibility** since data resides in Eventhouse

## Decision

Use **Real-Time Dashboard (FraudMonitoringDashboard)** with 30-second auto-refresh, connected to FraudEventhouse, combined with **Activator (FraudAlerts)** for automated notifications.

## Alternatives Considered

| Option | Pros | Cons | Why Rejected |
| ------ | ---- | ---- | ------------ |
| Power BI Report | Rich visualizations, familiar to BI teams | Requires scheduled refresh, not truly real-time | Operations team needs live data, not 15-minute snapshots |
| Power BI Dashboard | Can pin live tiles | Limited KQL support, refresh not as fast as Real-Time Dashboard | Eventhouse data best served by native Real-Time Dashboard |
| Paginated Report | Pixel-perfect formatting, great for printing | Batch-oriented, no real-time capability | Designed for reporting, not monitoring |
| Scorecard | Good for KPIs and targets | No time-series, limited for operational monitoring | Too simple for fraud pattern visualization |
| Custom application | Maximum flexibility | Requires development and maintenance | Over-engineering for standard dashboard use case |

## Consequences

### Benefits

- Sub-minute visibility into transaction patterns (30-second refresh)
- Native KQL integration with Eventhouse data
- Activator provides push notifications without polling
- Tiles can embed KQL queries from FraudPatternQueries directly

### Costs

- Real-Time Dashboard tiles must be configured manually in portal
- Activator rules configured via UI (not CLI)
- Less formatting flexibility than Power BI Report

### Mitigations

- Document tile configuration in deployment handoff
- Pre-define KQL queries in FraudPatternQueries for easy pinning
- Use Power BI Report for detailed historical analysis (separate from ops monitoring)

## References

- Decision guide: [decisions/visualization-selection.md](../../../../decisions/visualization-selection.md)
- Dashboard configuration: [handoff.md](../../deployments/handoff.md#phase-5-monitoring--alerting)
