# Item Definition Templates

Empty-state definition files for every Fabric item type, sourced from the
[Microsoft Fabric REST API documentation](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/item-definition-overview).

## Purpose

These templates are the **single source of truth** for item content deployed
via `fabric-cicd`.  The deploy script generator (`deploy-script-gen.py`) copies
files from here into each project's `workspace/` directory.  What you see on
disk is **byte-for-byte** what fabric-cicd will base64-encode and POST to the
Fabric Items API.

## Rules

1. **Do not invent content** — every file must match the API definition docs.
2. **Static types** are copied verbatim.  Dynamic types (Notebook, Report,
   SemanticModel, SQLDatabase) use the template as a base and the generator
   customizes runtime values (item name, dependency paths, etc.).
3. The `.platform` file is generated per-item by `deploy-script-gen.py` and is
   NOT stored here (it needs a unique `logicalId` UUID per item).
4. When adding a new item type, also update `item-type-registry.json` →
   `cicd.files` to list every file the type requires.

## Template inventory

| Item Type | Files | Source Doc |
|-----------|-------|-----------|
| ApacheAirflowJob | `apacheairflowjob-content.json`, `dags/dag1.py` | — |
| CopyJob | `copyjob-content.json` | [copyjob-definition](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/copyjob-definition) |
| DataPipeline | `pipeline-content.json` | [datapipeline-definition](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/datapipeline-definition) |
| Dataflow | `queryMetadata.json`, `mashup.pq` | [dataflow-definition](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/dataflow-definition) |
| Environment | `Setting/Sparkcompute.yml` | [environment-definition](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/environment-definition) |
| Eventhouse | `EventhouseProperties.json` | [eventhouse-definition](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/eventhouse-definition) |
| Eventstream | `eventstream.json`, `eventstreamProperties.json` | [eventstream-definition](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/eventstream-definition) |
| GraphQLApi | `graphql-definition.json` | [graphql-api-definition](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/graphql-api-definition) |
| KQLQueryset | `RealTimeQueryset.json` | [kql-queryset-definition](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/kql-queryset-definition) |
| Lakehouse | `lakehouse.metadata.json` | [lakehouse-definition](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/lakehouse-definition) |
| MirroredDatabase | `mirroring.json` | [mirrored-database-definition](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/mirrored-database-definition) |
| Notebook | `notebook-content.py` | [notebook-definition](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/notebook-definition) |
| Reflex | `ReflexEntities.json` | [reflex-definition](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/reflex-definition) |
| Report | `definition.pbir`, `report.json` | [report-definition](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/report-definition) |
| SemanticModel | `definition.pbism`, `definition/model.tmdl` | [semantic-model-definition](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/semantic-model-definition) |
| SparkJobDefinition | `SparkJobDefinitionV1.json` | [spark-job-definition](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/spark-job-definition) |
| SQLDatabase | `template.sqlproj` (renamed to `{name}.sqlproj`) | — |
| UserDataFunction | `function_app.py`, `definition.json`, `.resources/functions.json` | — |
| VariableLibrary | `variables.json`, `settings.json` | [variable-library-definition](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/variable-library-definition) |
