## Test Plan

**Project:** chicago-bears-85
**Task flow:** medallion
**Architecture Date:** 2026-03-06
**Test Plan Date:** 2026-03-06

---

### Acceptance Criteria Mapping

| # | Category | Criterion | Validation Checklist Reference | Test Method | `fab` CLI Command / Manual |
|---|----------|-----------|-------------------------------|-------------|----------------------------|
| AC-01 | Structural | Workspace exists with capacity | validation/medallion.md — Phase 1: Foundation | `fab` CLI existence check + manual capacity verification | `fab exists chicago-bears-85.Workspace` → then **Manual:** Fabric portal → Workspace Settings → verify Fabric capacity (F-SKU) assigned |
| AC-02 | Structural | Bronze Lakehouse created with schemas enabled | validation/medallion.md — Phase 1: Foundation | `fab` CLI existence check + property inspection | `fab exists chicago-bears-85.Workspace/chicago-bears-85-bronze.Lakehouse` then `fab get chicago-bears-85.Workspace/chicago-bears-85-bronze.Lakehouse -q properties` → verify `enableSchemas=true` |
| AC-03 | Structural | Silver Lakehouse created with schemas enabled | validation/medallion.md — Phase 1: Foundation | `fab` CLI existence check + property inspection | `fab exists chicago-bears-85.Workspace/chicago-bears-85-silver.Lakehouse` then `fab get chicago-bears-85.Workspace/chicago-bears-85-silver.Lakehouse -q properties` → verify `enableSchemas=true` |
| AC-04 | Structural | Warehouse Gold created | validation/medallion.md — Phase 1: Foundation (Option B) | `fab` CLI existence check | `fab exists chicago-bears-85.Workspace/chicago-bears-85-gold.Warehouse` |
| AC-05 | Structural | Environment published | validation/medallion.md — Phase 2: Environment | `fab` CLI existence check + status inspection | `fab exists chicago-bears-85.Workspace/chicago-bears-85-env.Environment` then `fab get chicago-bears-85.Workspace/chicago-bears-85-env.Environment -q properties` → verify Status = Published |
| AC-06 | Structural | Copy Job exists | validation/medallion.md — Phase 3: Ingestion | `fab` CLI existence check | `fab exists chicago-bears-85.Workspace/chicago-bears-85-ingest.CopyJob` |
| AC-06b | Data Flow | Copy Job configured with Oracle source | validation/medallion.md — Phase 3: Ingestion | Manual connection verification | **Manual:** Fabric portal → Copy Job settings → verify Oracle connection GUID bound and incremental refresh enabled |
| AC-07 | Data Flow | Oracle tables land in Bronze | validation/medallion.md — Phase 3: Ingestion | `fab` CLI listing + SQL query | Verified after implementation — `fab ls chicago-bears-85.Workspace/chicago-bears-85-bronze.Lakehouse` → verify expected tables present |
| AC-08 | Data Flow | Bronze→Silver deduplication succeeds | validation/medallion.md — Phase 4: Transformation | SQL query on Silver SQL endpoint | Verified after implementation — `SELECT COUNT(*) AS total_rows, COUNT(DISTINCT [pk_column]) AS distinct_pks FROM [schema].[table]` → total_rows = distinct_pks |
| AC-09 | Data Flow | Silver→Gold curation completes | validation/medallion.md — Phase 4: Transformation | `fab` CLI listing + SQL query | Verified after implementation — `fab ls chicago-bears-85.Workspace/chicago-bears-85-gold.Warehouse` → expected Gold tables/views exist |
| AC-10 | Structural | Notebook attached to Environment | validation/medallion.md — Phase 4: Transformation | `fab` CLI property inspection | `fab get chicago-bears-85.Workspace/chicago-bears-85-transform.Notebook -q properties` → verify Environment = `chicago-bears-85-env` and default lakehouse = `chicago-bears-85-bronze` |
| AC-11a | Structural | Pipeline exists with activities | validation/medallion.md — Phase 4: Transformation | `fab` CLI existence check | `fab exists chicago-bears-85.Workspace/chicago-bears-85-pipeline.DataPipeline` |
| AC-11b | Data Flow | Pipeline end-to-end run succeeds | validation/medallion.md — Phase 4: Transformation | `fab` CLI run check + manual portal verification | Verified after implementation — `fab job run-list chicago-bears-85.Workspace/chicago-bears-85-pipeline.DataPipeline` → at least one successful run |
| AC-12 | Structural | Direct Lake Semantic Model active | validation/medallion.md — Phase 5: Visualization | Manual portal verification | **Manual:** Fabric portal → Semantic Model → Properties → Query mode = "Direct Lake" (not Import or DirectQuery fallback) |
| AC-13 | Data Flow | Report renders with pipeline data | validation/medallion.md — Phase 5: Visualization | Manual portal verification | Verified after implementation — Open Report in Fabric portal → verify visuals load with data |
| AC-14 | Data Flow | Self-service users can create reports | validation/medallion.md — Phase 5: Visualization | Manual test with separate user account | Verified after implementation — Log in as test user with **Build** permission → create new report from `chicago-bears-85-model` |
| AC-15 | Structural | Governance: workspace roles configured | Cross-cutting (post-deployment manual step) | Manual portal verification | **Manual:** Fabric portal → Workspace → Manage access → verify: Data engineers = Contributor role; BI consumers = Viewer role; Semantic Model Build permission granted to BI group |

---

### Structural Critical Points (verify immediately after deployment)

These checks confirm items exist with correct configuration. No data or connections required.

| Priority | Verification Point | Why Critical | Blocking |
|----------|-------------------|-------------|----------|
| 🔴 P1 | Workspace exists and has Fabric capacity assigned (AC-01) | Direct Lake requires Fabric capacity (F-SKU). Without it, Semantic Model will silently fall back to DirectQuery. All items depend on workspace existence. | All items |
| 🔴 P1 | Bronze Lakehouse exists with `enableSchemas=true` (AC-02) | Default lakehouse for Notebook; landing zone for Copy Job. Schema enforcement is core governance requirement. | Copy Job, Notebook, Pipeline |
| 🔴 P1 | Silver Lakehouse exists with `enableSchemas=true` (AC-03) | Target for Bronze→Silver transformation; schema enforcement for deduplication governance. | Notebook transformation |
| 🔴 P1 | Warehouse Gold exists and is accessible via T-SQL (AC-04) | Gold layer for business consumption; Semantic Model Direct Lake source. Team's T-SQL familiarity depends on this. | Semantic Model, Report, Silver→Gold curation |
| 🔴 P1 | Environment published successfully (AC-05) | Notebook cannot run without a published Environment. Publish can take 20+ minutes — must be confirmed complete before Notebook execution. | Notebook, Pipeline |
| 🟡 P2 | Notebook attached to Environment with correct default lakehouse (AC-10) | Notebook must reference the correct compute and storage to function. Misconfiguration causes runtime failures. | Pipeline, Transformation |
| 🟡 P2 | Direct Lake mode confirmed — no silent fallback (AC-12) | Silent fallback to DirectQuery degrades performance invisibly. Must be explicitly verified in Semantic Model properties. | Report performance, user experience |

### Data Flow Critical Points (verify after implementation details are in place)

These checks require real connections, data, and pipeline execution. They cannot be validated until deployment blockers are resolved.

| Priority | Verification Point | Why Critical | Blocking |
|----------|-------------------|-------------|----------|
| 🔴 P1 | Oracle connection bound to Copy Job (AC-06b) | Without a valid Oracle connection (via on-prem gateway), no data enters the platform. The entire pipeline is inert without ingestion. | All data-dependent items (AC-07 through AC-14) |
| 🟡 P2 | Pipeline activities wired correctly (AC-11b) | Pipeline orchestrates the full data flow. Activities must be wired manually in portal (Copy Job → Notebook). Missing wiring = no end-to-end flow. | End-to-end data freshness |

---

### Validation Phase Checklist

#### Phase 1: Foundation

| Category | Check | Command / Method | Expected Result | Maps to AC |
|----------|-------|-----------------|-----------------|------------|
| Structural | Workspace exists | `fab exists chicago-bears-85.Workspace` | Returns success | AC-01 |
| Structural | Workspace has Fabric capacity | **Manual:** Portal → Workspace Settings → License info | F-SKU capacity assigned (F2 min for dev/test) | AC-01 |
| Structural | Bronze Lakehouse exists | `fab exists chicago-bears-85.Workspace/chicago-bears-85-bronze.Lakehouse` | Returns success | AC-02 |
| Structural | Bronze schemas enabled | `fab get chicago-bears-85.Workspace/chicago-bears-85-bronze.Lakehouse -q properties` | `enableSchemas=true` | AC-02 |
| Structural | Silver Lakehouse exists | `fab exists chicago-bears-85.Workspace/chicago-bears-85-silver.Lakehouse` | Returns success | AC-03 |
| Structural | Silver schemas enabled | `fab get chicago-bears-85.Workspace/chicago-bears-85-silver.Lakehouse -q properties` | `enableSchemas=true` | AC-03 |
| Structural | Warehouse Gold exists | `fab exists chicago-bears-85.Workspace/chicago-bears-85-gold.Warehouse` | Returns success | AC-04 |
| Structural | Warehouse Gold accessible via T-SQL | **Manual:** Portal → Warehouse → New SQL query → `SELECT 1` | Query returns `1` | AC-04 |

#### Phase 2: Environment

| Category | Check | Command / Method | Expected Result | Maps to AC |
|----------|-------|-----------------|-----------------|------------|
| Structural | Environment exists | `fab exists chicago-bears-85.Workspace/chicago-bears-85-env.Environment` | Returns success | AC-05 |
| Structural | Environment publish status | `fab get chicago-bears-85.Workspace/chicago-bears-85-env.Environment -q properties` | Status = Published | AC-05 |
| Structural | ⚠️ If status ≠ Published | Wait and re-check after 20 min (publish can take 20+ min) | Do not fail immediately — confirm delay vs failure | AC-05 |

#### Phase 3: Ingestion

| Category | Check | Command / Method | Expected Result | Maps to AC |
|----------|-------|-----------------|-----------------|------------|
| Structural | Copy Job exists | `fab exists chicago-bears-85.Workspace/chicago-bears-85-ingest.CopyJob` | Returns success | AC-06 |
| Data Flow | Oracle connection configured | **Manual:** Portal → Copy Job → Settings → Source connection | Oracle connection GUID present; gateway configured | AC-06b |
| Data Flow | Incremental refresh enabled | **Manual:** Portal → Copy Job → Settings → Incremental | Incremental refresh configured on primary key | AC-06b |
| Data Flow | Copy Job has run history | `fab job run-list chicago-bears-85.Workspace/chicago-bears-85-ingest.CopyJob` | At least one successful run | AC-06b |
| Data Flow | Bronze tables populated | `fab ls chicago-bears-85.Workspace/chicago-bears-85-bronze.Lakehouse` | Expected Oracle source tables listed | AC-07 |

#### Phase 4: Transformation

| Category | Check | Command / Method | Expected Result | Maps to AC |
|----------|-------|-----------------|-----------------|------------|
| Structural | Notebook exists | `fab exists chicago-bears-85.Workspace/chicago-bears-85-transform.Notebook` | Returns success | AC-10 |
| Structural | Notebook environment attachment | `fab get chicago-bears-85.Workspace/chicago-bears-85-transform.Notebook -q properties` | Environment = `chicago-bears-85-env` | AC-10 |
| Structural | Notebook default lakehouse | `fab get chicago-bears-85.Workspace/chicago-bears-85-transform.Notebook -q properties` | Default lakehouse = `chicago-bears-85-bronze` | AC-10 |
| Data Flow | Silver deduplication — no duplicates | SQL via Silver SQL endpoint: `SELECT COUNT(*) AS total, COUNT(DISTINCT [pk_column]) AS distinct_pks FROM [schema].[table]` | total = distinct_pks for every table | AC-08 |
| Data Flow | Gold tables/views exist | `fab ls chicago-bears-85.Workspace/chicago-bears-85-gold.Warehouse` | Expected Gold tables and/or views present | AC-09 |
| Structural | Pipeline exists | `fab exists chicago-bears-85.Workspace/chicago-bears-85-pipeline.DataPipeline` | Returns success | AC-11a |
| Data Flow | Pipeline activities wired | **Manual:** Portal → Pipeline → Edit → verify Copy Job and Notebook activities linked | Copy Job → Notebook activities connected with success dependency | AC-11b |
| Data Flow | Pipeline run history | `fab job run-list chicago-bears-85.Workspace/chicago-bears-85-pipeline.DataPipeline` | At least one successful run | AC-11b |
| Data Flow | Pipeline all-green run | **Manual:** Portal → Pipeline → Monitor → select latest run | All activities show green (succeeded) | AC-11b |

#### Phase 5: Visualization

| Category | Check | Command / Method | Expected Result | Maps to AC |
|----------|-------|-----------------|-----------------|------------|
| Structural | Semantic Model exists | `fab exists chicago-bears-85.Workspace/chicago-bears-85-model.SemanticModel` | Returns success | AC-12 |
| Structural | Semantic Model properties | `fab get chicago-bears-85.Workspace/chicago-bears-85-model.SemanticModel -q properties` | Connected to `chicago-bears-85-gold` Warehouse | AC-12 |
| Structural | Direct Lake mode active | **Manual:** Portal → Semantic Model → Properties → Query mode | Query mode = "Direct Lake" (NOT Import, NOT DirectQuery) | AC-12 |
| Structural | Report exists | `fab exists chicago-bears-85.Workspace/chicago-bears-85-report.Report` | Returns success | AC-13 |
| Data Flow | Report renders with data | **Manual:** Portal → Open Report → verify visuals | Visuals load; data reflects most recent pipeline run | AC-13 |
| Data Flow | Self-service report creation | **Manual:** Log in as test user → Semantic Model → Create report | New report created and renders data without errors | AC-14 |

#### Phase 6: ML

N/A — No ML items in this architecture.

#### CI/CD Readiness

N/A — Single workspace, single environment. No multi-environment parameterization required.

#### Cross-Cutting: Governance

| Category | Check | Command / Method | Expected Result | Maps to AC |
|----------|-------|-----------------|-----------------|------------|
| Structural | Workspace roles | **Manual:** Portal → Workspace → Manage access | Data engineers = Contributor; BI consumers = Viewer | AC-15 |
| Structural | Semantic Model Build permission | **Manual:** Portal → Semantic Model → Manage permissions | BI group has Build permission | AC-15 |
| Data Flow | No direct Oracle access by BI users | **Manual:** Confirm BI test user cannot access Oracle connection or Copy Job settings | BI user (Viewer role) has no access to data engineering artifacts | AC-14, AC-15 |

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

### Architecture Blockers (block sign-off)

These must be resolved before the user approves the architecture.

| # | Blocker | Owner | Status | Impact |
|---|---------|-------|--------|--------|
| AB-01 | **Fabric capacity (F-SKU)** — F2 min for dev/test, F4+ for production | User | ⬜ Not started | Direct Lake requires F-SKU; architecture feasibility depends on this |

### Deployment Blockers (block engineer, NOT sign-off)

These must be resolved before `@fabric-engineer` begins deployment. They do **not** block architecture approval.

| # | Blocker | Owner | Status | Impact |
|---|---------|-------|--------|--------|
| DB-01 | **On-premises data gateway** — Oracle assumed on-prem. **Confirm with user.** | User/IT | ⬜ Not started | Copy Job cannot reach Oracle |
| DB-02 | **Oracle connection GUID** — ODBC/JDBC via gateway in "Manage connections and gateways" | User/IT | ⬜ Not started | Copy Job connection configuration |
| DB-03 | **Oracle source table list** — Table names and primary keys | User | ⬜ Not started | Needed for Data Flow ACs (AC-07, AC-08, AC-09) |
| DB-04 | **Test user with Build permission** — User account for self-service validation | User | ⬜ Not started | Needed for AC-14 validation |

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

1. **Structural checks pass first:** After deployment, all Structural ACs (items exist, correct config) should pass immediately. Data Flow ACs require implementation details (connections, data) to be in place.
2. **Deployment order matters:** Follow the 4-wave parallel deployment in the Architecture Handoff. Environment publish (W2) must complete before Notebook deployment (W3).
3. **Manual steps are test-blocking:** MS-01 (Semantic Model connection) and MS-02 (Pipeline wiring) must be completed before tester can validate Phases 4 and 5.
4. **Edge case EC-01 (empty tables):** Ensure Notebook handles empty DataFrames gracefully.
5. **Oracle table list (DB-03):** The tester needs the expected table list to validate Data Flow ACs (AC-07, AC-08, AC-09). Include the table list in your deployment summary.
6. **Test user (DB-04):** Not required for deployment but needed for AC-14 validation.
