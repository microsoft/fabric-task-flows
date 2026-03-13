# Test Plan Schema

> Schema for `/fabric-test` Mode 1 output (Test Plan from FINAL architecture).
> Save as: `_projects/[name]/prd/test-plan.md`

Use the YAML template below. Every field has a max length noted in comments.
Prose sections are constrained — word limits noted inline.

```yaml
project: ""                    # from architecture handoff
task_flow: ""                  # from architecture handoff
architecture_date: ""          # YYYY-MM-DD — when FINAL handoff was produced
test_plan_date: ""             # YYYY-MM-DD

# Map each AC from the architecture handoff to a validation method
criteria_mapping:
  - ac_id: AC-1                # ID from architecture handoff
    type: structural           # structural | data-flow
    phase: ""                  # e.g., "Foundation" — from validation-checklists.json
    test_method: ""            # how to verify (≤20 words — e.g., fabric-cicd or REST API call)

# Items/configs that MUST work for the project to succeed
critical_verification:
  - ""                         # ≤20 words each — e.g., "Eventhouse receives and routes IoT events within 10 seconds"

# Failure scenarios the engineer should set up for
edge_cases:
  - ""                         # ≤20 words each — e.g., "Empty Lakehouse tables at deploy time"

blockers:
  architecture: []             # block sign-off — decisions still unresolved (≤15 words each)
  deployment: []               # block engineer — infra/creds needed (≤15 words each)
```

## Field Rules

- **`criteria_mapping`** = One entry per AC from the architecture handoff. Do NOT re-state the full criterion text — just the AC ID + how to test it.
- **`type: structural`** = Verifiable immediately after deployment (item exists, config correct).
- **`type: data-flow`** = Verifiable only after data sources and connections are configured.
- **`critical_verification`** = The 3-5 most important things. Not every AC — just the ones that define project success.
- **`edge_cases`** = Scenarios the engineer should be aware of during deployment. Max 5.
- **All text fields: max 20 words.** The AC detail lives in the architecture handoff — don't duplicate it.
