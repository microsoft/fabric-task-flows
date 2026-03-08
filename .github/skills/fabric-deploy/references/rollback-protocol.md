# Rollback & Error Recovery

Protocol for handling deployment failures in Microsoft Fabric item deployments.

## On Wave Failure

1. **Stop immediately** — do not proceed to subsequent waves
2. **Log the failure** — record which item failed, the error message, and the deployment method attempted
3. **Assess the state** — list what exists in the workspace via `GET /v1/workspaces/{ws_id}/items`

## Cleanup Decision

Ask the user which recovery path to take:

| Option | When to Use | Action |
|--------|-------------|--------|
| **Retry** | Transient error (timeout, auth token expired) | Re-authenticate (`az login`) and retry the failed wave |
| **Skip & Continue** | Non-critical optional item failed (e.g., Scorecard, Activator) | Mark item as skipped in handoff, proceed to next wave |
| **Rollback** | Fundamental issue (wrong config, missing dependency) | Delete items created in the failed wave via REST API, then optionally delete prior waves |
| **Leave for debugging** | Unknown error requiring investigation | Leave all items in place, flag in handoff as partial deployment |

## Rollback Commands

```bash
# Delete a specific item via REST API
curl -X DELETE "https://api.fabric.microsoft.com/v1/workspaces/{ws_id}/items/{item_id}" \
  -H "Authorization: Bearer $TOKEN"

# List all items in workspace to verify cleanup
curl "https://api.fabric.microsoft.com/v1/workspaces/{ws_id}/items" \
  -H "Authorization: Bearer $TOKEN"
```

## Partial Deployment Handoff

If deployment ends in a partial state, the handoff to `/fabric-test` must clearly indicate:
- Which waves completed successfully
- Which wave failed and why
- Which items exist vs. which are missing
- Whether the user chose to leave items for debugging or rolled back

The `/fabric-test` agent will adjust validation to only check deployed items.
