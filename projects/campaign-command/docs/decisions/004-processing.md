# ADR-004: Processing Selection

## Status

Accepted

**Date:** 2026-03-09
**Deciders:** fabric-architect agent + user confirmation

## Context

Batch path needs Python/Spark transforms: sentiment scoring, regional ROI aggregation, data quality before loading to Warehouse. Speed path needs real-time aggregations on social streams in Eventhouse. Team is code-first.

## Decision

Use **Notebook** for batch transforms (Python/Spark, Lakehouse → Warehouse) and **KQL Queryset** for real-time stream aggregations.

## Alternatives Considered

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| Spark Job Definition | Production CI/CD ready | Less interactive for dev | Notebook via Pipeline sufficient initially |
| Dataflow Gen2 | Visual, low-code | Not code-first; limited NLP | Team prefers Python; sentiment needs libraries |
| Stored Procedures | T-SQL native | Only Warehouse; can't process raw LH | Raw processing needs Spark first |

## Consequences

### Benefits
- Notebook gives full Python ecosystem for sentiment NLP
- KQL Queryset provides optimized time-series aggregations
- Both are code-first, matching team preference

### Costs
- Notebook requires Environment with dependencies
- KQL learning curve for team

### Mitigations
- Environment pre-configured with sentiment analysis libraries
- KQL patterns documented; Eventhouse has built-in editor

## References

- Decision guide: [decisions/processing-selection.md](../../../decisions/processing-selection.md)
- Related: [ADR-001](./001-task-flow.md), [ADR-002](./002-storage.md), [ADR-003](./003-ingestion.md)
