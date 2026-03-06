# Deployment Patterns by Item Type

Reference for `fab mkdir` commands and item-specific configuration when deploying Fabric items.

## Storage Items

- **Lakehouse**: `fab mkdir <ws>.Workspace/<name>.Lakehouse`
  - With schemas: add `-P enableSchemas=true`
  - For medallion: create Bronze, Silver, and Gold as separate Lakehouses
- **Warehouse**: `fab mkdir <ws>.Workspace/<name>.Warehouse`
- **Eventhouse**: `fab mkdir <ws>.Workspace/<name>.Eventhouse`
  - Then create KQL Database: `fab mkdir <ws>.Workspace/<name>.KQLDatabase -P eventhouseId=<id>`

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
