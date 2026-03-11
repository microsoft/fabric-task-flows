# Decision Guides

> **Agents:** Use `decision-resolver.py` to resolve all 7 decisions programmatically. Only read a guide file when the resolver returns `confidence: ambiguous` and you need comparison tables.

| ID | Guide | Key Options |
|----|-------|-------------|
| storage | [Storage Selection](storage-selection.md) | Lakehouse, Warehouse, Eventhouse, SQL Database, Cosmos DB, PostgreSQL |
| ingestion | [Ingestion Selection](ingestion-selection.md) | Pipeline, Dataflow Gen2, Eventstream, Copy Job, Mirroring, Shortcut, Fabric Link |
| processing | [Processing Selection](processing-selection.md) | Notebook, Spark Job, Dataflow Gen2, KQL Queryset, Stored Procs |
| visualization | [Visualization Selection](visualization-selection.md) | Report, Paginated Report, Scorecard, RT Dashboard, RT Map |
| skillset | [Skillset Selection](skillset-selection.md) | Code-First [CF], Low-Code [LC], Hybrid [LC/CF] |
| parameterization | [Parameterization Selection](parameterization-selection.md) | Variable Library, parameter.yml, Environment Variables |
| api | [API Selection](api-selection.md) | GraphQL API, User Data Functions, Direct Connection |
