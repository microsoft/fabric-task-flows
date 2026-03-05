# Test Plan

**Project:** old-style
**Task flow:** basic-data-analytics
**Architecture Date:** 2025-07-16
**Test Plan Date:** 2025-07-16

---

## Architecture Summary

Oracle migration project for a T-SQL-skilled team. Four Fabric items deployed into a single "old-style" workspace using the `fab` CLI. No Spark, no Python — all processing via Warehouse stored procedures and views. Single environment (DEV); CI/CD readiness is not in scope.

**Item Inventory:**

| # | Item | Type | Wave |
|---|------|------|------|
| 1 | old-style-warehouse | Warehouse | 1 |
| 2 | old-style-pipeline | DataPipeline | 2 |
| 3 | old-style-semantic-model | SemanticModel | 2 |
| 4 | old-style-report | Report | 3 |

---

## Acceptance Criteria Mapping

| # | Acceptance Criteria | Validation Checklist Reference | Test Method |
|---|---------------------|-------------------------------|-------------|
| AC-1 | Warehouse created — old-style-warehouse exists with T-SQL endpoint accessible | Phase 1: Warehouse | `fab exists old-style.Workspace/old-style-warehouse.Warehouse` + connect via SQL endpoint and run `SELECT 1` |
| AC-2 | Pipeline configured — connects to Oracle source and loads data into Warehouse staging tables | Phase 2: Ingestion | `fab exists old-style.Workspace/old-style-pipeline.DataPipeline` + `fab job run-list` — confirm at least one successful run with data in staging tables |
| AC-3 | T-SQL transforms work — Stored procedures/views can be executed against Warehouse data | Phase 1 + Phase 2 | Execute stored procedures and query views in Warehouse SQL editor; verify output matches expected results |
| AC-4 | Semantic Model connected — bound to Warehouse with relationships and measures | Phase 4: Semantic Layer | `fab exists old-style.Workspace/old-style-semantic-model.SemanticModel` + `fab get` — verify Warehouse binding; inspect relationships and measures |
| AC-5 | Report renders — displays data from Semantic Model without errors | Phase 4: Semantic Layer | `fab exists old-style.Workspace/old-style-report.Report` + open in Power BI service; confirm all visuals render with data |
| AC-6 | Query performance improved — analytical queries complete faster than Oracle baseline | Qualitative | Run 3–5 representative analytical queries against Warehouse and compare elapsed time to Oracle baseline |
| AC-7 | Power BI responsive — Report loads and filters respond within acceptable timeframes | Qualitative | Open report in browser, measure initial load time; apply filters to 3+ slicers; target < 5 seconds per interaction |

---

## Critical Verification Points

1. **Warehouse T-SQL endpoint connectivity** — The entire architecture depends on T-SQL access. If the SQL endpoint is unreachable, nothing else works.

2. **Oracle source connection** — The Pipeline's Copy Activity requires a working connection to the Oracle source. If Oracle is on-premises, an on-premises data gateway must be installed and configured. This is the highest-risk manual step.

3. **Pipeline run succeeds end-to-end** — At least one full pipeline execution must complete with data visible in Warehouse staging tables.

4. **Stored procedure / view execution** — T-SQL objects must be deployable and executable inside the Warehouse. This is the team's primary transformation mechanism.

5. **Semantic Model → Warehouse binding** — The Semantic Model must be correctly bound to the Warehouse. First refresh must succeed after manual connection configuration.

6. **Report → Semantic Model binding** — The Report must reference old-style-semantic-model with all visuals rendering data.

7. **Deployment wave order** — Wave 1 (Warehouse) must complete before Wave 2 begins. Wave 3 must wait for Semantic Model.

---

## Phase-by-Phase Validation Checklist

### Phase 1: Foundation (Warehouse)

| # | Check | Command / Method | Pass Criteria |
|---|-------|-----------------|---------------|
| 1.1 | Warehouse item exists | `fab exists old-style.Workspace/old-style-warehouse.Warehouse` | Returns true |
| 1.2 | Workspace exists with correct name | `fab ls old-style.Workspace -l` | Lists all 4 expected items (post-deployment) |
| 1.3 | T-SQL endpoint is accessible | Connect via SSMS or Azure Data Studio to Warehouse SQL endpoint | Connection succeeds; `SELECT 1` returns 1 |
| 1.4 | Permissions configured | Verify workspace role assignments | Team members have Contributor or higher |
| 1.5 | DDL objects deployed | Query `INFORMATION_SCHEMA.TABLES`, `INFORMATION_SCHEMA.ROUTINES`, `INFORMATION_SCHEMA.VIEWS` | Staging tables, stored procedures, and views exist |

### Phase 2: Ingestion (Pipeline)

| # | Check | Command / Method | Pass Criteria |
|---|-------|-----------------|---------------|
| 2.1 | Pipeline item exists | `fab exists old-style.Workspace/old-style-pipeline.DataPipeline` | Returns true |
| 2.2 | Oracle connection configured | Inspect pipeline in Fabric UI → Copy Activity source | Oracle connection authenticated and test-connection succeeds |
| 2.3 | On-prem gateway (if applicable) | Check gateway status in Manage connections & gateways | Gateway is online and connection uses it |
| 2.4 | Pipeline test run succeeds | `fab job run old-style.Workspace/old-style-pipeline.DataPipeline` | Run completes with "Succeeded" status |
| 2.5 | Data lands in staging tables | `SELECT COUNT(*) FROM [staging].[table_name]` | Row counts > 0 and match expected source counts |
| 2.6 | Pipeline run history | `fab job run-list old-style.Workspace/old-style-pipeline.DataPipeline` | At least one successful run recorded |

### Phase 3: Transformation (Warehouse T-SQL)

| # | Check | Command / Method | Pass Criteria |
|---|-------|-----------------|---------------|
| 3.1 | Stored procedures execute | Execute each stored procedure in SQL editor | No errors; output tables populated |
| 3.2 | Views return data | `SELECT TOP 10 * FROM [schema].[view_name]` for each view | Rows returned with expected schema |
| 3.3 | Data quality spot-check | Compare sample records between Oracle source and Warehouse output | Key columns match; row counts align |
| 3.4 | Query performance | Run 3–5 representative analytical queries; record elapsed time | Faster than documented Oracle baseline (AC-6) |

### Phase 4: Semantic Layer (Semantic Model + Report)

| # | Check | Command / Method | Pass Criteria |
|---|-------|-----------------|---------------|
| 4.1 | Semantic Model exists | `fab exists old-style.Workspace/old-style-semantic-model.SemanticModel` | Returns true |
| 4.2 | Bound to Warehouse | `fab get old-style.Workspace/old-style-semantic-model.SemanticModel -q properties` | Data source points to old-style-warehouse |
| 4.3 | Manual connection configured | Check semantic model settings in Fabric UI → Data source credentials | Credentials set; not showing "Configure required" |
| 4.4 | Refresh succeeds | Trigger manual refresh of Semantic Model in Fabric UI | Refresh completes without error |
| 4.5 | Relationships defined | Open model in Power BI Desktop or web model view | Relationships between tables visible and correct |
| 4.6 | Measures defined | Open model in Power BI Desktop or web model view | DAX measures present and return values |
| 4.7 | Report exists | `fab exists old-style.Workspace/old-style-report.Report` | Returns true |
| 4.8 | Report bound to Semantic Model | Open report → check data source | Connected to old-style-semantic-model |
| 4.9 | Visuals render | Open report in Power BI service | All visuals show data; no error icons |
| 4.10 | Filters responsive | Click 3+ slicers/filters in report | Visuals update within < 5 seconds |

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

---

## Pre-Deployment Blockers

| # | Blocker | Severity | Resolution |
|---|---------|----------|------------|
| B-1 | No Oracle connection details provided | 🔴 Critical | Engineer needs: Oracle host, port, SID/service name, schema, credentials, gateway requirement |
| B-2 | No DDL scripts for Warehouse objects | 🔴 Critical | Team must provide T-SQL scripts (CREATE TABLE, CREATE PROCEDURE, CREATE VIEW) |
| B-3 | No Oracle baseline query times documented | 🟡 Medium | Team should document baseline query times for AC-6 comparison |
| B-4 | Capacity not assigned to workspace | 🔴 Critical | Workspace must be assigned to Fabric capacity (resource limits based on assigned SKU) |
| B-5 | No Semantic Model design (tables, relationships, measures) | 🟡 Medium | Team should define which tables/views, relationships, and DAX measures go into the model |

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

1. **Warehouse DDL is separate from item creation.** `fab mkdir` creates the shell. Deploy schemas, tables, stored procedures, and views separately via DACPAC, sqlcmd, or manual SQL scripts.

2. **Pipeline connection is manual.** After creating the Pipeline item, configure the Oracle source connection in the Fabric UI. Test the connection before building Copy Activities.

3. **Semantic Model needs manual credential setup.** After deployment, go to Semantic Model settings → Data source credentials → configure. First refresh will fail without this.

4. **Document what you deploy.** In your Engineer handoff, list exact DDL objects, Oracle connection type, Semantic Model mode, manual steps completed vs pending, and known issues.

5. **Wave order is mandatory.** Do not create Semantic Model or Pipeline before Warehouse exists. Do not create Report before Semantic Model exists.
