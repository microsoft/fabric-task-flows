```yaml
# Tester Review — /fabric-test Mode 0
# Schema: .github/skills/fabric-design/schemas/tester-review.md
project: campaign-command
task_flow: lambda
review_date: 2026-03-09

findings:
  - id: T-1
    area: Missing coverage
    severity: yellow
    finding: No acceptance criteria for cc-spark-environment item
    suggestion: Add AC for Environment existence and published status
  - id: T-2
    area: AC specificity
    severity: yellow
    finding: AC-6 says Direct Lake but verify method doesn't check query mode
    suggestion: Verify via Semantic Model TMDL or REST API expression property
  - id: T-3
    area: Test coverage
    severity: green
    finding: All 13 items have at least one structural AC
    suggestion: No change needed (except Environment per T-1)
  - id: T-4
    area: AC type
    severity: green
    finding: AC-10 correctly typed as data_flow — threshold rules need config
    suggestion: No change needed
  - id: T-5
    area: Missing coverage
    severity: yellow
    finding: No AC for KQL Database if added per engineer review F-5
    suggestion: Add AC for KQL Database existence within Eventhouse

untestable_criteria: []

missing_coverage:
  - item: cc-spark-environment
    gap: No AC verifying Environment exists and is published
  - item: KQL Database (if added)
    gap: No AC verifying KQL Database created within Eventhouse

blockers:
  architecture: []
  deployment:
    - Google Analytics and social media API credentials needed before ingestion config

assessment: testable
review_outcome: approved
must_fix: []
should_fix: ["T-1", "T-2", "T-5"]
review_iteration: 1
```
