# ADR-005: Visualization Selection

## Status

Accepted

**Date:** 2026-03-09
**Deciders:** fabric-architect agent + user confirmation

## Context

Two visualization needs: interactive ROI exploration for batch data, and live social sentiment monitoring. Execs also want a self-service chatbot handled via Data Agent on a Semantic Model.

## Decision

Use **Power BI Report** for batch ROI analysis, **Real-Time Dashboard** for live social sentiment, and **Data Agent** for exec self-service Q&A.

## Alternatives Considered

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| Report only | Simpler, fewer items | No sub-second social data | Real-time monitoring is a core need |
| Paginated Report | Pixel-perfect exports | No interactivity, no real-time | Execs need interactive exploration |
| Custom app for chatbot | Full control, richer UX | Requires dev, hosting, maintenance | Data Agent is GA, simpler, meets use case |

## Consequences

### Benefits
- Report provides rich interactive ROI analysis with regional drill-through
- RT Dashboard gives sub-second social sentiment visibility
- Data Agent enables natural language Q&A with zero app code

### Costs
- Two visualization items to maintain
- Data Agent limited to read-only queries

### Mitigations
- Report and RT Dashboard serve different audiences
- Read-only sufficient for exec Q&A

## References

- Decision guide: [decisions/visualization-selection.md](../../../decisions/visualization-selection.md)
- Related: [ADR-001](./001-task-flow.md), [ADR-002](./002-storage.md)
