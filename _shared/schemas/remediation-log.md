# Remediation Log Schema

> Schema for tracking issues found during validation that require engineer remediation.
> Save as: `projects/[name]/prd/remediation-log.md`
> Created by `@fabric-tester` (Mode 2), consumed by `@fabric-engineer` (remediation mode).

Use the YAML template below. The tester populates `issues` when validation finds deployment problems.
The engineer updates `status` and `resolution` fields after fixing each issue.

```yaml
project: ""                    # from deployment handoff
task_flow: ""                  # from deployment handoff
iteration: 1                   # current remediation cycle (1, 2, 3)
max_iterations: 3              # hard cap — escalate to user after this
created_date: ""               # YYYY-MM-DD
last_updated: ""               # YYYY-MM-DD

issues:
  - id: R-1
    source_phase: ""           # "Foundation" | "Environment" | "Ingestion" | etc.
    item: ""                   # item name — e.g., "goi-eventhouse"
    severity: high             # high | medium | low
    issue: ""                  # what failed (≤15 words)
    category: deployment       # deployment | configuration | transient | design
    routed_to: engineer        # engineer | architect | user
    status: open               # open | in-progress | resolved | escalated
    resolution: ""             # how it was fixed (≤15 words) — engineer fills this
    resolved_iteration: null   # iteration number when resolved

# Summary — updated each iteration
outcome: pending               # pending | remediated | escalated | max-iterations-reached
unresolved_count: 0            # number of open issues
```

## Field Rules

- **`category: deployment`** = Item wasn't created correctly, `fab` command failed, or item is missing. Route to engineer.
- **`category: configuration`** = Item exists but is misconfigured (wrong settings, missing connections). Route to engineer.
- **`category: transient`** = Timing issue (Environment publish delay, propagation lag). Engineer retries after wait.
- **`category: design`** = Architecture decision was wrong (wrong item type, missing item). Route to architect. Blocks further remediation.
- **`routed_to: engineer`** = Engineer should fix this in their next remediation pass.
- **`routed_to: architect`** = Design issue — cannot be fixed by engineer. Escalate.
- **`routed_to: user`** = External dependency (credentials, data source access). Escalate.
- **`outcome: remediated`** = All issues resolved. Tester should re-validate.
- **`outcome: escalated`** = Design issues or external blockers found. Pipeline pauses for human intervention.
- **`outcome: max-iterations-reached`** = Hit 3 remediation cycles without full resolution. Escalate to user.
- **All text fields: max 15 words.**
- **Do NOT re-state validation report content.** Reference issues by ID.

## Iteration Protocol

1. **Tester (Mode 2)** validates → finds issues → creates/updates remediation log with `status: open`
2. **Engineer (remediation)** reads log → fixes `deployment` and `configuration` issues → updates `status: resolved` + `resolution`
3. **Tester (Mode 2)** re-validates resolved items only → updates log
4. Repeat until `outcome: remediated` or `iteration >= max_iterations`
5. If `category: design` issues exist → `outcome: escalated` → pipeline pauses

## Completion Promise

The remediation loop exits when:
- ✅ All issues have `status: resolved` → `outcome: remediated` → proceed to Phase 4 (Document)
- 🛑 Any `category: design` issue exists → `outcome: escalated` → human intervention required
- 🛑 `iteration >= max_iterations` → `outcome: max-iterations-reached` → human intervention required
