# Rollback & Error Recovery

Protocol for handling deployment failures in Microsoft Fabric item deployments.

## On Wave Failure

1. **Stop immediately** — do not proceed to subsequent waves
2. **Log the failure** — record which item failed, the error message, and the `fab` command that was attempted
3. **Assess the state** — list what exists in the workspace with `fab ls <ws>.Workspace -l`

## Cleanup Decision

Ask the user which recovery path to take:

| Option | When to Use | Action |
|--------|-------------|--------|
| **Retry** | Transient error (timeout, auth token expired) | Re-run `fab auth login` and retry the failed wave |
| **Skip & Continue** | Non-critical optional item failed (e.g., Scorecard, Activator) | Mark item as skipped in handoff, proceed to next wave |
| **Rollback** | Fundamental issue (wrong config, missing dependency) | Delete items created in the failed wave, then optionally delete prior waves |
| **Leave for debugging** | Unknown error requiring investigation | Leave all items in place, flag in handoff as partial deployment |

## Rollback Commands

```bash
# Delete a specific item
fab delete <ws>.Workspace/<item>.Type

# Delete all items in a wave (example - Wave 2 of Lambda)
fab delete <ws>.Workspace/<name>.Environment
fab delete <ws>.Workspace/<name>.Eventhouse
fab delete <ws>.Workspace/<name>.DataPipeline

# Verify cleanup
fab ls <ws>.Workspace -l
```

## Partial Deployment Handoff

If deployment ends in a partial state, the handoff to `/fabric-test` must clearly indicate:
- Which waves completed successfully
- Which wave failed and why
- Which items exist vs. which are missing
- Whether the user chose to leave items for debugging or rolled back

The `/fabric-test` agent will adjust validation to only check deployed items.
