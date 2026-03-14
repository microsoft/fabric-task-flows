# Parallel Deployment

Fabric item deployments can be significantly accelerated by deploying independent items concurrently. This guide explains how to analyze deployment order tables and generate parallel scripts.

## Dependency-Wave Analysis

The canonical deployment order is accessible via `deployment_loader.get_deployment_items(task_flow)`. Do NOT read `_shared/registry/deployment-order.json` directly — use the Python tool. Each item includes `dependsOn` and `requiredFor` fields. To parallelize:

1. **Identify foundation items** — items with no dependencies (depth 0)
2. **Walk the graph** — for each remaining item, its depth = max(dependency depths) + 1
3. **Group by depth** — items at the same depth form a parallel wave
4. **Deploy wave by wave** — all items in a wave run concurrently; wait for all to complete before starting the next wave

### Example: Lambda Task Flow

The Lambda deployment order table resolves to 3 largely independent chains:

```
BATCH CHAIN:                      SPEED CHAIN:                   ML CHAIN:
Lakehouse ─┐                      Eventhouse ─┬─► Eventstream    Lakehouse ──┐
Warehouse ─┤                                  ├─► KQL Queryset   Environment ┤
           ├─► Environment                    ├─► RT Dashboard               ▼
           │       │                          └─► Activator      Experiment → ML Model
           │       ├─► Notebook
           │       ├─► Spark Job Def
           │       ▼
           ├─► Semantic Model ─► Report
```

This produces **5 waves** instead of 15 sequential calls:

| Wave | Items (deploy in parallel) | Blocked by |
|------|---------------------------|------------|
| 1 | Lakehouse, Warehouse, Eventhouse | — |
| 2 | Environment, Eventstream, KQL Queryset, RT Dashboard | Wave 1 |
| 3 | Pipeline, Notebook, Spark Job Def, Experiment, Activator | Wave 2 |
| 4 | Semantic Model, ML Model | Wave 3 |
| 5 | Report | Wave 4 (needs Semantic Model ID) |

**Key insight:** The speed layer items (Eventstream, KQL Queryset, RT Dashboard) only depend on Eventhouse — they can start in Wave 2 alongside Environment, rather than waiting for it.

## Deploy Script Generation

The `deploy-script-gen.py` script generates deployment scripts with wave-based parallelism built in. Use it instead of writing bash templates manually:

```bash
python .github/skills/fabric-deploy/scripts/deploy-script-gen.py --handoff _projects/[name]/prd/architecture-handoff.md
```

The generated scripts include parallel execution helpers, wave grouping, error handling (fail-fast on wave failure), and timing instrumentation.

## When Not to Parallelize

Some operations must remain sequential:

- **Items that need IDs from earlier items** — e.g., Report creation needs Semantic Model ID from the REST API. Put these in a later wave.
- **Configuration calls** — these reference items that must already exist. They run after the creation wave.
- **Verification phase** — REST API existence checks are read-only and fast; sequential is fine.

## Applying to Any Task Flow

1. Load deployment items: `from deployment_loader import get_deployment_items; items = get_deployment_items("[task-flow]")`
2. Read the `dependsOn` field for each item
3. Group items by dependency depth
4. Generate waves using the bash template above

> **⚠️ Do NOT read `diagrams/[task-flow].md` for deployment order.** Diagram files are for human visualization only. Use `deployment_loader.get_deployment_items()` for programmatic access.

The engineer agent should perform this analysis automatically when generating deployment scripts.
