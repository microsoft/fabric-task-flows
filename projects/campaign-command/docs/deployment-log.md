# Deployment Log

**Deployed:** 2026-03-09
**Task flow:** lambda
**Validation Status:** Passed (structural) — 11/14 items deployed, 3 pending manual portal creation

## Items Deployed

| Wave | Item | Type | Status | Notes |
|------|------|------|--------|-------|
| 1 | cc_raw_lakehouse | Lakehouse | ✅ Deployed | |
| 1 | cc_gold_warehouse | Warehouse | ✅ Deployed | |
| 1 | cc_stream_eventhouse | Eventhouse | ✅ Deployed | |
| 1 | cc_stream_kqldb | KQL Database | ✅ Deployed | REST API within Eventhouse |
| 2 | cc_spark_environment | Environment | ✅ Deployed | Publish required before Notebook |
| 2 | cc_batch_pipeline | Data Pipeline | ✅ Deployed | |
| 2 | cc_social_eventstream | Eventstream | ✅ Deployed | Underscore naming (rejects hyphens) |
| 3 | cc_transform_nb | Notebook | ✅ Deployed | |
| 3 | cc_stream_kql | KQL Queryset | ✅ Deployed | |
| 4 | cc_campaign_sem | Semantic Model | ✅ Deployed | Manual Direct Lake config needed |
| 4 | cc_rt_dashboard | RT Dashboard | ⏳ Pending | Portal-only (M-1) |
| 5 | cc_roi_report | Report | ✅ Deployed | |
| 5 | cc_campaign_agent | Data Agent | ⏳ Pending | Portal-only (M-2) |
| 6 | cc_alerts_activator | Activator | ⏳ Pending | Portal-only (M-3) |

## Implementation Notes

All fabric-cicd-deployable items created successfully. Item names auto-converted to underscores (hyphens rejected by Eventstream, Lakehouse). KQL Database created via REST API within Eventhouse. Three portal-only items documented as manual steps.

## Manual Steps

### Pending
- **M-1:** Create Real-Time Dashboard in portal, bind to KQL Database
- **M-2:** Create Data Agent in portal, bind to Semantic Model
- **M-3:** Create Activator in portal, configure ROI threshold rules
- **M-4:** Configure Semantic Model Direct Lake connection manually

## Issues & Resolutions

| Issue | Resolution | Status |
|-------|-----------|--------|
| No issues | — | — |

## Lessons Learned

- Monitor Eventstream throughput during peak social media periods
- Consider adding Variable Library if multi-environment deployment needed later
- Data Agent is GA — no tenant admin prerequisites needed
