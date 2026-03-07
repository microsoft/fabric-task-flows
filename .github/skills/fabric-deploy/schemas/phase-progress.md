# Phase Progress Schema

> Schema for tracking per-item progress within deploy and validate phases.
> Save as: `projects/[name]/prd/phase-progress.md`
> Read/updated by `@fabric-engineer` and `@fabric-tester` to enable resume-from-failure.

Use the YAML template below. The agent updates this file as it progresses through items.
On restart or retry, the agent reads this file to know where to resume.

```yaml
project: ""                    # from architecture handoff
task_flow: ""                  # from architecture handoff
phase: deploy                  # deploy | validate | remediate
iteration: 1                   # current iteration within this phase
started: ""                    # ISO 8601 timestamp
last_updated: ""               # ISO 8601 timestamp

items:
  - name: ""                   # item name — e.g., "goi-lakehouse"
    wave: 1                    # deployment wave number
    status: not_started        # not_started | in_progress | completed | failed | retrying | skipped
    attempts: 0                # number of attempts
    last_error: ""             # error from most recent failure (≤20 words)
    last_attempt: ""           # ISO 8601 timestamp

waves:
  - id: 1
    status: not_started        # not_started | in_progress | completed | partial
    items_total: 0
    items_completed: 0

# Resumability
resume_from:
  wave: null                   # wave to resume from (null = start from beginning)
  item: null                   # specific item to resume (null = start of wave)
  reason: ""                   # why we're resuming (≤15 words)
```

## Field Rules

- **`status: not_started`** = Agent hasn't attempted this item yet.
- **`status: in_progress`** = Agent is currently working on this item.
- **`status: completed`** = Item successfully deployed/validated.
- **`status: failed`** = Item failed after max attempts for this iteration.
- **`status: retrying`** = Item failed but is being retried.
- **`status: skipped`** = Item intentionally skipped (document reason in `last_error`).
- **`attempts`** = Incremented each time the agent tries this item. Useful for identifying consistently problematic items.
- **`resume_from`** = Set when the agent is interrupted or the session ends. The next invocation reads this to continue.
- **All text fields: max 20 words.**

## Usage Protocol

### Deploy Phase
1. Engineer reads `phase-progress.md` at start of deployment
2. If `resume_from` is set → skip to that wave/item
3. For each item: set `status: in_progress` → deploy → set `status: completed` or `status: failed`
4. Update wave status after all items in wave are attempted
5. If session ends mid-wave → set `resume_from` with current position

### Validate Phase
1. Tester reads `phase-progress.md` at start of validation
2. Validates items in order, updating status as it goes
3. Failed items get error context in `last_error`
4. On remediation re-validate: only re-check items with `status: failed`

### Remediation Phase
1. Engineer reads items with `status: failed`
2. Attempts fixes, updates `status` and `attempts`
3. Resets `status: not_started` for items that need re-validation by tester
