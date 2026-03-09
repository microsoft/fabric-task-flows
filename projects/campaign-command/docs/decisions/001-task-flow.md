# ADR-001: Task Flow Selection

## Status

Accepted

**Date:** 2026-03-09
**Deciders:** fabric-architect agent + user confirmation

## Context

Campaign Command requires dual-velocity data processing: batch ingestion from Google Analytics and AdWords APIs for ROI reporting, plus real-time social media sentiment monitoring where "speed to share is EXTREMELY important." Additionally, execs want a self-service chatbot. Team is code-first with $500k ad spend and expects high volume.

## Decision

Use **Lambda** as the primary task flow with **Conversational Analytics** as an overlay for the exec Data Agent chatbot.

## Alternatives Considered

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| event-medallion | Strong streaming + quality layers | Batch analytics needs equal weight | Batch ROI reporting is as important as real-time |
| medallion | Proven data quality pattern | No native real-time path | Social sentiment speed requirement unmet |
| basic-data-analytics | Simplest architecture | No streaming at all | Real-time is a core requirement |

## Consequences

### Benefits
- Dual-path handles both batch and real-time optimally
- Layers are independently scalable
- Conversational-analytics overlay adds chatbot without complicating core pipeline

### Costs
- More items to deploy than single-velocity flows
- Team needs both Spark and KQL skills
- Three storage engines to manage

### Mitigations
- Lambda keeps layers independent — failures don't cascade
- Code-first team can handle both Spark and KQL
- Each storage engine is purpose-optimized

## References

- Decision guide: [decisions/storage-selection.md](../../../decisions/storage-selection.md)
- Task flow: [task-flows.md#lambda](../../../task-flows.md#lambda)
