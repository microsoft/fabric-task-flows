```yaml
# Deployment Handoff — /fabric-deploy
# Schema: .github/skills/fabric-deploy/schemas/deployment-handoff.md
project: campaign-command
task_flow: lambda
validation_checklist: "validation/lambda.md"
deployment_tool: fabric-cicd
parameterization: env-vars

items:
  - name: cc_raw_lakehouse
    type: Lakehouse
    wave: 1
    status: deployed
    command: "fabric-cicd deploy_with_config (config.yml)"
  - name: cc_gold_warehouse
    type: Warehouse
    wave: 1
    status: deployed
    command: "fabric-cicd deploy_with_config (config.yml)"
  - name: cc_stream_eventhouse
    type: Eventhouse
    wave: 1
    status: deployed
    command: "fabric-cicd deploy_with_config (config.yml)"
  - name: cc_stream_kqldb
    type: KQLDatabase
    wave: 1
    status: deployed
    command: "REST API POST /kqlDatabases"
    notes: "Created within cc_stream_eventhouse"
  - name: cc_spark_environment
    type: Environment
    wave: 2
    status: deployed
    command: "fabric-cicd deploy_with_config (config.yml)"
    notes: "Publish required before Notebook binding"
  - name: cc_batch_pipeline
    type: DataPipeline
    wave: 2
    status: deployed
    command: "fabric-cicd deploy_with_config (config.yml)"
  - name: cc_social_eventstream
    type: Eventstream
    wave: 2
    status: deployed
    command: "fabric-cicd deploy_with_config (config.yml)"
  - name: cc_transform_nb
    type: Notebook
    wave: 3
    status: deployed
    command: "fabric-cicd deploy_with_config (config.yml)"
  - name: cc_stream_kql
    type: KQLQueryset
    wave: 3
    status: deployed
    command: "fabric-cicd deploy_with_config (config.yml)"
  - name: cc_campaign_sem
    type: SemanticModel
    wave: 4
    status: deployed
    command: "fabric-cicd deploy_with_config (config.yml)"
    notes: "Manual Direct Lake connection required post-deploy"
  - name: cc_rt_dashboard
    type: Dashboard
    wave: 4
    status: skipped
    command: "Portal manual creation"
    notes: "Real-Time Dashboard is portal-only; see M-1"
  - name: cc_roi_report
    type: Report
    wave: 5
    status: deployed
    command: "fabric-cicd deploy_with_config (config.yml)"
  - name: cc_campaign_agent
    type: DataAgent
    wave: 5
    status: skipped
    command: "Portal manual creation"
    notes: "Data Agent is portal-only; see M-2"
  - name: cc_alerts_activator
    type: Reflex
    wave: 6
    status: skipped
    command: "Portal manual creation"
    notes: "Activator is portal-only; see M-3"

waves:
  - id: 1
    items: [cc_raw_lakehouse, cc_gold_warehouse, cc_stream_eventhouse, cc_stream_kqldb]
    status: success
  - id: 2
    items: [cc_spark_environment, cc_batch_pipeline, cc_social_eventstream]
    status: success
  - id: 3
    items: [cc_transform_nb, cc_stream_kql]
    status: success
  - id: 4
    items: [cc_campaign_sem, cc_rt_dashboard]
    status: partial
  - id: 5
    items: [cc_roi_report, cc_campaign_agent]
    status: partial
  - id: 6
    items: [cc_alerts_activator]
    status: partial

manual_steps:
  completed: []
  pending:
    - id: M-1
      description: "Create Real-Time Dashboard in portal, bind to KQL Database"
      blocked_by: "Portal access to workspace"
    - id: M-2
      description: "Create Data Agent in portal, bind to Semantic Model"
      blocked_by: "Semantic Model Direct Lake connection configured"
    - id: M-3
      description: "Create Activator in portal, configure ROI threshold rules"
      blocked_by: "Eventstream data flowing"
    - id: M-4
      description: "Configure Semantic Model Direct Lake connection manually"
      blocked_by: "First refresh after manual connection setup"

known_issues: []
```

### Implementation Notes

Deploy scripts generated via `deploy-script-gen.py` using `fabric-cicd`. All item names auto-converted to underscores per learnings (hyphens rejected by Eventstream, Lakehouse). Three portal-only items (Real-Time Dashboard, Data Agent, Activator) documented as manual steps. KQL Database created via REST API within Eventhouse since `fabric-cicd` doesn't support nested KQL DB creation directly. Environment requires publish confirmation before Notebook binding. Semantic Model needs manual Direct Lake connection configuration before first refresh succeeds.

### Configuration Rationale

| Item | Setting | Why |
|------|---------|-----|
| cc_raw_lakehouse | Default config | Raw batch landing zone |
| cc_gold_warehouse | Default config | T-SQL gold layer for BI |
| cc_stream_eventhouse | Default config | Real-time social sentiment store |
| cc_spark_environment | Python libraries | Sentiment NLP dependencies |
| cc_campaign_sem | Direct Lake mode | Optimal query performance on Warehouse |
| cc_social_eventstream | Underscore naming | Eventstream rejects hyphens |
