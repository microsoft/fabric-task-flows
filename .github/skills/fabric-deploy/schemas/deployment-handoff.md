# Deployment Handoff Schema

> Schema for `/fabric-deploy` post-deployment output.
> Save as: `projects/[name]/prd/deployment-handoff.md`

Use the YAML template below. Every field has a max length noted in comments.
The `implementation_notes` and `configuration_rationale` sections allow brief prose.

```yaml
project: ""                    # from architecture handoff
task_flow: ""                  # from architecture handoff
validation_checklist: ""       # path — e.g., "validation/lambda.md"
deployment_tool: fab           # fab | fabric-cicd
parameterization: none         # none | parameter-yml | env-vars

items:
  - name: ""                   # item name — e.g., "goi-eventhouse"
    type: ""                   # Fabric item type — e.g., "Eventhouse"
    wave: 1                    # wave number
    status: deployed           # deployed | failed | skipped
    command: ""                # fab command used (full command string)
    notes: ""                  # only if noteworthy (≤15 words) — omit if clean deploy

waves:
  - id: 1
    items: []                  # item names in this wave
    status: success            # success | partial | failed

manual_steps:
  completed:
    - id: ""                   # e.g., "M-1"
      description: ""          # ≤15 words
  pending:
    - id: ""
      description: ""          # ≤15 words
      blocked_by: ""           # what's needed (≤10 words)

known_issues:
  - item: ""                   # item name
    issue: ""                  # ≤15 words
    impact: low                # high | medium | low

cicd_notes:                    # omit section for single-environment projects
  - ""                         # ≤20 words each — connection/parameterization notes
```

After the YAML block, include two **brief** prose sections:

```markdown
### Implementation Notes
<!-- Max 150 words. Document ONLY deviations from the architecture handoff,
     workarounds applied, or commands that failed. If deployment matched
     the handoff exactly, write "No deviations." -->

### Configuration Rationale
<!-- Use a compact table. Max 10 words per "Why" cell. -->
| Item | Setting | Why |
|------|---------|-----|
| [name] | [setting] | [≤10 words] |
```

## Field Rules

- **`status: deployed`** = `fab mkdir` succeeded and `fab exists` confirms the item.
- **`status: failed`** = `fab mkdir` failed. Include error in `notes`.
- **`status: skipped`** = Intentionally not deployed. Include reason in `notes`.
- **`command`** = The exact `fab mkdir` or `fab set` command used. This is auditable evidence.
- **Do NOT re-describe items.** The architecture handoff has descriptions. This document records what was actually deployed and what happened.
- **Implementation Notes are MANDATORY** even if "No deviations." The documenter requires them.
- **Configuration Rationale is MANDATORY.** The documenter requires it.
