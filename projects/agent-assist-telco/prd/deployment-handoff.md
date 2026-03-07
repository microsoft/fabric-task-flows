```yaml
# Deployment Handoff — @fabric-engineer
# Schema: _shared/schemas/deployment-handoff.md
project: agent-assist-telco
task_flow: lambda
deployment_mode: design-only
validation_checklist: "validation/lambda.md"
deployment_tool: fab
parameterization: env-vars

items:
  - name: call-transcripts-lakehouse
    type: Lakehouse
    wave: 1
    status: scripted
    command: "fab mkdir <ws>.Workspace/call-transcripts-lakehouse.Lakehouse"
  - name: call-analytics-warehouse
    type: Warehouse
    wave: 1
    status: scripted
    command: "fab mkdir <ws>.Workspace/call-analytics-warehouse.Warehouse"
  - name: call-events-eventhouse
    type: Eventhouse
    wave: 1
    status: scripted
    command: "fab mkdir <ws>.Workspace/call-events-eventhouse.Eventhouse"
  - name: call-events-kqldb
    type: KQL Database
    wave: 1
    status: scripted
    command: "fab mkdir <ws>.Workspace/call-events-kqldb.KQLDatabase -P eventhouseId=<id>"
  - name: spark-env
    type: Environment
    wave: 1
    status: scripted
    command: "fab mkdir <ws>.Workspace/spark-env.Environment && fab publish <ws>.Workspace/spark-env.Environment"
  - name: call-stream-eventstream
    type: Eventstream
    wave: 2
    status: scripted
    command: "fab mkdir <ws>.Workspace/call-stream-eventstream.Eventstream"
  - name: crm-sync-pipeline
    type: Pipeline
    wave: 2
    status: scripted
    command: "fab mkdir <ws>.Workspace/crm-sync-pipeline.DataPipeline"
  - name: transcript-etl-notebook
    type: Notebook
    wave: 3
    status: scripted
    command: "fab mkdir <ws>.Workspace/transcript-etl-notebook.Notebook"
  - name: call-insights-kql
    type: KQL Queryset
    wave: 3
    status: scripted
    command: "fab mkdir <ws>.Workspace/call-insights-kql.KQLQueryset"
  - name: call-analytics-model
    type: Semantic Model
    wave: 4
    status: scripted
    command: "fab mkdir <ws>.Workspace/call-analytics-model.SemanticModel"
  - name: call-ops-rt-dash
    type: Real-Time Dashboard
    wave: 4
    status: manual
    command: "portal-only — no CLI support"
  - name: call-analytics-report
    type: Report
    wave: 5
    status: scripted
    command: "fab mkdir <ws>.Workspace/call-analytics-report.Report -P semanticModelId=<id>"
  - name: call-alert-activator
    type: Activator
    wave: 5
    status: manual
    command: "portal-only — no CLI support"
  - name: transcript-ml-experiment
    type: Experiment
    wave: 6
    status: scripted
    command: "fab mkdir <ws>.Workspace/transcript-ml-experiment.MLExperiment"
  - name: transcript-ml-model
    type: ML Model
    wave: 6
    status: scripted
    command: "fab mkdir <ws>.Workspace/transcript-ml-model.MLModel"
  - name: ml-scoring-notebook
    type: Notebook
    wave: 6
    status: scripted
    command: "fab mkdir <ws>.Workspace/ml-scoring-notebook.Notebook"

waves:
  - id: 1
    name: "Foundation + Compute"
    items: [call-transcripts-lakehouse, call-analytics-warehouse, call-events-eventhouse, call-events-kqldb, spark-env]
    status: scripted
  - id: 2
    name: "Ingestion"
    items: [call-stream-eventstream, crm-sync-pipeline]
    status: scripted
  - id: 3
    name: "Processing"
    items: [transcript-etl-notebook, call-insights-kql]
    status: scripted
  - id: 4
    name: "Serving"
    items: [call-analytics-model, call-ops-rt-dash]
    status: scripted (1 portal-only)
  - id: 5
    name: "Visualization"
    items: [call-analytics-report, call-alert-activator]
    status: scripted (1 portal-only)
  - id: 6
    name: "ML"
    items: [transcript-ml-experiment, transcript-ml-model, ml-scoring-notebook]
    status: scripted

manual_steps:
  completed: []
  pending:
    - id: M-1
      description: "Configure telephony/transcription source in Eventstream"
    - id: M-2
      description: "Set up Dataverse Fabric Link for CRM entity sync"
    - id: M-3
      description: "Configure Activator alert thresholds for queue SLA"
    - id: M-4
      description: "Build Real-Time Dashboard tiles in portal"
    - id: M-5
      description: "Configure Activator rules in portal"

known_issues:
  - "RT Dashboard and Activator require portal creation (no CLI)"
  - "Notebook-to-Lakehouse binding may need manual setup if fab set fails"
  - "Environment publish may fail if capacity is paused — publish manually in portal"

cicd_notes:
  - "Scripts require FABRIC_CAPACITY_ID env var (or interactive prompt) for workspace capacity assignment"
  - "Scripts use FABRIC_WORKSPACE_NAME env var with interactive fallback"
  - "Event Hub and Dataverse URLs are required prompts with skip-with-warning option"
  - "Scripts run fab auth status preflight — authenticate with fab auth login before running"

preflight_checks:
  - "fab CLI installed (pip install ms-fabric-cli)"
  - "fab auth login completed (script verifies via fab auth status)"
  - "Fabric capacity ID available (Admin portal → Capacities → copy GUID)"

scripts:
  - path: "deployments/deploy-agent-assist-telco.sh"
    format: bash
  - path: "deployments/deploy-agent-assist-telco.ps1"
    format: powershell
```

### Implementation Notes

Design-only deployment: generated both `.sh` and `.ps1` scripts following the lambda wave structure (6 waves, 16 items including KQL Database). Scripts run preflight checks for `fab` CLI and `fab auth status` before deployment. Capacity ID is a required prompt — workspace creation and all subsequent items fail without it. Two items (RT Dashboard, Activator) are portal-only and documented as manual steps M-4/M-5. KQL Database is auto-created after Eventhouse using the captured eventhouse ID. Environment is published after creation so notebooks can attach. Event Hub and Dataverse are required prompts with skip-with-warning for structural-only deployment.

### Configuration Rationale

| Item | Setting | Why |
|------|---------|-----|
| Lakehouse | Default (no schemas) | Single-domain; schemas not needed |
| Notebooks | Bound to call-transcripts-lakehouse | Default lakehouse for ETL + ML |
| Report | semanticModelId parameter | Auto-bind to call-analytics-model |
| Semantic Model | Direct Lake | Fast BI without import refresh |
| Scripts | Env var + interactive prompts | Design-only; flexible runtime config |
