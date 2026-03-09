# ADR-003: Ingestion Approach

## Status

Accepted

**Date:** 2026-03-09
**Deciders:** fabric-architect agent + user confirmation

## Context

Two ingestion paths: batch from Google Analytics/AdWords APIs (large volume, orchestration needed) and real-time from social media sentiment feeds (continuous streaming). Team is code-first.

## Decision

Use **Data Pipeline** for batch ingestion and **Eventstream** for real-time social media streaming.

## Alternatives Considered

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| Dataflow Gen2 (batch) | Visual transforms | Power Query, not code-first | Team prefers code; complex API auth better in Pipeline |
| Copy Job (batch) | Simple, no-code | No orchestration, no API connectors | Needs multi-step orchestration |
| Notebook (standalone) | Full code control | No built-in scheduling/retry | Pipeline provides orchestration layer |

## Consequences

### Benefits
- Pipeline orchestrates multi-source batch ingestion with retry logic
- Eventstream handles continuous social feeds with backpressure
- Both paths independently schedulable and monitorable

### Costs
- Pipeline requires API connector configuration
- Eventstream requires social media API integration setup

### Mitigations
- Pipeline can invoke Notebooks for custom API logic
- Eventstream supports custom endpoints for any streaming source

## References

- Decision guide: [decisions/ingestion-selection.md](../../../decisions/ingestion-selection.md)
- Related: [ADR-001](./001-task-flow.md), [ADR-002](./002-storage.md)
