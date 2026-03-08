# Validation Patterns by Item Type

> ⚠️ **DEPRECATED** — This file documents legacy `fab exists` patterns. The project standard is `validate-items.py` (REST API). This reference is retained for historical context only.

Legacy `fab` CLI commands and criteria for verifying each item type after deployment.

## Storage Validation

- **Lakehouse**: `fab exists <ws>.Workspace/<name>.Lakehouse` — tables exist, permissions set, SQL endpoint accessible
- **Warehouse**: `fab exists <ws>.Workspace/<name>.Warehouse` — schemas created, stored procedures deployed
- **Eventhouse**: `fab exists <ws>.Workspace/<name>.Eventhouse` — KQL database responsive, retention configured

## Ingestion Validation

- **Copy Job**: `fab job run-list <ws>.Workspace/<name>.CopyJob` — source connected, data copied successfully
- **Pipeline**: `fab job run-list <ws>.Workspace/<name>.DataPipeline` — activities completed, no failures in runs
- **Eventstream**: `fab exists <ws>.Workspace/<name>.Eventstream` — events flowing, transformations applied
- **Dataflow Gen2**: Refresh completed, data quality checks pass

## Processing Validation

- **Notebook**: `fab job run <ws>.Workspace/<name>.Notebook` — runs successfully against environment
- **Spark Job**: `fab job run <ws>.Workspace/<name>.SparkJobDefinition` — job completes within expected time
- **KQL Queryset**: `fab exists <ws>.Workspace/<name>.KQLQueryset` — queries return expected results

## Serving Validation

- **Semantic Model**: `fab get <ws>.Workspace/<name>.SemanticModel -q properties` — refresh succeeds, relationships correct
- **Report/Dashboard**: `fab exists <ws>.Workspace/<name>.Report` — visuals render, filters work
