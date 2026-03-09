```yaml
# Validation Report — /fabric-test Mode 2
# Schema: .github/skills/fabric-test/schemas/validation-report.md
project: campaign-command
task_flow: lambda
date: "2026-03-09"
status: passed

phases:
  - name: Foundation
    status: passed
    notes: "Lakehouse, Warehouse, Eventhouse, KQL Database all exist"
  - name: Environment
    status: passed
    notes: "Environment created and published"
  - name: Ingestion
    status: passed
    notes: "Pipeline and Eventstream deployed"
  - name: Transformation
    status: passed
    notes: "Notebook and KQL Queryset deployed"
  - name: Serving Layer
    status: partial
    notes: "Semantic Model + Report deployed; RT Dashboard pending portal creation"
  - name: AI & Governance
    status: partial
    notes: "Data Agent and Activator pending portal creation"

items_validated:
  - name: cc_raw_lakehouse
    type: Lakehouse
    status: exists
  - name: cc_gold_warehouse
    type: Warehouse
    status: exists
  - name: cc_stream_eventhouse
    type: Eventhouse
    status: exists
  - name: cc_stream_kqldb
    type: KQLDatabase
    status: exists
  - name: cc_spark_environment
    type: Environment
    status: exists
  - name: cc_batch_pipeline
    type: DataPipeline
    status: exists
  - name: cc_social_eventstream
    type: Eventstream
    status: exists
  - name: cc_transform_nb
    type: Notebook
    status: exists
  - name: cc_stream_kql
    type: KQLQueryset
    status: exists
  - name: cc_campaign_sem
    type: SemanticModel
    status: exists
  - name: cc_rt_dashboard
    type: Dashboard
    status: pending_manual
  - name: cc_roi_report
    type: Report
    status: exists
  - name: cc_campaign_agent
    type: DataAgent
    status: pending_manual
  - name: cc_alerts_activator
    type: Reflex
    status: pending_manual

manual_steps:
  - id: M-1
    description: "Create RT Dashboard in portal"
    status: pending
  - id: M-2
    description: "Create Data Agent in portal"
    status: pending
  - id: M-3
    description: "Create Activator in portal"
    status: pending
  - id: M-4
    description: "Configure Semantic Model Direct Lake connection"
    status: pending

issues: []

next_steps:
  - "Complete manual portal steps M-1 through M-4"
  - "Configure Google Analytics and AdWords API credentials in Pipeline"
  - "Configure social media API keys in Eventstream"
  - "Run first batch pipeline to populate Lakehouse"
```

### Validation Context

All 11 fabric-cicd-deployable items verified via REST API — they exist in the workspace. Three portal-only items (Real-Time Dashboard, Data Agent, Activator) are documented as pending manual steps and do not block structural validation. The Semantic Model requires manual Direct Lake connection configuration before data flows. Validation status is **passed** for structural criteria.

### Future Considerations

Once API credentials are configured and data flows, re-run validation to verify data-flow acceptance criteria (AC-12, AC-13). Monitor Eventstream throughput during peak social media periods. Consider adding Variable Library if multi-environment deployment is needed later.
