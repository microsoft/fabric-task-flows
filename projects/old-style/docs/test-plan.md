---
project: old-style
task_flow: basic-data-analytics
phase: test-plan-complete
status: final
created: 2025-07-16
last_updated: 2026-03-06
acceptance_criteria: 8
checks: 29
blockers:
  critical: [B-1, B-2, B-4, B-5, B-6]
  medium: [B-3, B-7]
edge_cases: 11
next_phase: deployment
---

# Test Plan

**Project:** old-style
**Task flow:** basic-data-analytics
**Architecture Date:** 2025-07-16
**Test Plan Date:** 2025-07-16

---

## Architecture Summary

Oracle migration project for a T-SQL-skilled team. Four Fabric items deployed into a single "old-style" workspace using the `fab` CLI in 5 sequential waves. No Spark, no Python — all processing via Warehouse stored procedures and views. Single environment (DEV); CI/CD readiness is not in scope. Semantic Model uses Direct Lake on SQL endpoint.

**Item Inventory:**

| # | Item | Type | Wave |
|---|------|------|------|
| 1 | old-style-warehouse | Warehouse | 1 |
| — | (DDL deployment) | T-SQL scripts | 2 |
| 2 | old-style-pipeline | DataPipeline | 3 |
| 3 | old-style-semantic-model | SemanticModel | 4 |
| 4 | old-style-report | Report | 5 |

---

## Acceptance Criteria Mapping

| # | Acceptance Criteria | Validation Checklist Reference | Test Method |
|---|---------------------|-------------------------------|-------------|
| AC-1 | Warehouse created — old-style-warehouse exists with T-SQL endpoint accessible | Phase 1: Warehouse | `fab exists old-style.Workspace/old-style-warehouse.Warehouse` + connect via SQL endpoint and run `SELECT 1` |
| AC-2 | Pipeline configured — connects to Oracle source and loads data into Warehouse staging tables (as defined in DDL scripts). Verify with `SELECT COUNT(*) > 0` for each staging table. | Phase 2: Ingestion | `fab exists old-style.Workspace/old-style-pipeline.DataPipeline` + `fab job run-list` — confirm at least one successful run; `SELECT COUNT(*)` per staging table |
| AC-3 | T-SQL transforms work — All stored procedures execute without error and populate output tables. Views return non-empty result sets. At least 3 sample records validated against Oracle source. | Phase 3: Transformation | Execute each stored procedure and view in SQL editor; verify error-free completion, populated output, sample record fidelity |
| AC-4 | Semantic Model connected — bound to Warehouse with relationships and measures per Semantic Model design document from team (B-5) | Phase 4: Semantic Layer | `fab exists old-style.Workspace/old-style-semantic-model.SemanticModel` + `fab get` — verify Warehouse binding; inspect relationships and measures against design doc |
| AC-5 | Report renders — contains visuals connected to old-style-semantic-model. All visuals render data (no error icons). At least one slicer/filter is functional. | Phase 4: Semantic Layer | `fab exists old-style.Workspace/old-style-report.Report` + open in Power BI service; confirm visuals render, test slicer interaction |
| AC-6 | Query performance — Run 3–5 named analytical queries (defined by team) against Warehouse. Each must complete in ≤ threshold defined by team. Compare against Oracle baseline (B-3). If baselines unavailable, document Warehouse times as new baseline. | Performance | Run named queries via SQL editor; record elapsed times; compare against documented Oracle baselines or establish new baselines |
| AC-7 | Power BI responsive — Report initial load < 10 seconds. Filter interactions respond within < 5 seconds. | Performance | Open report in browser; measure initial load time; apply filters to 3+ slicers; verify sub-5-second response |
| AC-8 | Direct Lake active — Semantic Model storage mode is Direct Lake (on SQL endpoint). No silent fallback to DirectQuery during representative query load. | Phase 4: Semantic Layer | Check Semantic Model settings → Storage mode indicator; run DAX query `EVALUATE { SUMMARIZE(INFO.STORAGETABLECOLUMNS(), [StorageMode]) }` to confirm Direct Lake active |

---

## Critical Verification Points

1. **Warehouse T-SQL endpoint connectivity** — The entire architecture depends on T-SQL access. If the SQL endpoint is unreachable, nothing else works.

2. **Oracle source connection** — The Pipeline's Copy Activity requires a working connection to the Oracle source. If Oracle is on-premises, an on-premises data gateway must be installed and configured. This is the highest-risk manual step.

3. **Pipeline run succeeds end-to-end** — At least one full pipeline execution must complete with data visible in Warehouse staging tables.

4. **Stored procedure / view execution** — T-SQL objects must be deployable and executable inside the Warehouse. This is the team's primary transformation mechanism.

5. **Semantic Model → Warehouse binding** — The Semantic Model must be correctly bound to the Warehouse via Direct Lake on SQL endpoint. First refresh must succeed after manual connection configuration.

6. **Direct Lake mode verification** — Semantic Model must be confirmed as Direct Lake, not DirectQuery or Import. Silent fallback to DirectQuery can occur if data exceeds memory limits or unsupported features are used.

7. **Report → Semantic Model binding** — The Report must reference old-style-semantic-model with all visuals rendering data.

8. **Deployment wave order** — 5 sequential waves. DDL deployment (Wave 2) must complete before Pipeline (Wave 3). Pipeline must populate data before Semantic Model (Wave 4).

---

## Phase-by-Phase Validation Checklist

### Phase 1: Foundation (Warehouse — Wave 1)

| # | Check | Command / Method | Pass Criteria |
|---|-------|-----------------|---------------|
| 1.1 | Warehouse item exists | `fab exists old-style.Workspace/old-style-warehouse.Warehouse` | Returns true |
| 1.2 | Workspace exists with correct name | `fab ls old-style.Workspace -l` | Lists all 4 expected items (post-deployment) |
| 1.3 | T-SQL endpoint is accessible | Connect via SSMS or Azure Data Studio to Warehouse SQL endpoint | Connection succeeds; `SELECT 1` returns 1 |
| 1.4 | Permissions configured | Verify workspace role assignments | Team members have Contributor or higher |

### Phase 1b: DDL Deployment (Wave 2)

| # | Check | Command / Method | Pass Criteria |
|---|-------|-----------------|---------------|
| 1b.1 | DDL scripts deployed | Query `INFORMATION_SCHEMA.TABLES` | All staging and analytics tables exist |
| 1b.2 | Stored procedures exist | Query `INFORMATION_SCHEMA.ROUTINES` | All stored procedures from DDL scripts present |
| 1b.3 | Views exist | Query `INFORMATION_SCHEMA.VIEWS` | All views from DDL scripts present |
| 1b.4 | DDL source-controlled | Check `projects/old-style/sql/` directory | All T-SQL scripts versioned |

### Phase 2: Ingestion (Pipeline — Wave 3)

| # | Check | Command / Method | Pass Criteria |
|---|-------|-----------------|---------------|
| 2.1 | Pipeline item exists | `fab exists old-style.Workspace/old-style-pipeline.DataPipeline` | Returns true |
| 2.2 | Oracle connection configured | Inspect pipeline in Fabric UI → Copy Activity source | Oracle connection authenticated and test-connection succeeds |
| 2.3 | On-prem gateway (if applicable) | Check gateway status in Manage connections & gateways | Gateway is online and connection uses it |
| 2.4 | Pipeline test run succeeds | `fab job run old-style.Workspace/old-style-pipeline.DataPipeline` | Run completes with "Succeeded" status |
| 2.5 | Data lands in staging tables | `SELECT COUNT(*) FROM [staging].[table_name]` for each table | Row counts > 0 and match expected source counts (±1% tolerance) |
| 2.6 | Pipeline run history | `fab job run-list old-style.Workspace/old-style-pipeline.DataPipeline` | At least one successful run recorded |

### Phase 3: Transformation (Warehouse T-SQL)

| # | Check | Command / Method | Pass Criteria |
|---|-------|-----------------|---------------|
| 3.1 | Stored procedures execute | Execute each stored procedure in SQL editor | No errors; output tables populated |
| 3.2 | Views return data | `SELECT TOP 10 * FROM [schema].[view_name]` for each view | Rows returned with expected schema |
| 3.3 | Data quality spot-check | Compare at least 3 sample records between Oracle source and Warehouse output | Key columns match; row counts align (±1% tolerance) |
| 3.4 | Query performance | Run 3–5 named analytical queries (from team); record elapsed time | Meet thresholds defined by team or document as new baseline (AC-6) |

### Phase 4: Semantic Layer (Semantic Model + Report — Waves 4-5)

| # | Check | Command / Method | Pass Criteria |
|---|-------|-----------------|---------------|
| 4.1 | Semantic Model exists | `fab exists old-style.Workspace/old-style-semantic-model.SemanticModel` | Returns true |
| 4.2 | Bound to Warehouse | `fab get old-style.Workspace/old-style-semantic-model.SemanticModel -q properties` | Data source points to old-style-warehouse |
| 4.3 | **Direct Lake mode active** | Check Semantic Model settings → Storage mode; run DAX: `EVALUATE { SUMMARIZE(INFO.STORAGETABLECOLUMNS(), [StorageMode]) }` | Storage mode shows "Direct Lake"; no fallback to DirectQuery (AC-8) |
| 4.4 | Manual connection configured | Check semantic model settings in Fabric UI → Data source credentials | Credentials set; not showing "Configure required" |
| 4.5 | Refresh succeeds | Trigger manual refresh of Semantic Model in Fabric UI | Refresh completes without error |
| 4.6 | Relationships defined | Open model in Power BI Desktop or web model view; compare against Semantic Model design doc (B-5) | Relationships match design document |
| 4.7 | Measures defined | Open model in Power BI Desktop or web model view; compare against design doc | DAX measures present and return expected values |
| 4.8 | Report exists | `fab exists old-style.Workspace/old-style-report.Report` | Returns true |
| 4.9 | Report bound to Semantic Model | Open report → check data source | Connected to old-style-semantic-model |
| 4.10 | Visuals render | Open report in Power BI service | All visuals show data; no error icons |
| 4.11 | Filters responsive | Click 3+ slicers/filters in report | Visuals update within < 5 seconds (AC-7) |
| 4.12 | Report load time | Measure initial load time in browser | < 10 seconds (AC-7) |

### Phase 5: CI/CD Readiness

| # | Check | Status |
|---|-------|--------|
| 5.1 | CI/CD in scope? | **N/A** — Single environment (DEV); CI/CD not applicable per architecture decision |

---

## Manual Steps the Engineer Must Complete

| # | Manual Step | Item | Why Manual | Verification |
|---|-------------|------|-----------|--------------|
| M-1 | Create Oracle source connection | Pipeline | Connections are not source-controlled; credentials required | Pipeline Copy Activity source shows authenticated connection |
| M-2 | Install/configure on-prem data gateway (if Oracle is on-prem) | Pipeline | Infrastructure setup outside Fabric | Gateway shows "Online" in Manage connections & gateways |
| M-3 | Deploy DDL to Warehouse (schemas, tables, stored procs, views) | Warehouse | `fab mkdir` creates shell only; DDL deployed separately via DACPAC, sqlcmd, or manual script | `INFORMATION_SCHEMA` queries return expected objects |
| M-4 | Configure Semantic Model data source credentials | Semantic Model | First deployment requires manual connection config | Semantic Model refresh succeeds |
| M-5 | Verify Report ↔ Semantic Model binding | Report | Need to confirm visuals are connected to the correct model | Report renders data in Power BI service |
| M-6 | Set Pipeline schedule/trigger (if applicable) | Pipeline | Schedules configured in UI | Pipeline runs on expected schedule |

---

## Edge Cases

1. **Oracle connection timeout / firewall** — If Oracle is on-prem behind a firewall, the data gateway must have network access. Test with `SELECT 1 FROM DUAL` before configuring full extraction.

2. **Large table extraction** — If any Oracle table exceeds 1M rows, configure Copy Activity with partitioning to avoid timeouts. Document which tables are large.

3. **Oracle data type mapping** — Watch for:
   - `NUMBER(38,0)` → potential overflow in `INT` (use `BIGINT` or `DECIMAL`)
   - `DATE` → Oracle DATE includes time; Warehouse `DATE` does not (use `DATETIME2`)
   - `CLOB` → Warehouse `VARCHAR(MAX)` (watch for truncation)

4. **Warehouse DDL deployment order** — Stored procedures referencing views must deploy *after* those views. DACPAC handles this automatically.

5. **Semantic Model query mode** — **Direct Lake is recommended** for Warehouse (data stored as Delta/Parquet in OneLake). DirectQuery is an alternative if near-zero latency to latest writes is needed. Import requires scheduled refresh. Document which mode is used and rationale.

6. **Empty Warehouse at Semantic Model binding** — If Semantic Model is deployed before Pipeline runs, tables may be empty. Model should still bind but measures may show errors. **Recommendation:** Run Pipeline before configuring Semantic Model.

7. **Gateway credential expiry** — On-prem gateway credentials can expire. Document credential rotation policy.

8. **Fabric capacity throttling during Pipeline runs** — If the capacity SKU is undersized or shared with other workloads, Pipeline runs may be throttled or fail. Particularly relevant for large Oracle extractions.

9. **Schema evolution — Oracle source changes after Pipeline is configured** — If Oracle adds/drops/renames columns after Pipeline Copy Activities are built, the Pipeline will fail or load incorrect data. No schema drift detection is planned.

10. **Semantic Model refresh failure after schema change** — If Warehouse DDL is updated (new columns, changed types), the Semantic Model may fail to refresh until re-bound. This is a common operational issue.

11. **Report visual errors from NULL data** — If staging or transformed data contains unexpected NULLs, DAX measures may return errors or blanks. Measures should use `IF(ISBLANK(...))` patterns.

---

## Pre-Deployment Blockers

| # | Blocker | Severity | Resolution |
|---|---------|----------|------------|
| B-1 | No Oracle connection details provided | 🔴 Critical | Engineer needs: Oracle host, port, SID/service name, schema, credentials, gateway requirement |
| B-2 | No DDL scripts for Warehouse objects | 🔴 Critical | Team must provide T-SQL scripts (CREATE TABLE, CREATE PROCEDURE, CREATE VIEW) — store in `projects/old-style/sql/` |
| B-3 | No Oracle baseline query times documented | 🟡 Medium | Team should document baseline query times for AC-6. If unavailable, Warehouse times become the baseline. |
| B-4 | Capacity not assigned to workspace | 🔴 Critical | Workspace must be assigned to Fabric capacity (F2/F4 sufficient for dev) |
| B-5 | No Semantic Model design (tables, relationships, measures) | 🔴 Critical | Team must provide: which tables/views to include, expected relationships, initial DAX measures, report wireframe. **Elevated from 🟡 — prerequisite for AC-4, AC-5, AC-7, AC-8.** |
| B-6 | No Oracle table/schema inventory | 🔴 Critical | Team must provide: which Oracle schemas/tables to extract, estimated row counts, which tables are large (> 1M rows for partitioning) |
| B-7 | No data volume estimates | 🟡 Medium | Affects Pipeline partitioning strategy (edge case #2) and Fabric capacity sizing (B-4) |

---

## Fab CLI Verification Commands (Quick Reference)

```bash
# Authenticate
fab auth login

# Verify all items exist
fab ls old-style.Workspace -l
fab exists old-style.Workspace/old-style-warehouse.Warehouse
fab exists old-style.Workspace/old-style-pipeline.DataPipeline
fab exists old-style.Workspace/old-style-semantic-model.SemanticModel
fab exists old-style.Workspace/old-style-report.Report

# Check pipeline run history
fab job run-list old-style.Workspace/old-style-pipeline.DataPipeline

# Get semantic model properties (verify Warehouse binding)
fab get old-style.Workspace/old-style-semantic-model.SemanticModel -q properties

# Run pipeline (trigger test execution)
fab job run old-style.Workspace/old-style-pipeline.DataPipeline
```

---

## Notes for the Engineer

1. **Warehouse DDL is separate from item creation.** `fab mkdir` creates the shell (Wave 1). Deploy schemas, tables, stored procedures, and views separately via DACPAC, sqlcmd, or manual SQL scripts (Wave 2). Store DDL in `projects/old-style/sql/`.

2. **Pipeline connection is manual.** After creating the Pipeline item (Wave 3), configure the Oracle source connection in the Fabric UI. Test the connection before building Copy Activities. Run Pipeline to populate data before proceeding to Wave 4.

3. **Semantic Model must use Direct Lake.** Configure storage mode as Direct Lake on SQL endpoint (Wave 4). After deployment, go to Semantic Model settings → Data source credentials → configure. Verify no DirectQuery fallback after first refresh.

4. **Document what you deploy.** In your Engineer handoff, list exact DDL objects, Oracle connection type, Semantic Model mode (Direct Lake), manual steps completed vs pending, and known issues.

5. **Wave order is mandatory (5 waves, all sequential).** Do not skip DDL deployment. Do not create Semantic Model before Pipeline has populated data. Do not create Report before Semantic Model exists and is configured.
