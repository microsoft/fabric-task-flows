# Verified Item Definition Files — Authoritative Reference

> **DO NOT modify item type file generation in `deploy-script-gen.py` without updating this document.**
> Every item type is tracked here with its API capability, fabric-cicd requirement, and deployment status.

## How to Read This Table

| Column | Meaning |
|--------|---------|
| **API: No Def** | Can the Fabric REST API create this item without a definition? |
| **API: With Def** | Can the Fabric REST API create this item with a definition? |
| **fabric-cicd Requires** | What files does fabric-cicd actually need to deploy? |
| **Our Strategy** | `.platform` only OR `.platform` + content files |
| **Deploy Status** | ✅ Verified working / ⚠️ Stub (untested) / ❌ Known broken |

## All 25 fabric-cicd Supported Types

### Category: `.platform` ONLY — No content files needed

These items can be created without a definition AND fabric-cicd doesn't need content files.

| Item Type | API: No Def | API: With Def | Our Strategy | Deploy Status |
|-----------|------------|---------------|--------------|---------------|
| Lakehouse | ✅ | ✅ | `.platform` only | ✅ Verified |
| Warehouse | ✅ | ❌ | `.platform` only | ✅ Verified |
| MLExperiment | ✅ | ❌ | `.platform` only | ✅ Verified |
| KQLDashboard | ✅ | ✅ | `.platform` only — content file causes fabric-cicd parser error | ✅ Verified |

### Category: `.platform` + REQUIRED content files

These items either require a definition (API: No Def = ❌) or fabric-cicd needs content files to deploy properly.

| Item Type | API: No Def | API: With Def | Required Files | Sample Source | Deploy Status |
|-----------|------------|---------------|----------------|--------------|---------------|
| Environment | ✅ | ✅ | `Setting/Sparkcompute.yml` | Error: "Required file missing" | ✅ Verified |
| VariableLibrary | — | — | `variables.json` + `settings.json` | Sample: `Vars.VariableLibrary` | ✅ Verified |
| Notebook | ✅ | ✅ | `notebook-content.py` | Sample: `Hello World.Notebook` | ✅ Verified |
| SemanticModel | ❌ | ✅ | `definition.pbism` + `definition/model.tmdl` | Sample: `ABC.SemanticModel` | ✅ Verified |
| Report | ❌ | ✅ | `definition.pbir` (byPath) + `report.json` | Sample: `ABCD.Report` | ✅ Verified |
| DataPipeline | ✅ | ✅ | `pipeline-content.json` | Error: file not found | ✅ Verified |
| Eventstream | ✅ | ✅ | `eventstream.json` (needs `compatibilityLevel: "1.0"`) + `eventstreamProperties.json` | Sample + error-driven | ✅ Verified |
| KQLQueryset | ✅ | ✅ | `RealTimeQueryset.json` | Sample: `SampleKQLQueryset.KQLQueryset` | ✅ Verified |
| Eventhouse | ✅ | ✅ | `EventhouseProperties.json` (`{}`) | Sample: `SampleEventhouse.Eventhouse` | ✅ Verified |
| Reflex | ✅ | ✅ | `ReflexEntities.json` (`[]`) | Sample: `SampleDataActivator.Reflex` | ✅ Verified |

### Category: Stubs — Not yet deployed in any project

These have content file stubs generated but have NOT been tested in a real deployment.

| Item Type | API: No Def | API: With Def | Stub Files | Sample Exists? | Deploy Status |
|-----------|------------|---------------|------------|----------------|---------------|
| CopyJob | ✅ | ✅ | `copyjob-content.json` | Yes: `Hello Copy Job.CopyJob` | ⚠️ Untested |
| Dataflow | ✅ | ✅ def only | `mashup.pq` | Yes: `Hello Dataflow.Dataflow` | ⚠️ Untested |
| GraphQLApi | ✅ | ✅ def only | `graphql-definition.json` | Yes: `Sample.GraphQLApi` | ⚠️ Untested |
| SparkJobDefinition | ✅ | ✅ | `SparkJobDefinitionV1.json` | Yes: `Sample.SparkJobDefinition` | ⚠️ Untested |
| SQLDatabase | ✅ | ✅ | `{name}.sqlproj` | Yes: `Hello db.SQLDatabase` | ⚠️ Untested |
| UserDataFunction | — | — | `function_app.py` + `definition.json` + `.resources/functions.json` | Yes: `Sample.UserDataFunction` | ⚠️ Untested |
| MirroredDatabase | ❌ | ✅ | `mirroring.json` | Yes: `MirroredDatabase_1.MirroredDatabase` | ⚠️ Untested |
| ApacheAirflowJob | — | — | `apacheairflowjob-content.json` + `dags/dag1.py` | Yes: sample | ⚠️ Untested |
| MountedDataFactory | ❌ | ✅ | Unknown | No sample | ⚠️ Unknown |
| DataAgent | — | — | Unknown | No sample | ⚠️ Unknown |

## Key Learnings (Do Not Repeat These Mistakes)

1. **API "create without definition = ✅" does NOT mean fabric-cicd skips content files.** fabric-cicd reads the local directory and may expect content files even when the API doesn't require them.

2. **Empty stubs with wrong structure cause errors.** Example: `{"entities": []}` for Reflex fails, but `[]` works. Always copy exact content from the sample repo.

3. **Some items need extra files not obvious from the API.** Eventstream needs `eventstreamProperties.json` (not in API docs), Environment needs `Setting/Sparkcompute.yml` (not in API docs).

4. **Some items work BETTER without content files.** KQLDashboard's content file causes a fabric-cicd parser crash — `.platform` only works fine.

5. **When adding a new item type: check the sample repo FIRST, then test deployment, then update this file.**
