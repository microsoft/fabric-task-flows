# Deployment Patterns by Item Type

> ⚠️ **DEPRECATED** — This file documents legacy `fab mkdir` patterns. The project standard is `fabric-cicd` via `deploy-script-gen.py`. This reference is retained for historical context only.

Reference for legacy `fab mkdir` commands and item-specific configuration.

## Storage Items

- **Lakehouse**: `fab mkdir <ws>.Workspace/<name>.Lakehouse`
  - With schemas: add `-P enableSchemas=true`
  - For medallion: create Bronze, Silver, and Gold as separate Lakehouses
- **Warehouse**: `fab mkdir <ws>.Workspace/<name>.Warehouse`
- **Eventhouse**: `fab mkdir <ws>.Workspace/<name>.Eventhouse`
  - Then create KQL Database: `fab mkdir <ws>.Workspace/<name>.KQLDatabase -P eventhouseId=<id>`
- **SQL Database**: `fab mkdir <ws>.Workspace/<name>.SQLDatabase`
  - OLTP-capable with full T-SQL, stored procedures, foreign keys
  - Automatically mirrors data to OneLake in Delta format
  - Creates SQL analytics endpoint for cross-database queries
  - Supports GraphQL API creation directly from portal
- **Cosmos DB**: Create via Fabric Portal → + New Item → Cosmos DB database
  - AI-optimized NoSQL database with vector search, full-text search, hybrid search
  - Schema-less document model — ideal for semi-structured and evolving data
  - Automatically mirrors data to OneLake in Delta format
  - Supports GraphQL API and User Data Functions integration
  - No `fab mkdir` support — portal only

## Ingestion Items

- **Copy Job**: `fab mkdir <ws>.Workspace/<name>.CopyJob`
  - Configure source/destination connections via `fab set` or portal
- **Pipeline**: `fab mkdir <ws>.Workspace/<name>.DataPipeline`
  - Import definition: `fab import <ws>.Workspace/<name>.DataPipeline -i ./pipeline-def`
- **Eventstream**: `fab mkdir <ws>.Workspace/<name>.Eventstream`
- **Dataflow Gen2**: Create via portal (not supported by CLI)

## Processing Items

- **Environment**: `fab mkdir <ws>.Workspace/<name>.Environment`
- **Notebook**: `fab mkdir <ws>.Workspace/<name>.Notebook`
  - Set default lakehouse: `fab set <ws>.Workspace/<nb>.Notebook -q lakehouse -i '<json>'`
  - Set environment: `fab set <ws>.Workspace/<nb>.Notebook -q environment -i '<json>'`
  - Import from file: `fab import <ws>.Workspace/<nb>.Notebook -i ./notebook.ipynb`
- **Spark Job Definition**: `fab mkdir <ws>.Workspace/<name>.SparkJobDefinition`
- **KQL Queryset**: `fab mkdir <ws>.Workspace/<name>.KQLQueryset`

## Serving Items

- **Semantic Model**: `fab mkdir <ws>.Workspace/<name>.SemanticModel`
  - Configure **Direct Lake** mode for optimal performance on any Fabric source with Delta tables in OneLake (Lakehouse, Warehouse, SQL Database, Eventhouse) — see `decisions/visualization-selection.md`
  - Two variants: **Direct Lake on SQL endpoints** (GA, Lakehouse/Warehouse, with DirectQuery fallback) and **Direct Lake on OneLake** (Preview, any Fabric source, no fallback)
  - Version control model definitions via **TMDL** in git — all measure/relationship changes through PRs
  - First deployment requires **manual connection configuration** before the first refresh will succeed
- **Report**: `fab mkdir <ws>.Workspace/<name>.Report -P semanticModelId=<id>`
  - Rebind: `fab set <ws>.Workspace/<report>.Report -q semanticModelId -i "<id>"`

## Portal-Only Items

Items below require portal or REST API creation — `fab mkdir` is not supported. The engineer should document these as manual deployment steps in the deployment handoff.

### GraphQL API (GA)

- **Create:** Fabric Portal → workspace → + New Item → API for GraphQL
- **Configure:** Select data sources (Warehouse, SQL Database, Lakehouse SQL endpoint, Mirrored Database), choose tables/views to expose, define relationships
- **Schema:** Auto-generated from data source schemas — no custom resolver code needed
- **Verify:** Access the GraphQL endpoint URL from the item page; test queries in the built-in editor
- **Supports:** Warehouse, SQL Database, Lakehouse (via SQL endpoint), Mirrored Databases (Azure SQL, Cosmos DB, Snowflake, Databricks)

### User Data Functions (Preview)

- **Create:** Fabric Portal → workspace → + New Item → User Data Functions
- **Configure:** Write Python functions with `@udf.function()` decorator, add libraries via Library Management (PyPI)
- **Publish:** Select Publish to make functions callable — publishing may take a few minutes
- **Invoke:** REST endpoint (auto-generated), Pipeline activity, Notebook call, Activator rule
- **Verify:** Use Run Only mode in portal to test each function with sample inputs
- **Note:** Parameter names must use camelCase. The `fabric-user-data-functions` package is required.

### Variable Library (GA)

- **Create:** Fabric Portal → workspace → + New Item → Variable Library (Data Factory section)
- **Configure:** Add variables (Boolean, Integer, Number, String, DateTime, Guid, Item Reference), set default values, create value sets per stage
- **Value Sets:** Each value set maps to a deployment stage (Dev, PPE, Prod). One value set is active per workspace at a time.
- **Item References:** Store workspace ID + item ID pairs for dynamic binding to Notebooks, Pipelines, Shortcuts
- **Consume:** Notebooks (via NotebookUtils), Lakehouse Shortcuts, User Data Functions, Data Pipelines
- **Git:** Stored as JSON definition — syncable via Fabric Git integration
- **Verify:** Check variable values in the portal; verify consuming items reference the correct library
- **Limits:** Max 1,000 variables, 1,000 value sets, total cells < 10,000, item size < 1 MB

### Ontology (Preview)

- **Create:** Fabric Portal → workspace → + New Item → Ontology (IQ workload)
- **Configure:** Define entity types, properties, relationships. Bind to data sources (Lakehouse tables, Eventhouse streams, Semantic Models)
- **Refresh:** Manual refresh required after upstream data changes
- **Verify:** Use the ontology preview experience to visualize the graph model
- **Prerequisite:** Ontology tenant settings must be enabled by tenant admin
- **Note:** Preview feature — schema and capabilities may change

### Data Agent (Preview)

- **Create:** Fabric Portal → workspace → + New Item → Fabric Data Agent
- **Configure:** Add up to 5 data sources (Lakehouse, Warehouse, Semantic Model, KQL Database, Ontology). Select tables to expose. Add instructions (up to 15,000 chars) and example queries for few-shot learning.
- **Verify:** Ask test questions in the built-in chat; review generated SQL/DAX/KQL for accuracy
- **Prerequisite:** Fabric data agent tenant settings + cross-geo AI processing must be enabled
- **Note:** Read-only queries only — no data modification. Preview feature.

### Cosmos DB Mirroring (GA)

- **Create:** Fabric Portal → workspace → + New Item → Mirrored Azure Cosmos DB
- **Configure:** Connect to Azure Cosmos DB account (requires continuous backup enabled, NoSQL API only). Select databases and containers to mirror.
- **Result:** Creates mirrored database item + SQL analytics endpoint automatically
- **Replication:** Near real-time, zero RU consumption, automatic schema evolution
- **Verify:** Check replication status in the mirrored database item; query via SQL analytics endpoint
- **Note:** Nested JSON data accessible via OPENJSON in T-SQL queries
