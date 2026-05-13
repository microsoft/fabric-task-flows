# Keep deployment-order.json hand-authored (slimmed)

We evaluated generating `_shared/registry/deployment-order.json` from `item-type-registry.json` and decided to keep it hand-authored — but slimmed to only irreducible fields.

## Analysis

| Metric | Value |
|--------|-------|
| Active code consumers | 4 scripts (handoff-scaffolder, taskflow-gen, decision-resolver, heal-orchestrator) |
| Total items | 148 across 12 task flows |
| Naming: display_name/alias variants | 19 of 37 unique types (not truly role-qualified) |
| True role instances | 9 (Lakehouse ×5, Notebook ×2, Warehouse ×1) |
| Phase predicts correct wave | Only 58/148 items (39%) — order is flow-specific |
| Same-phase deps (need intra-wave info) | 15 |
| Phase violations (reverse-direction deps) | 3 |

The `phase` field in item-type-registry correctly predicts deployment wave ordering for 89% of edges, but 15 same-phase dependencies and 3 reverse-direction dependencies (e.g., Notebook→ML Model in `basic-machine-learning-models`) require explicit `dependsOn` that cannot be inferred.

## Decision

Keep the file hand-authored with these irreducible fields per item:

- **`itemType`** — role-qualified display name (consumed by 4 scripts for rendering)
- **`order`** — wave code, derivable from phase but kept for readability
- **`dependsOn`** — the DAG edges (15 same-phase + 3 violations prove these are irreducible)
- **`requiredFor`** — used by `_purpose_from()` in handoff-scaffolder for purpose generation (96/134 values are descriptive text, not just item names)
- **`alternativeGroup`** — which items are interchangeable (consumed by decision-resolver)
- **`optional`** — which items can be skipped

**Removed** (dead fields with zero code consumers):
- `notes` — 17 items had human-only annotations; no script reads them

## Considered Options

1. **Generate from registry + per-flow YAML** — Rejected: the "source YAML" would contain the same domain knowledge as the current JSON, just with an extra indirection layer and a build step.

2. **Derive entirely from `phase` field** — Rejected: phase gives wave buckets but not intra-wave deps (15 same-phase edges) or the 3 reverse-direction edges. Also cannot produce the 96 descriptive `requiredFor` values used for purpose generation.

3. **Keep hand-authored, slimmed** (chosen) — removed dead `notes` field; all remaining fields have active code consumers.

## Future Considerations

- **Normalize `itemType` to registry keys** — 19 names are just display_name/alias variants (e.g., "Copy Job" = `CopyJob`). Scripts could resolve display names at render time. Deferred: requires updating 4 consumer scripts + test assertions.
- **Derive `order` from `phase` at runtime** — **NOT VIABLE**. Testing showed 90/148 items (61%) have `order` values that diverge from `phase`-derived waves. Each task flow defines its own relative ordering (e.g., GraphQL API is wave 2 in `app-backend` but `phase=Transformation` would place it at wave 4). The `order` field is irreducible task-flow-specific knowledge.

## Consequences

- `deployment-order.json` remains the authoritative source for deployment sequencing — agents use `registry_loader.get_deployment_items()`.
- New task flows require manual authoring of their deployment order section.
- The 37 role-qualified item names (e.g., "Lakehouse Bronze", "Copy Job") intentionally diverge from registry keys — this is display/role labeling, not a bug.
