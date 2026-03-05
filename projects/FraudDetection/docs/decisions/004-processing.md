# ADR-004: Processing/Transformation Selection

## Status

Accepted

**Date:** 2026-03-05  
**Deciders:** fabric-architect agent + user confirmation

## Context

The fraud detection system requires two types of processing:

1. **ML model training** - Feature engineering, model training, evaluation, and registration using Python/Spark
2. **Real-time analytics** - Pattern detection queries, aggregations, anomaly identification on streaming data

These processing needs align with different engines and query languages.

## Decision

Use **dual processing**:

- **Notebook (FraudModelTraining)** - ML model training with Spark/Python, bound to Lakehouse and Environment
- **KQL Queryset (FraudPatternQueries)** - Real-time pattern detection queries against Eventhouse

## Alternatives Considered

| Option | Pros | Cons | Why Rejected |
| ------ | ---- | ---- | ------------ |
| Notebook only | Single processing paradigm, team expertise | Cannot query Eventhouse efficiently, not designed for real-time | Real-time queries would require awkward workarounds |
| Spark Job Definition | Production-ready scheduling, parameterized | Same limitations as Notebook for real-time | Better for scheduled ETL than ad-hoc analytics |
| Dataflow Gen2 | Low-code transformations | No ML support, batch-oriented, limited for streaming | Cannot support model training or real-time queries |
| KQL Queryset only | Excellent real-time queries | No Spark/Python, cannot train ML models | ML workload requires Python libraries (scikit-learn, xgboost) |
| Stored Procedures (Warehouse) | T-SQL familiar to some teams | No Spark, limited ML libraries, batch-oriented | Team lacks T-SQL skills, ML training not feasible |

## Consequences

### Benefits

- ML training uses familiar Python/Spark with MLflow integration
- Real-time queries leverage KQL's time-series optimization
- Clear separation: Notebook for training, KQL for serving
- Environment isolates ML dependencies (scikit-learn, xgboost, mlflow)

### Costs

- Team must maintain both Python notebooks and KQL queries
- Two query languages to learn and support
- Environment publish time adds deployment delay (10+ minutes)

### Mitigations

- Pre-built KQL query templates in FraudPatternQueries reduce learning curve
- Environment dependencies documented for reproducibility
- MLflow experiment tracking provides model lineage

## References

- Decision guide: [decisions/processing-selection.md](../../../../decisions/processing-selection.md)
- Notebook implementation: [FraudModelTraining.py](../../deployments/notebooks/FraudModelTraining.py)
- KQL queries: [fraud-pattern-queries.kql](../../deployments/queries/fraud-pattern-queries.kql)
