# Fabric CLI Command Reference

The Fabric CLI (`fab`) is the preferred tool for deploying and managing Microsoft Fabric items. Install with `pip install ms-fabric-cli`.

Full documentation: https://microsoft.github.io/fabric-cli/

## Authentication

```bash
# Interactive (local development)
fab auth login

# Service principal (CI/CD)
fab auth login -u <client_id> -p <client_secret> --tenant <tenant_id>

# Managed identity
fab auth login --identity
```

## Item Creation (`fab mkdir`)

> **Workspace creation requires a capacity.** Pass `-P capacityName=<name>` or set `fab config set default_capacity <name>` first. List capacities with `fab ls .capacities`. Prefer `config set` — it handles special characters in capacity names that `-P` may strip.

> **Naming restrictions:** Some item types reject hyphens (`-`) in names. Use underscores (`_`) instead for: **Eventstream**, **MLExperiment**, **MLModel**. All other types accept hyphens.

### Storage

```bash
fab mkdir <workspace>.Workspace/<name>.Lakehouse
fab mkdir <workspace>.Workspace/<name>.Lakehouse -P enableSchemas=true
fab mkdir <workspace>.Workspace/<name>.Warehouse
fab mkdir <workspace>.Workspace/<name>.Eventhouse
fab mkdir <workspace>.Workspace/<name>.KQLDatabase -P eventhouseId=<id>
fab mkdir <workspace>.Workspace/<name>.SQLDatabase
fab mkdir <workspace>.Workspace/<name>.Datamart
fab mkdir <workspace>.Workspace/<name>.MirroredWarehouse
fab mkdir <workspace>.Workspace/<name>.MirroredDatabase

# Cosmos DB — portal only (no fab mkdir support)
# Create via Portal → + New Item → Cosmos DB database
```

### Ingestion

```bash
fab mkdir <workspace>.Workspace/<name>.DataPipeline
fab mkdir <workspace>.Workspace/<name>.Eventstream
fab mkdir <workspace>.Workspace/<name>.MountedDataFactory

# CopyJob — portal only (commented out in CLI v0.1.10)
# Dataflow Gen2 — portal only
```

### Processing

```bash
fab mkdir <workspace>.Workspace/<name>.Environment
fab mkdir <workspace>.Workspace/<name>.Notebook
fab mkdir <workspace>.Workspace/<name>.SparkJobDefinition
fab mkdir <workspace>.Workspace/<name>.KQLQueryset
```

### ML

```bash
fab mkdir <workspace>.Workspace/<name>.MLExperiment
fab mkdir <workspace>.Workspace/<name>.MLModel
```

### Serving

```bash
fab mkdir <workspace>.Workspace/<name>.SemanticModel
fab mkdir <workspace>.Workspace/<name>.Report -P semanticModelId=<id>
```

## Configuration (`fab set`)

```bash
# Bind notebook to default lakehouse
fab set <ws>.Workspace/<nb>.Notebook -q lakehouse -i '<lakehouse_json>'

# Set notebook environment
fab set <ws>.Workspace/<nb>.Notebook -q environment -i '<environment_json>'

# Rebind report to semantic model
fab set <ws>.Workspace/<report>.Report -q semanticModelId -i "<model_id>"

# Rename an item
fab set <ws>.Workspace/<item>.Type -q displayName -i "New Name"

# Set item description
fab set <ws>.Workspace/<item>.Type -q description -i "Description text"
```

## Data Operations

```bash
# Upload file to OneLake (alias: copy)
fab cp ./local/data.csv <ws>.Workspace/<lh>.Lakehouse/Files/data.csv

# Download from OneLake
fab cp <ws>.Workspace/<lh>.Lakehouse/Files/data.csv ./local/

# Load data into lakehouse table
fab table load Tables/<table_name> --file data.csv
fab table load Tables/<table_name> --file data/ --format format=parquet --mode append

# Optimize table
fab table optimize Tables/<table_name> --vorder
```

## Job Execution

```bash
# Run pipeline synchronously (waits for completion)
fab job run <ws>.Workspace/<pipeline>.DataPipeline

# Run notebook with parameters
fab job run <ws>.Workspace/<nb>.Notebook -P param1:string=value1

# Start pipeline asynchronously
fab job start <ws>.Workspace/<pipeline>.DataPipeline

# Schedule a notebook
fab job run-sch <ws>.Workspace/<nb>.Notebook --type daily --interval "09:00,15:00"

# Check job status
fab job run-status <ws>.Workspace/<item>.Type --id <job_id>

# List job runs
fab job run-list <ws>.Workspace/<item>.Type
```

## Shortcuts (`fab ln`)

```bash
# Internal OneLake shortcut (alias: mklink)
fab ln Files/scut.Shortcut --type oneLake --target ../../<ws2>.Workspace/<lh>.Lakehouse/Files

# External shortcut (ADLS Gen2)
fab ln Tables/ext_table.Shortcut --type adlsGen2 -i '<inline_json_w_location_subpath_connectionid>'
```

## Import / Export

```bash
# Export item definition to local directory
fab export <ws>.Workspace/<nb>.Notebook -o ./exports

# Import item definition from local
fab import <ws>.Workspace/<nb>.Notebook -i ./exports/nb.Notebook

# Import notebook from .py file
fab import <ws>.Workspace/<nb>.Notebook -i ./script.py --format .py
```

## Verification

```bash
# Check if an item exists (outputs '* true' or '* false'; exit code is always 0)
fab exists <ws>.Workspace/<item>.Type

# List all items in a workspace (alias: dir)
fab ls <ws>.Workspace
fab ls <ws>.Workspace -l

# Get item details (use -q for JMESPath queries)
fab get <ws>.Workspace/<item>.Type
fab get <ws>.Workspace/<item>.Type -q .

# Inspect table schema
fab table schema Tables/<table_name>
```

## Capacity Assignment (`fab assign`)

```bash
# Assign a capacity to a workspace (uses capacity NAME, not GUID)
fab assign .capacities/<capacity_name>.Capacity -W <ws>.Workspace

# Assign a domain to a workspace
fab assign .domains/<domain_name>.Domain -W <ws>.Workspace -f
```

> **Note:** `fab assign` uses the capacity **display name**, not a GUID. Find capacity names in the Fabric Admin Portal → Capacities, or via `fab ls .capacities`.

## Portal-Only Items (No `fab mkdir` Support)

The following Fabric item types cannot be created with `fab mkdir`. Use the Fabric Portal.

| Item Type | CLI Type | Creation Method | CLI Operations |
|-----------|----------|-----------------|----------------|
| Dashboard | `.Dashboard` | Portal → + New Item → Dashboard | get, ls |
| Activator | `.Reflex` | Portal → + New Item → Activator | get, set, export, import |
| Real-Time Dashboard | `.KQLDashboard` | Portal → + New Item → Real-Time Dashboard | get, set, export, import |
| GraphQL API | `.GraphQLApi` | Portal → + New Item → API for GraphQL | get, set |
| CopyJob | `.CopyJob` | Portal → + New Item → Copy Job | get (commented out in CLI v0.1.10) |
| Dataflow Gen2 | `.DataflowGen2` | Portal → + New Item → Dataflow Gen2 | — |
| Paginated Report | `.PaginatedReport` | Portal or Power BI Desktop | get, ls |

> Use `fab desc .<Type>` to check which operations any item type supports.
