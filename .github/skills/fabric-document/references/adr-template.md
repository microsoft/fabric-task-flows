# ADR Template

> Architecture Decision Record (ADR) template for documenting design decisions.
>
> ⚠️ This template is duplicated in `fabric-design/references/adr-template.md` — keep both in sync.

Use this template when the `fabric-documenter` agent generates decision records, or when manually documenting architecture choices.

---

## Template

```markdown
# ADR-NNN: [Decision Title]

## Status

[Accepted | Superseded | Deprecated]

**Date:** [YYYY-MM-DD]
**Deciders:** [who made this decision - agent pipeline or human]
**Supersedes:** [ADR-XXX if this replaces a previous decision]

## Context

[Describe the problem, constraints, and requirements that led to this decision. Include:
- What problem are we solving?
- What constraints exist (technical, business, team skillset)?
- What requirements must be met?]

## Decision

[State the decision clearly and concisely. What did we choose?]

## Alternatives Considered

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| [Alternative 1] | [benefits] | [drawbacks] | [specific reason] |
| [Alternative 2] | [benefits] | [drawbacks] | [specific reason] |

## Consequences

### Benefits
- [What this decision enables]
- [Advantages gained]

### Costs
- [What this decision limits or prevents]
- [Trade-offs accepted]

### Mitigations
- [How we address the costs/limitations]
- [Workarounds or future improvements planned]

## References

- Decision guide: [decisions/xxx-selection.md](../../../decisions/xxx-selection.md)
- Task flow: [task-flows.md#section](../../../task-flows.md#section)
- Related ADRs: [ADR-XXX](./xxx-related.md)
```

---

## Example

```markdown
# ADR-002: Storage Layer Selection

## Status

Accepted

**Date:** 2026-03-05
**Deciders:** fabric-architect agent + user confirmation

## Context

The fraud detection system requires:
- Real-time transaction scoring (sub-second latency)
- Historical data for ML model training (batch processing)
- SQL access for analyst queries

Team has strong Python/Spark skills and limited SQL expertise.

## Decision

Use **Eventhouse** for real-time transaction data and **Lakehouse** for historical/ML training data.

## Alternatives Considered

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| Lakehouse only | Simpler architecture, single storage layer | Cannot meet sub-second latency for streaming | Real-time requirement not achievable |
| Warehouse only | Strong SQL support, familiar to BI teams | No native streaming support, requires SQL expertise team lacks | Team skillset mismatch, no streaming |
| Eventhouse only | Excellent streaming, real-time queries | Limited batch processing for ML training, KQL learning curve | ML training workload needs Spark |

## Consequences

### Benefits
- Real-time scoring meets SLA (<1 second)
- ML models can train on full historical dataset
- Each workload uses optimal storage engine

### Costs
- Two storage layers to maintain
- Data duplication between Eventhouse and Lakehouse
- Team needs to learn KQL for real-time queries

### Mitigations
- Use Eventstream to route data to both destinations (single ingestion)
- Document KQL patterns in team wiki
- Consider Lakehouse SQL endpoint for analysts who prefer SQL

## References

- Decision guide: [decisions/storage-selection.md](../../../decisions/storage-selection.md)
- Task flow: [task-flows.md#lambda](../../../task-flows.md#lambda)
```

---

## Usage Guidelines

1. **Number ADRs sequentially** within each project's `docs/[workspace]/decisions/` folder
2. **Use descriptive titles** that indicate what was decided (not the question)
3. **Always include alternatives** - this is what makes ADRs valuable for understanding "why"
4. **Link to decision guides** so readers can explore the full context
5. **Keep language accessible** - stakeholders beyond engineers may read these
6. **Update status** when decisions change (Superseded) or become obsolete (Deprecated)

## ADR Numbering Convention

| Number | Decision Type |
|--------|---------------|
| 001 | Task flow selection |
| 002 | Storage layer |
| 003 | Ingestion approach |
| 004 | Processing/transformation |
| 005 | Visualization |
| 006+ | Project-specific decisions |
