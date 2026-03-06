## Test Plan

**Project:** chicago-bears-85
**Task flow:** medallion
**Architecture Date:** 2026-03-06
**Test Plan Date:** 2026-03-06

---

### Acceptance Criteria Mapping

| # | Criterion | Validation Checklist Reference | Test Method | `fab` CLI Command / Manual |
|---|-----------|-------------------------------|-------------|----------------------------|
| AC-01 | Workspace exists with capacity | validation/medallion.md — Phase 1: Foundation | `fab` CLI existence check + manual capacity verification | `fab exists chicago-bears-85.Workspace` → then **Manual:** Fabric portal → Workspace Settings → verify Fabric capacity (F-SKU) assigned |
| AC-02 | Bronze Lakehouse created with schemas enabled | validation/medallion.md — Phase 1: Foundation | `fab` CLI existence check + property inspection | `fab exists chicago-bears-85.Workspace/chicago-bears-85-bronze.Lakehouse` then `fab get chicago-bears-85.Workspace/chicago-bears-85-bronze.Lakehouse -q properties` → verify `enableSchemas=true` |
| AC-03 | Silver Lakehouse created with schemas enabled | validation/medallion.md — Phase 1: Foundation | `fab` CLI existence check + property inspection | `fab exists chicago-bears-85.Workspace/chicago-bears-85-silver.Lakehouse` then `fab get chicago-bears-85.Workspace/chicago-bears-85-silver.Lakehouse -q properties` → verify `enableSchemas=true` |
| AC-04 | Warehouse Gold created | validation/medallion.md — Phase 1: Foundation (Option B) | `fab` CLI existence check | `fab exists chicago-bears-85.Workspace/chicago-bears-85-gold.Warehouse` |
| AC-05 | Environment published | validation/medallion.md — Phase 2: Environment | `fab` CLI existence check + status inspection | `fab exists chicago-bears-85.Workspace/chicago-bears-85-env.Environment` then `fab get chicago-bears-85.Workspace/chicago-bears-85-env.Environment -q properties` → verify Status = Published |
| AC-06 | Copy Job configured with Oracle source | validation/medallion.md — Phase 3: Ingestion | `fab` CLI existence check + manual connection verification | `fab exists chicago-bears-85.Workspace/chicago-bears-85-ingest.CopyJob` then **Manual:** Fabric portal → Copy Job settings → verify Oracle connection GUID bound and incremental refresh enabled |
| AC-07 | Oracle tables land in Bronze | validation/medallion.md — Phase 3: Ingestion | `fab` CLI listing + SQL query | `fab ls chicago-bears-85.Workspace/chicago-bears-85-bronze.Lakehouse` → verify expected tables present; then SQL query via Bronze SQL endpoint: `SELECT COUNT(*) FROM [schema].[table]` → rows > 0 for each expected table |
| AC-08 | Bronze→Silver deduplication succeeds | validation/medallion.md — Phase 4: Transformation | SQL query on Silver SQL endpoint | `SELECT COUNT(*) AS total_rows, COUNT(DISTINCT [pk_column]) AS distinct_pks FROM [schema].[table]` → total_rows = distinct_pks (zero duplicates) for each migrated table |
| AC-09 | Silver→Gold curation completes | validation/medallion.md — Phase 4: Transformation | `fab` CLI listing + SQL query | `fab ls chicago-bears-85.Workspace/chicago-bears-85-gold.Warehouse` → expected Gold tables/views exist; SQL query via Warehouse endpoint: `SELECT COUNT(*) FROM [table]` → rows > 0 |
| AC-10 | Notebook attached to Environment | validation/medallion.md — Phase 4: Transformation | `fab` CLI property inspection | `fab get chicago-bears-85.Workspace/chicago-bears-85-transform.Notebook -q properties` → verify Environment = `chicago-bears-85-env` and default lakehouse = `chicago-bears-85-bronze` |
| AC-11 | Pipeline end-to-end run succeeds | validation/medallion.md — Phase 4: Transformation | `fab` CLI run check + manual portal verification | `fab job run-list chicago-bears-85.Workspace/chicago-bears-85-pipeline.DataPipeline` → at least one successful run; **Manual:** Fabric portal → Pipeline → Monitor → all activities green (Copy Job → Notebook) |
| AC-12 | Direct Lake Semantic Model active | validation/medallion.md — Phase 5: Visualization | Manual portal verification | **Manual:** Fabric portal → Semantic Model → Properties → Query mode = "Direct Lake" (not Import or DirectQuery fallback) |
| AC-13 | Report renders with pipeline data | validation/medallion.md — Phase 5: Visualization | Manual portal verification | `fab exists chicago-bears-85.Workspace/chicago-bears-85-report.Report` then **Manual:** Open Report in Fabric portal → verify visuals load with data from most recent pipeline run |
| AC-14 | Self-service users can create reports | validation/medallion.md — Phase 5: Visualization | Manual test with separate user account | **Manual:** Log in as test user with **Build** permission on Semantic Model → create new report from `chicago-bears-85-model` → verify visuals render; confirm no direct Oracle access is used |
| AC-15 | Governance: workspace roles configured | Cross-cutting (post-deployment manual step) | Manual portal verification | **Manual:** Fabric portal → Workspace → Manage access → verify: Data engineers = Contributor role; BI consumers = Viewer role; Semantic Model Build permission granted to BI group |

---

### Critical Verification Points

These are the checks that **must pass** for the architecture to function. Failure of any of these blocks downstream items.

| Priority | Verification Point | Why Critical | Blocking |
|----------|-------------------|-------------|----------|
| 🔴 P1 | Workspace exists and has Fabric capacity assigned (AC-01) | Direct Lake requires Fabric capacity (F-SKU). Without it, Semantic Model will silently fall back to DirectQuery. All items depend on workspace existence. | All items |
| 🔴 P1 | Bronze Lakehouse exists with `enableSchemas=true` (AC-02) | Default lakehouse for Notebook; landing zone for Copy Job. Schema enforcement is core governance requirement. | Copy Job, Notebook, Pipeline |
| 🔴 P1 | Silver Lakehouse exists with `enableSchemas=true` (AC-03) | Target for Bronze→Silver transformation; schema enforcement for deduplication governance. | Notebook transformation |
| 🔴 P1 | Warehouse Gold exists and is accessible via T-SQL (AC-04) | Gold layer for business consumption; Semantic Model Direct Lake source. Team's T-SQL familiarity depends on this. | Semantic Model, Report, Silver→Gold curation |
| 🔴 P1 | Environment published successfully (AC-05) | Notebook cannot run without a published Environment. Publish can take 20+ minutes — must be confirmed complete before Notebook execution. | Notebook, Pipeline |
| 🔴 P1 | Oracle connection bound to Copy Job (AC-06) | Without a valid Oracle connection (via on-prem gateway), no data enters the platform. The entire pipeline is inert without ingestion. | All data-dependent items (AC-07 through AC-14) |
| 🟡 P2 | Notebook attached to Environment with correct default lakehouse (AC-10) | Notebook must reference the correct compute and storage to function. Misconfiguration causes runtime failures. | Pipeline, Transformation |
| 🟡 P2 | Direct Lake mode confirmed — no silent fallback (AC-12) | Silent fallback to DirectQuery degrades performance invisibly. Must be explicitly verified in Semantic Model properties. | Report performance, user experience |
| 🟡 P2 | Pipeline activities wired correctly (AC-11) | Pipeline orchestrates the full data flow. Activities must be wired manually in portal (Copy Job → Notebook). Missing wiring = no end-to-end flow. | End-to-end data freshness |

---

### Validation Phase Checklist

#### Phase 1: Foundation

| Check | Command / Method | Expected Result | Maps to AC |
|-------|-----------------|-----------------|------------|
| Workspace exists | `fab exists chicago-bears-85.Workspace` | Returns success | AC-01 |
| Workspace has Fabric capacity | **Manual:** Portal → Workspace Settings → License info | F-SKU capacity assigned (F2 min for dev/test) | AC-01 |
| Bronze Lakehouse exists | `fab exists chicago-bears-85.Workspace/chicago-bears-85-bronze.Lakehouse` | Returns success | AC-02 |
| Bronze schemas enabled | `fab get chicago-bears-85.Workspace/chicago-bears-85-bronze.Lakehouse -q properties` | `enableSchemas=true` | AC-02 |
| Silver Lakehouse exists | `fab exists chicago-bears-85.Workspace/chicago-bears-85-silver.Lakehouse` | Returns success | AC-03 |
| Silver schemas enabled | `fab get chicago-bears-85.Workspace/chicago-bears-85-silver.Lakehouse -q properties` | `enableSchemas=true` | AC-03 |
| Warehouse Gold exists | `fab exists chicago-bears-85.Workspace/chicago-bears-85-gold.Warehouse` | Returns success | AC-04 |
| Warehouse Gold accessible via T-SQL | **Manual:** Portal → Warehouse → New SQL query → `SELECT 1` | Query returns `1` | AC-04 |

#### Phase 2: Environment

| Check | Command / Method | Expected Result | Maps to AC |
|-------|-----------------|-----------------|------------|
| Environment exists | `fab exists chicago-bears-85.Workspace/chicago-bears-85-env.Environment` | Returns success | AC-05 |
| Environment publish status | `fab get chicago-bears-85.Workspace/chicago-bears-85-env.Environment -q properties` | Status = Published | AC-05 |
| ⚠️ If status ≠ Published | Wait and re-check after 20 min (publish can take 20+ min) | Do not fail immediately — confirm delay vs failure | AC-05 |

#### Phase 3: Ingestion

| Check | Command / Method | Expected Result | Maps to AC |
|-------|-----------------|-----------------|------------|
| Copy Job exists | `fab exists chicago-bears-85.Workspace/chicago-bears-85-ingest.CopyJob` | Returns success | AC-06 |
| Oracle connection configured | **Manual:** Portal → Copy Job → Settings → Source connection | Oracle connection GUID present; gateway configured | AC-06 |
| Incremental refresh enabled | **Manual:** Portal → Copy Job → Settings → Incremental | Incremental refresh configured on primary key | AC-06 |
| Copy Job has run history | `fab job run-list chicago-bears-85.Workspace/chicago-bears-85-ingest.CopyJob` | At least one successful run | AC-06 |
| Bronze tables populated | `fab ls chicago-bears-85.Workspace/chicago-bears-85-bronze.Lakehouse` | Expected Oracle source tables listed | AC-07 |
| Bronze rows > 0 | SQL via Bronze SQL endpoint: `SELECT COUNT(*) FROM [schema].[table]` (per expected table) | COUNT > 0 for each table | AC-07 |

#### Phase 4: Transformation

| Check | Command / Method | Expected Result | Maps to AC |
|-------|-----------------|-----------------|------------|
| Notebook exists | `fab exists chicago-bears-85.Workspace/chicago-bears-85-transform.Notebook` | Returns success | AC-10 |
| Notebook environment attachment | `fab get chicago-bears-85.Workspace/chicago-bears-85-transform.Notebook -q properties` | Environment = `chicago-bears-85-env` | AC-10 |
| Notebook default lakehouse | `fab get chicago-bears-85.Workspace/chicago-bears-85-transform.Notebook -q properties` | Default lakehouse = `chicago-bears-85-bronze` | AC-10 |
| Silver deduplication — no duplicates | SQL via Silver SQL endpoint: `SELECT COUNT(*) AS total, COUNT(DISTINCT [pk_column]) AS distinct_pks FROM [schema].[table]` | total = distinct_pks for every table | AC-08 |
| Gold tables/views exist | `fab ls chicago-bears-85.Workspace/chicago-bears-85-gold.Warehouse` | Expected Gold tables and/or views present | AC-09 |
| Gold rows > 0 | SQL via Warehouse endpoint: `SELECT COUNT(*) FROM [table]` (per Gold table) | COUNT > 0 for each table | AC-09 |
| Pipeline exists | `fab exists chicago-bears-85.Workspace/chicago-bears-85-pipeline.DataPipeline` | Returns success | AC-11 |
| Pipeline activities wired | **Manual:** Portal → Pipeline → Edit → verify Copy Job and Notebook activities linked | Copy Job → Notebook activities connected with success dependency | AC-11 |
| Pipeline run history | `fab job run-list chicago-bears-85.Workspace/chicago-bears-85-pipeline.DataPipeline` | At least one successful run | AC-11 |
| Pipeline all-green run | **Manual:** Portal → Pipeline → Monitor → select latest run | All activities show green (succeeded) | AC-11 |

#### Phase 5: Visualization

| Check | Command / Method | Expected Result | Maps to AC |
|-------|-----------------|-----------------|------------|
| Semantic Model exists | `fab exists chicago-bears-85.Workspace/chicago-bears-85-model.SemanticModel` | Returns success | AC-12 |
| Semantic Model properties | `fab get chicago-bears-85.Workspace/chicago-bears-85-model.SemanticModel -q properties` | Connected to `chicago-bears-85-gold` Warehouse | AC-12 |
| Direct Lake mode active | **Manual:** Portal → Semantic Model → Properties → Query mode | Query mode = "Direct Lake" (NOT Import, NOT DirectQuery) | AC-12 |
| Report exists | `fab exists chicago-bears-85.Workspace/chicago-bears-85-report.Report` | Returns success | AC-13 |
| Report renders with data | **Manual:** Portal → Open Report → verify visuals | Visuals load; data reflects most recent pipeline run | AC-13 |
| Self-service report creation | **Manual:** Log in as test user → Semantic Model → Create report | New report created and renders data without errors | AC-14 |

#### Phase 6: ML

N/A — No ML items in this architecture.

#### CI/CD Readiness

N/A — Single workspace, single environment. No multi-environment parameterization required.

#### Cross-Cutting: Governance

| Check | Command / Method | Expected Result | Maps to AC |
|-------|-----------------|-----------------|------------|
| Workspace roles | **Manual:** Portal → Workspace → Manage access | Data engineers = Contributor; BI consumers = Viewer | AC-15 |
| Semantic Model Build permission | **Manual:** Portal → Semantic Model → Manage permissions | BI group has Build permission | AC-15 |
| No direct Oracle access by BI users | **Manual:** Confirm BI test user cannot access Oracle connection or Copy Job settings | BI user (Viewer role) has no access to data engineering artifacts | AC-14, AC-15 |

---

### Manual Steps Verification (Post-Deployment)

These steps must be completed by `@fabric-engineer` in the portal before validation can pass.

| # | Manual Step | When | Who | Verification Method |
|---|------------|------|-----|---------------------|
| MS-01 | Configure Semantic Model connection to Warehouse Gold | After Semantic Model creation (W3) | Engineer (portal) | AC-12: Semantic Model properties show `chicago-bears-85-gold` as source |
| MS-02 | Wire Pipeline activities (Copy Job → Notebook) | After Pipeline creation (W4) | Engineer (portal) | AC-11: Pipeline edit view shows connected activities |
| MS-03 | Assign workspace roles | After workspace creation (W1) | User/Admin | AC-15: Manage access shows correct role assignments |
| MS-04 | Set Pipeline schedule (optional) | After validation | User | Optional — not blocking for validation; manual trigger is acceptable during learning phase |

---

### Edge Cases to Configure For

| # | Scenario | Impact | Mitigation | How to Test |
|---|----------|--------|------------|-------------|
| EC-01 | Empty Oracle source tables at deploy time | Notebook may fail on empty DataFrames during Bronze→Silver transformation | Notebook should include null/empty checks: `if df.count() == 0: log warning and skip` | Deploy with at least one empty test table; verify Notebook completes without error; verify Silver layer has no phantom rows |
| EC-02 | Environment publish exceeds 20 minutes | Notebook deployment in W3 is blocked; Pipeline runs will fail | Environment is deployed in W2 to overlap publish time with Copy Job setup; verify publish status before W3 | Run `fab get ...Environment -q properties` at 5-minute intervals; do not fail validation until 30 min have elapsed |
| EC-03 | Direct Lake silent fallback to DirectQuery | Degraded query performance; invisible to end users | Verify Direct Lake mode explicitly in Semantic Model settings; check for unsupported column types in Warehouse Gold | **Manual:** Portal → Semantic Model → Properties → confirm Query mode = "Direct Lake" |

---

### Pre-Deployment Blockers

All items below must be resolved **before** `@fabric-engineer` begins deployment.

| # | Blocker | Owner | Status | Impact if Missing |
|---|---------|-------|--------|-------------------|
| PB-01 | **Fabric capacity (F-SKU)** — F2 min for dev/test, F4+ for production | User | ⬜ Not started | Direct Lake will not function; all Fabric compute blocked |
| PB-02 | **On-premises data gateway** — Oracle assumed on-prem. **Confirm with user.** | User/IT | ⬜ Not started | Copy Job cannot reach Oracle; no data enters Bronze |
| PB-03 | **Oracle connection** — ODBC/JDBC via gateway in "Manage connections and gateways" | User/IT | ⬜ Not started | Copy Job cannot be configured |
| PB-04 | **Oracle source table list** — Table names, primary keys, expected row counts | User | ⬜ Not started | Cannot validate AC-07, AC-08, AC-09 |
| PB-05 | **Test user account** — User with Build permission on Semantic Model | User | ⬜ Not started | Cannot validate AC-14 (not a deployment blocker) |

---

### `fab` CLI Quick Reference

```bash
# Phase 1: Foundation
fab exists chicago-bears-85.Workspace
fab exists chicago-bears-85.Workspace/chicago-bears-85-bronze.Lakehouse
fab exists chicago-bears-85.Workspace/chicago-bears-85-silver.Lakehouse
fab exists chicago-bears-85.Workspace/chicago-bears-85-gold.Warehouse

# Phase 2: Environment
fab exists chicago-bears-85.Workspace/chicago-bears-85-env.Environment

# Phase 3: Ingestion
fab exists chicago-bears-85.Workspace/chicago-bears-85-ingest.CopyJob

# Phase 4: Transformation
fab exists chicago-bears-85.Workspace/chicago-bears-85-transform.Notebook
fab exists chicago-bears-85.Workspace/chicago-bears-85-pipeline.DataPipeline

# Phase 5: Visualization
fab exists chicago-bears-85.Workspace/chicago-bears-85-model.SemanticModel
fab exists chicago-bears-85.Workspace/chicago-bears-85-report.Report

# Property Checks
fab get chicago-bears-85.Workspace/chicago-bears-85-bronze.Lakehouse -q properties
fab get chicago-bears-85.Workspace/chicago-bears-85-silver.Lakehouse -q properties
fab get chicago-bears-85.Workspace/chicago-bears-85-env.Environment -q properties
fab get chicago-bears-85.Workspace/chicago-bears-85-transform.Notebook -q properties
fab get chicago-bears-85.Workspace/chicago-bears-85-model.SemanticModel -q properties

# Job Run History
fab job run-list chicago-bears-85.Workspace/chicago-bears-85-ingest.CopyJob
fab job run-list chicago-bears-85.Workspace/chicago-bears-85-pipeline.DataPipeline

# Listing
fab ls chicago-bears-85.Workspace
fab ls chicago-bears-85.Workspace/chicago-bears-85-bronze.Lakehouse
fab ls chicago-bears-85.Workspace/chicago-bears-85-gold.Warehouse
```

---

### Manual-Only Checks (No CLI Equivalent)

| Check | Why Manual | AC |
|-------|-----------|-----|
| Fabric capacity assignment on workspace | Workspace settings only visible in portal | AC-01 |
| Oracle connection bound to Copy Job | Connection configuration is portal-only | AC-06 |
| Incremental refresh configuration | Copy Job settings are portal-only | AC-06 |
| Pipeline activity wiring (Copy Job → Notebook) | Pipeline designer is portal-only | AC-11 |
| Pipeline all-green run monitoring | Run monitor is portal-only | AC-11 |
| Direct Lake query mode confirmation | Semantic Model properties detail is portal-only | AC-12 |
| Report visual rendering | Visual rendering requires browser | AC-13 |
| Self-service report creation by test user | Requires separate user login in browser | AC-14 |
| Workspace role assignments | Manage access is portal-only | AC-15 |
| Semantic Model Build permission | Permissions management is portal-only | AC-15 |
| Warehouse T-SQL accessibility | Query editor is portal-only | AC-04 |

---

### Notes for `@fabric-engineer`

1. **Deployment order matters:** Follow the 4-wave parallel deployment in the Architecture Handoff. Environment publish (W2) must complete before Notebook deployment (W3).
2. **Manual steps are test-blocking:** MS-01 (Semantic Model connection) and MS-02 (Pipeline wiring) must be completed before tester can validate Phases 4 and 5.
3. **Edge case EC-01 (empty tables):** Ensure Notebook handles empty DataFrames gracefully.
4. **Oracle table list (PB-04):** The tester needs the expected table list to validate AC-07, AC-08, and AC-09. Include the table list in your deployment summary.
5. **Test user (PB-05):** Not required for deployment but needed for AC-14 validation.
