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
| 2 | old-style-pipeline | DataPipeline | [LC/CF] | Warehouse |
| 3 | old-style-semantic-model | SemanticModel | [LC/CF] | Warehouse (populated) |
| 4 | old-style-report | Report | [LC] | Semantic Model |

### Deployment Order

**Wave 1:** Warehouse (foundation — must deploy first)
**Wave 2:** Pipeline + Semantic Model (parallel — both depend only on Warehouse)
**Wave 3:** Report (depends on Semantic Model)

### Acceptance Criteria

1. **Warehouse created** — old-style-warehouse exists in workspace with T-SQL endpoint accessible
2. **Pipeline configured** — old-style-pipeline connects to Oracle source and loads data into Warehouse staging tables
3. **T-SQL transforms work** — Stored procedures/views can be executed against Warehouse data
4. **Semantic Model connected** — old-style-semantic-model bound to Warehouse with relationships and measures defined
5. **Report renders** — old-style-report displays data from Semantic Model without errors
6. **Query performance improved** — Analytical queries on Warehouse complete faster than Oracle baseline (qualitative check)
7. **Power BI responsive** — Report loads and filters respond within acceptable timeframes

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
- Oracle source connection (on-premises data gateway required if Oracle is on-prem)

**Parameterization Needs:**
- None for single environment — add workspace ID and connection string parameterization when expanding to PPE/PROD

**Values Collected:**
- Workspace: Create new (name: "old-style")
- Language: T-SQL

### References
- Project folder: projects/old-style/
- Diagram: diagrams/basic-data-analytics.md
- Validation: validation/basic-data-analytics.md
- Decisions: decisions/storage-selection.md, decisions/ingestion-selection.md
