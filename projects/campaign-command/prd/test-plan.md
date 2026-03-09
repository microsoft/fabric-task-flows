```yaml
# Test Plan — /fabric-test Mode 1
# Schema: .github/skills/fabric-test/schemas/test-plan.md
project: campaign-command
task_flow: lambda
architecture_date: 2026-03-09
test_plan_date: 2026-03-09

criteria_mapping:
  - ac_id: AC-1
    type: structural
    checklist_ref: "validation/lambda.md#foundation"
    test_method: "GET /workspaces/{id}/lakehouses, /warehouses, /eventhouses — verify 3 items exist"
  - ac_id: AC-2
    type: structural
    checklist_ref: "validation/lambda.md#foundation"
    test_method: "GET /workspaces/{id}/kqlDatabases — verify cc-stream-kqldb exists under Eventhouse"
  - ac_id: AC-3
    type: structural
    checklist_ref: "validation/lambda.md#environment"
    test_method: "GET /workspaces/{id}/items?type=Environment — verify exists and publishInfo.state=Published"
  - ac_id: AC-4
    type: structural
    checklist_ref: "validation/lambda.md#ingestion"
    test_method: "GET /workspaces/{id}/items?type=Eventstream — verify cc-social-eventstream exists"
  - ac_id: AC-5
    type: structural
    checklist_ref: "validation/lambda.md#ingestion"
    test_method: "GET /workspaces/{id}/items?type=DataPipeline — verify cc-batch-pipeline exists"
  - ac_id: AC-6
    type: structural
    checklist_ref: "validation/lambda.md#transformation"
    test_method: "GET /workspaces/{id}/items?type=Notebook — verify cc-transform-nb exists"
  - ac_id: AC-7
    type: structural
    checklist_ref: "validation/lambda.md#transformation"
    test_method: "GET /workspaces/{id}/items?type=KQLQueryset — verify cc-stream-kql exists"
  - ac_id: AC-8
    type: structural
    checklist_ref: "validation/lambda.md#serving-layer"
    test_method: "GET /workspaces/{id}/semanticModels — verify cc-campaign-sem exists, check expression for Direct Lake"
  - ac_id: AC-9
    type: structural
    checklist_ref: "validation/lambda.md#serving-layer"
    test_method: "GET /workspaces/{id}/reports — verify cc-roi-report exists and datasetId matches semantic model"
  - ac_id: AC-10
    type: structural
    checklist_ref: "validation/lambda.md#serving-layer"
    test_method: "GET /workspaces/{id}/items?type=Dashboard — verify cc-rt-dashboard exists"
  - ac_id: AC-11
    type: structural
    checklist_ref: "validation/lambda.md#ai-governance"
    test_method: "GET /workspaces/{id}/items?type=DataAgent — verify cc-campaign-agent exists"
  - ac_id: AC-12
    type: data_flow
    checklist_ref: "validation/lambda.md#monitoring-ml"
    test_method: "GET /workspaces/{id}/items?type=Reflex — verify cc-alerts-activator exists"
  - ac_id: AC-13
    type: manual
    checklist_ref: "validation/lambda.md#serving-layer"
    test_method: "Manual: verify Semantic Model refresh succeeds after Direct Lake connection config"

critical_verification:
  - "Eventhouse receives social sentiment events via Eventstream within 10 seconds"
  - "Batch pipeline successfully ingests from Google Analytics and AdWords APIs"
  - "Semantic Model Direct Lake connection configured and first refresh succeeds"
  - "Data Agent returns accurate answers to campaign performance questions"
  - "Real-Time Dashboard shows live social sentiment with sub-second latency"

edge_cases:
  - "Empty Lakehouse tables at deploy time before first batch pipeline run"
  - "Environment publish delay — Notebook may fail if Environment not yet published"
  - "Semantic Model first refresh fails until manual Direct Lake connection is configured"
  - "Social media API rate limits may throttle Eventstream during high-volume periods"
  - "Data Agent may return incomplete answers if Semantic Model has not refreshed"

blockers:
  architecture: []
  deployment:
    - "Google Analytics API OAuth credentials required for cc-batch-pipeline"
    - "Social media streaming API keys required for cc-social-eventstream"
    - "Fabric workspace with sufficient capacity must be provisioned"
```
