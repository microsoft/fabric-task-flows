# ADR-002: Storage Layer Selection

## Status

Accepted

**Date:** 2026-03-05  
**Deciders:** fabric-architect agent + user confirmation

## Context

The fraud detection system has two distinct data access patterns:

1. **Real-time queries** - Sub-second lookups for transaction scoring, time-windowed aggregations for fraud patterns, high-volume append operations
2. **Batch processing** - ML model training on historical data, exploratory analysis, Spark/Python workloads

These patterns have conflicting optimization requirements that cannot be served well by a single storage type.

## Decision

Use **dual storage**:

- **FraudEventhouse (Eventhouse)** - Real-time transaction store with KQL queries for streaming analytics
- **FraudLakehouse (Lakehouse)** - Historical transactions and ML training data with Spark access

## Alternatives Considered

| Option | Pros | Cons | Why Rejected |
| ------ | ---- | ---- | ------------ |
| Lakehouse only | Simpler architecture, single storage layer, native Spark | Cannot meet sub-second latency for streaming, not optimized for time-series | Real-time SLA requirement not achievable |
| Warehouse only | Strong T-SQL support, familiar to BI teams | No native streaming support, requires SQL expertise team lacks, poor Spark integration | Team skillset mismatch, no streaming capability |
| Eventhouse only | Excellent streaming, real-time queries, high ingestion throughput | Limited batch processing for ML training, KQL-only (no Spark) | ML training workload needs Spark, not supported |

## Consequences

### Benefits

- Real-time scoring queries execute in milliseconds (Eventhouse optimized)
- ML models train on full historical dataset with Spark (Lakehouse optimized)
- Each workload uses storage engine designed for its access pattern
- Clear data lifecycle: hot data in Eventhouse, cold data in Lakehouse

### Costs

- Two storage layers to provision and maintain
- Data duplication between Eventhouse and Lakehouse
- Team needs to learn KQL for real-time queries alongside existing Spark skills

### Mitigations

- Eventstream routes to both destinations from single ingestion point (no dual ingestion)
- 30-day retention in Eventhouse limits duplication cost
- KQL query patterns documented in FraudPatternQueries for team reference
- Consider Lakehouse shortcuts to Eventhouse for unified catalog view

## References

- Decision guide: [decisions/storage-selection.md](../../../../decisions/storage-selection.md)
- Task flow: [task-flows.md#lambda](../../../../task-flows.md#lambda)
