```yaml
# Engineer Review — /fabric-deploy Mode 0
# Schema: .github/skills/fabric-design/schemas/engineer-review.md
project: campaign-command
task_flow: lambda
review_date: 2026-03-09
architecture_version: draft

findings:
  - id: F-1
    area: Wave optimization
    severity: yellow
    finding: Environment can deploy parallel with Pipeline and Eventstream in Wave 3
    suggestion: Merge Wave 2 into Wave 3 to reduce total waves from 7 to 6
  - id: F-2
    area: Manual step
    severity: yellow
    finding: Semantic Model needs manual Direct Lake connection on first deploy
    suggestion: Document as manual post-deployment step in deployment handoff
  - id: F-3
    area: Portal-only item
    severity: green
    finding: Data Agent (cc-campaign-agent) is portal-only, no CLI support
    suggestion: Already noted as LC; document portal creation in deploy handoff
  - id: F-4
    area: Dependency graph
    severity: green
    finding: All dependencies correctly reflect lambda dual-path structure
    suggestion: No change needed
  - id: F-5
    area: Missing item
    severity: yellow
    finding: No KQL Database item listed; Eventhouse needs one for KQL queries
    suggestion: Add KQL Database as Wave 1 item, depends on Eventhouse

wave_optimization:
  current_waves: 7
  proposed_waves: 6
  changes:
    - description: Merge Environment into Wave 3 (parallel with ingestion)
      reason: Environment depends only on Wave 1, same as Pipeline/Eventstream

cli_verification:
  - item_type: DataAgent
    api_path: items
    supported: false
    fallback: portal
  - item_type: Reflex
    api_path: items
    supported: false
    fallback: portal

prerequisites:
  - id: D-1
    description: Google Analytics API credentials and OAuth setup
    status: external
    deployment_impact: Blocks cc-batch-pipeline configuration
  - id: D-2
    description: Social media streaming API keys (Twitter/X, etc.)
    status: external
    deployment_impact: Blocks cc-social-eventstream configuration

assessment: needs-changes
review_outcome: approved
must_fix: []
should_fix: ["F-1", "F-2", "F-5"]
no_change: ["F-3", "F-4"]
review_iteration: 1
```
