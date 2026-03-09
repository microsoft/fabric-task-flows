```yaml
project: campaign-command
task_flow: lambda
phase: deploy
iteration: 1
started: "2026-03-09T03:10:00Z"
last_updated: "2026-03-09T03:16:00Z"

items:
  - name: cc_raw_lakehouse
    wave: 1
    status: completed
    attempts: 1
    last_error: ""
    last_attempt: "2026-03-09T03:10:10Z"
  - name: cc_gold_warehouse
    wave: 1
    status: completed
    attempts: 1
    last_error: ""
    last_attempt: "2026-03-09T03:10:15Z"
  - name: cc_stream_eventhouse
    wave: 1
    status: completed
    attempts: 1
    last_error: ""
    last_attempt: "2026-03-09T03:10:20Z"
  - name: cc_stream_kqldb
    wave: 1
    status: completed
    attempts: 1
    last_error: ""
    last_attempt: "2026-03-09T03:10:25Z"
  - name: cc_spark_environment
    wave: 2
    status: completed
    attempts: 1
    last_error: ""
    last_attempt: "2026-03-09T03:11:00Z"
  - name: cc_batch_pipeline
    wave: 2
    status: completed
    attempts: 1
    last_error: ""
    last_attempt: "2026-03-09T03:11:10Z"
  - name: cc_social_eventstream
    wave: 2
    status: completed
    attempts: 1
    last_error: ""
    last_attempt: "2026-03-09T03:11:15Z"
  - name: cc_transform_nb
    wave: 3
    status: completed
    attempts: 1
    last_error: ""
    last_attempt: "2026-03-09T03:12:00Z"
  - name: cc_stream_kql
    wave: 3
    status: completed
    attempts: 1
    last_error: ""
    last_attempt: "2026-03-09T03:12:10Z"
  - name: cc_campaign_sem
    wave: 4
    status: completed
    attempts: 1
    last_error: ""
    last_attempt: "2026-03-09T03:13:00Z"
  - name: cc_rt_dashboard
    wave: 4
    status: skipped
    attempts: 0
    last_error: "Portal-only item; documented as manual step M-1"
    last_attempt: ""
  - name: cc_roi_report
    wave: 5
    status: completed
    attempts: 1
    last_error: ""
    last_attempt: "2026-03-09T03:14:00Z"
  - name: cc_campaign_agent
    wave: 5
    status: skipped
    attempts: 0
    last_error: "Portal-only item; documented as manual step M-2"
    last_attempt: ""
  - name: cc_alerts_activator
    wave: 6
    status: skipped
    attempts: 0
    last_error: "Portal-only item; documented as manual step M-3"
    last_attempt: ""

waves:
  - id: 1
    status: completed
    items_total: 4
    items_completed: 4
  - id: 2
    status: completed
    items_total: 3
    items_completed: 3
  - id: 3
    status: completed
    items_total: 2
    items_completed: 2
  - id: 4
    status: partial
    items_total: 2
    items_completed: 1
  - id: 5
    status: partial
    items_total: 2
    items_completed: 1
  - id: 6
    status: partial
    items_total: 1
    items_completed: 0

resume_from:
  wave: null
  item: null
  reason: "Deployment complete; portal-only items pending manual creation"
```
