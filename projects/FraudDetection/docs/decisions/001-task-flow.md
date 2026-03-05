# ADR-001: Task Flow Selection

## Status

Accepted

**Date:** 2026-03-05  
**Deciders:** fabric-architect agent + user confirmation

## Context

The fraud detection system requires:

- **Real-time transaction scoring** with sub-second latency for immediate fraud alerts
- **Historical data storage** for ML model training on transaction patterns
- **ML model training pipeline** with experimentation and versioning
- **Live monitoring dashboards** for operations team oversight

The team has strong Python/Spark skills and needs both streaming and batch processing capabilities.

## Decision

Use the **Lambda** task flow pattern, which processes batch and real-time data in one data process flow while maintaining clear separation between the two processing modes.

## Alternatives Considered

| Option | Pros | Cons | Why Rejected |
| ------ | ---- | ---- | ------------ |
| Medallion | Progressive data quality layers, simpler architecture | No native real-time streaming, batch-only | Cannot meet sub-second alerting requirement |
| Event Analytics | Excellent real-time processing, KQL native | Limited batch processing for ML training | ML model training needs Spark/Python, not just KQL |
| Event Medallion | Combines streaming with medallion layers | More complex than needed, primarily for event-driven BI | Over-engineered for single-use-case fraud detection |
| Basic Machine Learning Models | Focused on ML workflow | No real-time ingestion or alerting | Missing streaming requirement entirely |

## Consequences

### Benefits

- Real-time fraud scoring meets <1 second SLA
- ML models can train on historical data without impacting streaming
- Clear separation between hot path (Eventhouse) and cold path (Lakehouse)
- Activator enables automated alerts without custom code

### Costs

- Two storage layers to maintain (Eventhouse + Lakehouse)
- Team needs to learn KQL for real-time queries
- More complex architecture than single-layer approach

### Mitigations

- Eventstream routes data to both destinations (single ingestion point)
- KQL query patterns documented in FraudPatternQueries
- Clear phase separation in deployment reduces complexity

## References

- Task flow: [task-flows.md#lambda](../../../../task-flows.md#lambda)
- Deployment diagram: [diagrams/lambda.md](../../../../diagrams/lambda.md)
- Validation checklist: [validation/lambda.md](../../../../validation/lambda.md)
