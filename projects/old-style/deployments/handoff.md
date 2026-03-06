# Architecture Handoff

## Project: old-style

**Task flow:** basic-data-analytics
**Date:** 2025-07-16

### Decisions
| Decision | Choice | Rationale |
|----------|--------|-----------|
| Storage | Warehouse | Native T-SQL support — stored procedures, views, functions. Oracle developers transition seamlessly with zero new language skills. Distributed SQL engine with columnar storage addresses "slow analytical queries" directly. |
| Ingestion | Pipeline | Orchestrates Oracle data extraction with Copy Activity. Handles scheduling, error handling, conditional logic, and multi-step workflows. Team can extend with additional activities as needed. |
| Processing | Warehouse T-SQL | All transformations done via stored procedures, views, and functions within the Warehouse — team's existing Oracle SQL skills transfer directly. |
| Visualization | Report | Power BI Report connected via Semantic Model to Warehouse. **Direct Lake** recommended — Warehouse stores data as Delta/Parquet in OneLake, giving near-import performance without scheduled refresh. |

### Items to Deploy

| Order | Item | Type | Skillset | Depends On |
|-------|------|------|----------|------------|
| 1 | old-style-warehouse | Warehouse | [LC/CF] | (none — foundation) |
| 2 | (DDL deployment) | T-SQL scripts | [CF] | Warehouse |
| 3 | old-style-pipeline | DataPipeline | [LC/CF] | Warehouse + DDL |
| 4 | old-style-semantic-model | SemanticModel | [LC/CF] | Warehouse (populated by Pipeline) |
| 5 | old-style-report | Report | [LC] | Semantic Model |

### Deployment Order

**Wave 1:** Warehouse — create shell via `fab mkdir`
**Wave 2:** DDL deployment — deploy schemas, tables, stored procs, views via DACPAC or sqlcmd (Pipeline needs target tables; Semantic Model needs views)
**Wave 3:** Pipeline — create item, configure Oracle connection, execute first run to populate staging tables
**Wave 4:** Semantic Model — create item, configure Direct Lake on SQL endpoint, manual connection setup, first refresh
**Wave 5:** Report — create item, bind to Semantic Model

> **⚠️ Design Review correction:** Original draft parallelized Pipeline + Semantic Model in Wave 2. Engineer review identified that Semantic Model depends on *populated* Warehouse data (not just existence), so these must be sequential. DDL deployment was also missing as a wave — `fab mkdir` creates an empty shell; DDL must deploy separately.

### Acceptance Criteria

1. **Warehouse created** — old-style-warehouse exists in workspace with T-SQL endpoint accessible
2. **Pipeline configured** — old-style-pipeline connects to Oracle source and loads data into Warehouse staging tables (as defined in DDL scripts). Verify with `SELECT COUNT(*) > 0` for each staging table.
3. **T-SQL transforms work** — All stored procedures execute without error and populate output tables. Views return non-empty result sets. At least 3 sample records validated against Oracle source for data accuracy.
4. **Semantic Model connected** — old-style-semantic-model bound to Warehouse with relationships and measures defined (per Semantic Model design document from team)
5. **Report renders** — old-style-report contains visuals connected to old-style-semantic-model. All visuals render data (no error icons). At least one slicer/filter is functional.
6. **Query performance improved** — Run 3–5 named analytical queries (defined by team) against Warehouse. Each must complete in ≤ threshold defined by team. Compare against documented Oracle baseline times (B-3). If baselines unavailable, document Warehouse query times as the new baseline.
7. **Power BI responsive** — Report initial load < 10 seconds. Filter interactions respond within < 5 seconds.
8. **Direct Lake active** — Semantic Model storage mode is configured as Direct Lake (on SQL endpoint). Verify via Semantic Model settings → Storage mode indicator. Confirm no silent fallback to DirectQuery during representative query load.

### Alternatives Considered

| Decision | Option Rejected | Why Rejected |
|----------|-----------------|---------------|
| Storage | Lakehouse + SQL analytics endpoint | SQL endpoint is read-only — cannot write T-SQL stored procedures for transformations. Team would need Spark/Python skills they don't have. |
| Storage | SQL Database (Translytical) | Designed for OLTP/transactional workloads with writeback. Overkill for pure analytical use case — Warehouse is purpose-built for analytics. |
| Ingestion | Copy Job | Too simple — no orchestration, no conditional logic, no error handling for multi-table Oracle extraction. |
| Ingestion | Dataflow Gen2 | Power Query-based — while low-code, it doesn't provide the orchestration capabilities needed for multi-table Oracle extraction with dependencies. |
| Processing | Notebook (Spark) | Team is T-SQL only — learning PySpark would slow the migration. Warehouse T-SQL delivers same analytical transforms in their native language. |
| Task flow | medallion | Spark-based transformation layers (Bronze/Silver/Gold). Great pattern but requires Python/Spark skills the team lacks. |
| Task flow | data-analytics-sql-endpoint | Requires Spark Notebooks for data processing. SQL endpoint only provides read-only T-SQL access — insufficient for a team that needs stored procedures. |

### Trade-offs

| Trade-off | Benefit | Cost | Mitigation |
|-----------|---------|------|------------|
| Warehouse over Lakehouse | Full T-SQL DML (stored procs, views, functions) — zero learning curve for Oracle team | No Delta Lake open format — data locked in Warehouse proprietary format | If open format needed later, add a Lakehouse for raw data and use Warehouse as serving layer |
| Pipeline over Copy Job | Full orchestration — scheduling, error handling, conditional logic, loops | More complex to configure than simple Copy Job | Start with Copy Activity inside Pipeline — gets simplicity of Copy Job with Pipeline's orchestration wrapper |
| No Spark/Notebooks | Team productive immediately — no new skills required | Cannot use PySpark for large-scale data processing or ML | Add Notebooks later if team upskills; Warehouse handles most analytical transforms fine |
| Single visualization (Report) | Simple, focused output — one report to maintain | No dashboards, scorecards, or paginated reports | Easy to add Dashboard, Scorecard later — they just depend on Semantic Model or Report |

### Deployment Strategy

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Workspace Approach | Single workspace | Simple project with 4 items — single workspace minimizes complexity for a team new to Fabric |
| Environments | Single (DEV) | Start with one environment; add PPE/PROD when the team is ready for CI/CD |
| CI/CD Tool | fab CLI | Interactive deployment fits a team learning Fabric; upgrade to fabric-cicd when automating |
| Branching Model | N/A | Single environment — no branching strategy needed yet |

**Connections to Pre-Create:**
- Oracle source connection (on-premises data gateway required — confirm Oracle location; if on-prem, gateway provisioning may take days)

**Parameterization Needs:**
- None for single environment — add workspace ID and connection string parameterization when expanding to PPE/PROD

**DDL Source Control:**
- Store all T-SQL scripts in `projects/old-style/sql/` (schemas, tables, stored procs, views)
- Deploy via DACPAC (recommended for dependency ordering) or sqlcmd

**Values Collected:**
- Workspace: Create new (name: "old-style")
- Language: T-SQL
- Semantic Model query mode: Direct Lake (on SQL endpoint, with DirectQuery fallback)

### References
- Project folder: projects/old-style/
- Diagram: diagrams/basic-data-analytics.md
- Validation: validation/basic-data-analytics.md
- Decisions: decisions/storage-selection.md, decisions/ingestion-selection.md

---

### Design Review

> This section records feedback from the collaborative Design Review (Phase 1).

#### Engineer Review — Deployment Feasibility

| # | Area | Finding | Severity | Resolution |
|---|------|---------|----------|------------|
| E-1 | Deployment order | Wave 2 incorrectly parallelized Pipeline + Semantic Model. Semantic Model depends on *populated* data, not just Warehouse existence. | 🔴 | **Fixed:** Revised to 5 sequential waves. |
| E-2 | DDL deployment | `fab mkdir` creates empty shell. No DDL deployment wave existed — Pipeline has nowhere to load, Semantic Model has nothing to bind to. | 🔴 | **Fixed:** Added Wave 2 for DDL deployment via DACPAC/sqlcmd. Added `projects/old-style/sql/` for DDL source control. |
| E-3 | Per-item gotchas | Semantic Model manual connection requirement not documented in handoff. | 🟡 | **Fixed:** Documented in Wave 4 description. |
| E-4 | Prerequisites | On-prem gateway is conditional but Oracle migration almost certainly requires it. Gateway provisioning takes days. | 🟡 | **Fixed:** Strengthened gateway prerequisite language. |
| E-5 | Prerequisites | Fabric capacity assignment not mentioned as prerequisite. | 🟡 | Already covered in B-4; no change needed. |
| E-6 | Direct Lake | Configuration details unspecified — endpoint, fallback behavior, binding timing. | 🟡 | **Fixed:** Added AC-8, specified "Direct Lake on SQL endpoint" with DirectQuery fallback in Values Collected. |
| E-7 | Parallel deployment | 4-item project — parallelism adds no value. Sequential is correct. | 🟢 | Accepted. |
| E-8 | 4 V's assessment | Pipeline correct for batch Oracle extraction of structured data. | 🟢 | No change needed. |
| E-9 | Pipeline config | Copy Activity requires portal configuration — not documented as manual step. | 🟡 | **Acknowledged:** Covered by Wave 3 description. |

**Overall Assessment:** ⚠️ Needs Changes → ✅ Resolved (2 blockers fixed)

#### Tester Review — Testability Assessment

| # | Area | Finding | Severity | Resolution |
|---|------|---------|----------|------------|
| T-1 | AC-4 | "Relationships and measures defined" untestable without Semantic Model design document. | 🔴 | **Fixed:** AC-4 now references "per Semantic Model design document from team." B-5 elevated to 🔴 Critical. |
| T-2 | AC-6 | "Qualitative check" is not a pass/fail criterion. No baseline, no queries, no thresholds. | 🔴 | **Fixed:** Rewritten with specific thresholds, named queries requirement, fallback to documenting new baseline. |
| T-3 | Direct Lake | Recommended in handoff but no AC verifies it. Engineer could deploy DirectQuery and no criterion catches it. | 🔴 | **Fixed:** Added AC-8 for Direct Lake verification. |
| T-4 | AC-3 | "Work" is ambiguous — runs without error? Returns expected counts? Matches Oracle? | 🟡 | **Fixed:** Rewritten to require error-free execution, populated output tables, and sample record validation. |
| T-5 | AC-7 | "Acceptable timeframes" undefined — test plan invented "< 5 seconds." | 🟡 | **Fixed:** Architect now defines thresholds (< 10s load, < 5s filter). |
| T-6 | AC-5 | "Without errors" needs specifics on what visuals should exist. | 🟡 | **Fixed:** Rewritten to require visuals rendering data with at least one functional slicer. |
| T-7 | B-5 severity | Semantic Model design is prerequisite for 4 of 8 ACs — should be 🔴 not 🟡. | 🔴 | **Fixed:** Elevated to 🔴 Critical. |
| T-8 | Missing blocker | No Oracle table/schema inventory (B-6). Engineer can't configure Pipeline without table list. | 🔴 | **Fixed:** Added B-6. |
| T-9 | Missing blocker | No data volume estimates (B-7). Affects partitioning and capacity sizing. | 🟡 | **Fixed:** Added B-7. |
| T-10 | Pipeline scheduling | One-time migration or ongoing sync? Affects Pipeline scheduling AC. | 🟡 | **Noted:** Team must clarify — not resolved in this review. |
| T-11 | Data completeness | No AC for row counts or data fidelity. Only tester-added spot-check. | 🟡 | **Partially addressed:** AC-2 now includes row count verification. |

**Overall Assessment:** Needs Refinement → ✅ Resolved (3 critical gaps fixed, 5 medium items addressed)
