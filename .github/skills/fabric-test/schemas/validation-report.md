# Validation Report Schema

> Schema for `/fabric-test` Mode 2 output (post-deployment validation).
> Save as: `_projects/[name]/prd/validation-report.md`

Use the YAML template below. Every field has a max length noted in comments.
The `validation_context` and `future_considerations` sections allow brief prose.

```yaml
project: ""                    # from deployment handoff
task_flow: ""                  # from deployment handoff
date: ""                       # YYYY-MM-DD
status: passed                 # passed | partial | failed

phases:
  - name: Foundation
    status: pass               # pass | warn | fail
    notes: ""                  # ≤15 words — omit if clean pass
  - name: Environment
    status: pass
    notes: ""
  - name: Ingestion
    status: pass
    notes: ""
  - name: Transformation
    status: pass
    notes: ""
  - name: Visualization
    status: pass
    notes: ""
  - name: CI/CD Readiness
    status: na                 # pass | warn | fail | na
    notes: ""

items_validated:
  - name: ""                   # item name
    verified: true             # true | false
    method: ""                 # e.g., "REST API" (≤10 words)
    issue: ""                  # only if verified: false (≤15 words)

manual_steps:
  - id: ""                     # e.g., "M-1"
    confirmed: true            # true | false
    action_needed: ""          # only if confirmed: false (≤15 words)

issues:
  - severity: high             # high | medium | low
    item: ""                   # item name
    issue: ""                  # ≤15 words
    action: ""                 # recommended fix (≤15 words)

next_steps:
  - ""                         # ≤20 words each
```

After the YAML block, include two **brief** prose sections:

```markdown
### Validation Context
<!-- Max 100 words. Explain what successful validation means for this
     specific architecture. Tie back to the original requirements and
     acceptance criteria. -->

### Future Considerations
<!-- Max 100 words. Operational learnings discovered during validation —
     scaling concerns, monitoring gaps, improvement opportunities.
     The documenter uses this for lessons learned. -->
```

## Field Rules

- **`status: passed`** = All phases pass, all items verified, no high-severity issues.
- **`status: partial`** = Some phases warn or items have issues, but no blockers.
- **`status: failed`** = Any phase fails or high-severity issues exist.
- **`items_validated`** = One entry per item from the deployment handoff. Reference by name.
- **`issues`** = Only list actual problems found. Don't list things that passed.
- **Do NOT re-state acceptance criteria text.** Reference AC IDs from the architecture handoff.
- **Validation Context is MANDATORY.** The documenter requires it.
- **Future Considerations is MANDATORY.** The documenter requires it.
