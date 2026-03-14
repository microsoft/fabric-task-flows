# Tester Review Schema

> Schema for `/fabric-test` Mode 0 output (DRAFT architecture testability review).
> Save as: `_projects/[name]/docs/tester-review.md`

Use the YAML template below. Every field has a max length noted in comments.
Do NOT add prose sections outside this structure. The architect parses this programmatically.

```yaml
project: ""                    # from architecture handoff
task_flow: ""                  # from architecture handoff
review_date: ""                # YYYY-MM-DD

# Each finding: max 1 sentence per field (≤15 words)
findings:
  - id: T-1
    area: ""                   # category — e.g., "AC specificity", "Test coverage"
    severity: green            # red | yellow | green
    finding: ""                # what you found (≤15 words)
    suggestion: ""             # recommended change (≤15 words)

untestable_criteria: []        # AC IDs that cannot be verified — e.g., ["AC-5", "AC-12"]

missing_coverage:              # items or configs with no acceptance criteria
  - item: ""                   # item name
    gap: ""                    # what's missing (≤15 words)

blockers:
  architecture: []             # decisions that must resolve before FINAL (≤15 words each)
  deployment: []               # infra/creds needed before deploy — do NOT block sign-off (≤15 words each)

# Summary — architect reads this first
assessment: testable           # testable | needs-refinement | major-gaps
review_outcome: approved       # approved | revise — drives iteration loop
must_fix: []                   # finding IDs
should_fix: []                 # finding IDs
review_iteration: 1            # current review cycle (1, 2, 3)
```

## Field Rules

- **`severity: red`** = Major testability gap. Architecture cannot be validated without changes.
- **`severity: yellow`** = Testability concern. Criteria are vague or coverage is incomplete.
- **`severity: green`** = Minor observation or confirmation that something is fine.
- **`untestable_criteria`** = AC IDs where "How to Verify" is impossible or meaningless. These block the test plan.
- **`missing_coverage`** = Items in the architecture handoff with zero acceptance criteria.
- **All text fields: max 15 words.** Concise findings only.
- **Do NOT re-state the architecture.** Reference items and ACs by ID.
- **Architecture blockers block sign-off.** Deployment blockers do NOT.
- **`review_outcome: approved`** = Architecture is testable. All ACs are measurable and verifiable.
- **`review_outcome: revise`** = Architecture has `red` severity testability gaps. Architect must revise and re-submit.
- **`review_iteration`** = Tracks which review cycle this is. Max 3 iterations — after 3, escalate to user.
