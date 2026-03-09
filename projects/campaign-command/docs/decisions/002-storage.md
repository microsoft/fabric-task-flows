# ADR-002: Storage Layer Selection

## Status

Accepted

**Date:** 2026-03-09
**Deciders:** fabric-architect agent + user confirmation

## Context

Lambda requires separate storage for batch and real-time. Batch path needs Spark processing (raw → curated) plus T-SQL gold layer for BI. Speed path needs sub-second time-series queries on social streams. Team is code-first.

## Decision

Use **Lakehouse** (raw batch, Spark), **Warehouse** (gold layer, T-SQL ROI reporting), and **Eventhouse** (real-time social sentiment, KQL).

## Alternatives Considered

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| Lakehouse only | Single engine, simpler | No streaming; SQL endpoint read-only | Can't serve T-SQL gold or real-time |
| Warehouse only | Strong T-SQL | No Spark, no streaming | Code-first needs Spark; no real-time |
| Eventhouse only | Excellent streaming | Limited batch for ML/transforms | Batch is half the workload |

## Consequences

### Benefits
- Each engine optimized for its workload
- Lakehouse gives Spark/Python for code-first team
- Warehouse provides T-SQL gold for Reports and Data Agent
- Eventhouse enables sub-second social queries

### Costs
- Three storage items to provision
- Data flows through multiple hops (LH → WH)

### Mitigations
- Lambda keeps layers independent
- Warehouse is single gold source for Reports and Data Agent

## References

- Decision guide: [decisions/storage-selection.md](../../../decisions/storage-selection.md)
- Related: [ADR-001](./001-task-flow.md)
