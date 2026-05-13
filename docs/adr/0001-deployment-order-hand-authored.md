# Keep deployment-order.json hand-authored

We evaluated generating `_shared/registry/deployment-order.json` from `item-type-registry.json` + task flow definitions, and decided to keep it hand-authored. The file encodes role-qualified instance graphs (e.g., "Lakehouse Bronze → Lakehouse Silver → Lakehouse Gold") whose dependency relationships are task-flow-specific design decisions — not derivable from item-type metadata alone.

## Considered Options

1. **Generate from registry + per-flow YAML** — each task flow declares instances and dependencies in a source file; a script resolves types against the registry and emits deployment-order.json. Rejected: the "source YAML" would contain the same domain knowledge as the current JSON, just with an extra indirection layer and a build step.

2. **Derive from item-type-registry `phase` field** — use the coarse wave ordering (Foundation → Ingestion → Transformation → Visualization) to auto-assign deployment waves. Rejected: `phase` gives wave buckets but not fine-grained inter-item dependencies (`dependsOn`, `requiredFor`, `alternativeGroup`, `optional`). Many items share a phase but have specific ordering constraints within it.

3. **Keep hand-authored** (chosen) — the 37KB file covers 12 task flows / 148 items. It changes only when task flows are added or restructured — roughly quarterly. The maintenance cost is low; the semantic richness (role-qualified names, alternative groups, optional flags, notes) cannot be mechanically inferred.

## Consequences

- `deployment-order.json` remains the authoritative source for deployment sequencing — agents use `registry_loader.get_deployment_items()`.
- New task flows require manual authoring of their deployment order section.
- The 37 role-qualified item names (e.g., "Lakehouse Bronze", "Copy Job") intentionally diverge from registry keys — this is display/role labeling, not a bug.
