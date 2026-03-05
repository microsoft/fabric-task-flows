# ADR-003: Ingestion Approach Selection

## Status

Accepted

**Date:** 2026-03-05  
**Deciders:** fabric-architect agent + user confirmation

## Context

Transaction data arrives continuously from payment processors via Event Hub. The system must:

- Ingest transactions in real-time with minimal latency
- Route data to both Eventhouse (streaming) and Lakehouse (batch)
- Support in-stream transformations for ML scoring
- Handle high throughput during peak transaction periods

## Decision

Use **Eventstream** as the primary ingestion method, connecting Event Hub source to both Eventhouse and Lakehouse destinations with an in-stream ML scoring transformation.

## Alternatives Considered

| Option | Pros | Cons | Why Rejected |
| ------ | ---- | ---- | ------------ |
| Pipeline (batch) | Robust orchestration, retry handling, familiar to ETL teams | Batch-only, cannot meet real-time latency requirements | Adds minutes of latency to fraud detection |
| Copy Job | Simple configuration, good for bulk loads | No streaming support, scheduled execution only | Cannot process continuous transaction stream |
| Dataflow Gen2 | Low-code transformations, Power Query interface | Not designed for streaming, batch-oriented | Same latency issues as Pipeline |
| Direct SDK ingestion | Maximum control, custom code | Requires custom development, no low-code management | Over-engineering for standard Event Hub integration |

## Consequences

### Benefits

- Sub-second ingestion latency from Event Hub
- Single ingestion point for multiple destinations (DRY principle)
- In-stream ML scoring without separate processing step
- Low-code configuration via Fabric portal

### Costs

- Eventstream requires manual configuration for Event Hub connection
- ML scoring node depends on model endpoint availability
- Limited transformation complexity compared to Notebook

### Mitigations

- Document Event Hub connection setup in deployment handoff
- Deploy ML model first, then configure scoring node
- Use KQL for complex post-ingestion transformations in Eventhouse

## References

- Decision guide: [decisions/ingestion-selection.md](../../../../decisions/ingestion-selection.md)
- Eventstream configuration: [handoff.md](../../deployments/handoff.md#phase-3-ingestion)
