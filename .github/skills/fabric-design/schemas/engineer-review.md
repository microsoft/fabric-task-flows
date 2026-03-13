# Engineer Review Schema

> Schema for `/fabric-deploy` Mode 0 output (DRAFT architecture review).
> Save as: `_projects/[name]/prd/engineer-review.md`

Use the YAML template below. Every field has a max length noted in comments.
Do NOT add prose sections outside this structure. The architect parses this programmatically.

```yaml
project: ""                    # from architecture handoff
task_flow: ""                  # from architecture handoff
review_date: ""                # YYYY-MM-DD
architecture_version: draft    # draft | final

# Each finding: max 1 sentence per field (≤15 words)
findings:
  - id: F-1
    area: ""                   # category — e.g., "Wave structure", "Missing step"
    severity: green            # red | yellow | green
    finding: ""                # what you found (≤15 words)
    suggestion: ""             # recommended change (≤15 words)

wave_optimization:
  current_waves: 0
  proposed_waves: 0
  changes:                     # list only if proposing changes
    - description: ""          # e.g., "Merge waves 2+3" (≤10 words)
      reason: ""               # why (≤15 words)

cli_verification:              # only list items with issues or unknowns
  - item_type: ""
    api_path: ""               # REST API path (e.g., "eventhouses")
    supported: true            # true | false | unknown
    fallback: ""               # "portal" | "rest-api" | "" (if supported)

prerequisites:                 # only list items needing attention
  - id: ""                     # e.g., D-1
    description: ""            # ≤15 words
    status: external           # blocking | external | ready
    deployment_impact: ""      # what it blocks (≤10 words)

# Summary — architect reads this first
assessment: needs-changes      # ready | needs-changes | blocked
review_outcome: approved       # approved | revise — drives iteration loop
must_fix: []                   # finding IDs — e.g., ["F-6", "F-7"]
should_fix: []                 # finding IDs
no_change: []                  # finding IDs
review_iteration: 1            # current review cycle (1, 2, 3)
```

## Field Rules

- **`severity: red`** = Must fix before FINAL. Deployment will fail without this change.
- **`severity: yellow`** = Should fix. Improves reliability or efficiency.
- **`severity: green`** = No change needed, or nice-to-have.
- **All text fields: max 15 words.** If you need more context, the architect will ask.
- **Do NOT re-state the architecture.** Reference items by name (e.g., "goi-eventhouse"), not by re-describing what they do.
- **Wave optimization is optional.** Only include if proposing structural changes to the wave plan.
- **`review_outcome: approved`** = Architecture is deployment-ready. No blocking issues remain.
- **`review_outcome: revise`** = Architecture has `red` severity findings. Architect must revise and re-submit for review.
- **`review_iteration`** = Tracks which review cycle this is. Max 3 iterations — after 3, escalate to user regardless of outcome.
