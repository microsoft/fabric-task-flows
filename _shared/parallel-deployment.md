# Parallel Deployment

Fabric item deployments can be significantly accelerated by deploying independent items concurrently. This guide explains how to analyze deployment order tables and generate parallel scripts.

## Dependency-Wave Analysis

Every deployment diagram in `diagrams/[task-flow].md` includes a **Deployment Order** table with a "Depends On" column. This is the dependency graph. To parallelize:

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

## Bash Parallel Template

Use this pattern in generated deployment scripts:

```bash
#!/bin/bash
set -e

WORKSPACE_ID="${WORKSPACE_ID:?'Set WORKSPACE_ID environment variable'}"
FAILED=0
TOTAL_START=$(date +%s)

# --- Parallel execution helper ---
# Usage: run_wave "Wave Name" "cmd1" "cmd2" "cmd3"
run_wave() {
    local wave_name="$1"
    shift
    local pids=()
    local cmds=()
    local wave_start=$(date +%s)

    echo ""
    echo "═══════════════════════════════════════════"
    echo "  $wave_name"
    echo "═══════════════════════════════════════════"

    for cmd in "$@"; do
        echo "  ► Starting: $cmd"
        eval "$cmd" &
        pids+=($!)
        cmds+=("$cmd")
    done

    local wave_failed=0
    for i in "${!pids[@]}"; do
        if ! wait "${pids[$i]}"; then
            echo "  ✗ FAILED: ${cmds[$i]}"
            wave_failed=$((wave_failed + 1))
            FAILED=$((FAILED + 1))
        else
            echo "  ✓ Done: ${cmds[$i]}"
        fi
    done

    local wave_end=$(date +%s)
    echo "  ⏱ $wave_name completed in $((wave_end - wave_start))s ($wave_failed failures)"

    if [ $wave_failed -gt 0 ]; then
        echo "ERROR: $wave_name had $wave_failed failure(s). Stopping."
        exit 1
    fi
}

# --- Deploy in dependency waves ---

run_wave "WAVE 1: Foundation" \
    "fab mkdir $WORKSPACE_ID.Workspace/item1.Lakehouse" \
    "fab mkdir $WORKSPACE_ID.Workspace/item2.Warehouse" \
    "fab mkdir $WORKSPACE_ID.Workspace/item3.Eventhouse"

run_wave "WAVE 2: Environment + Speed Layer" \
    "fab mkdir $WORKSPACE_ID.Workspace/item4.Environment" \
    "fab mkdir $WORKSPACE_ID.Workspace/item5.Eventstream"

# ... continue for each wave ...

# --- Summary ---
TOTAL_END=$(date +%s)
echo ""
echo "═══════════════════════════════════════════"
echo "  DEPLOYMENT COMPLETE"
echo "  Total time: $((TOTAL_END - TOTAL_START))s"
echo "  Failures: $FAILED"
echo "═══════════════════════════════════════════"
```

## Error Handling

- **Fail-fast on wave failure** — if any item in a wave fails, stop the entire deployment. Later waves depend on earlier ones.
- **Capture PIDs** — track which background processes belong to which items for clear error reporting.
- **Exit codes** — `wait $PID` returns the exit code of the background process. Check it per-item.

## Timing Instrumentation

Always include timing output so users can measure the speedup:

- Log wave start/end timestamps
- Log per-item completion
- Log total deployment time at the end
- This makes it easy to compare sequential vs. parallel performance

## When Not to Parallelize

Some operations must remain sequential:

- **Items that need IDs from earlier items** — e.g., Report creation needs Semantic Model ID from `fab get`. Put these in a later wave.
- **`fab set` configuration calls** — these reference items that must already exist. They run after the `fab mkdir` wave.
- **Verification phase** — `fab exists` checks are read-only and fast; sequential is fine.

## Applying to Any Task Flow

1. Open `diagrams/[task-flow].md`
2. Find the "Deployment Order" table
3. Read the "Depends On" column
4. Group items by dependency depth
5. Generate waves using the bash template above

The engineer agent should perform this analysis automatically when generating deployment scripts.
