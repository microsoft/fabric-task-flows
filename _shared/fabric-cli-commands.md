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

### Storage

```bash
fab mkdir <workspace>.Workspace/<name>.Lakehouse
fab mkdir <workspace>.Workspace/<name>.Lakehouse -P enableSchemas=true
fab mkdir <workspace>.Workspace/<name>.Warehouse
fab mkdir <workspace>.Workspace/<name>.Eventhouse
fab mkdir <workspace>.Workspace/<name>.KQLDatabase -P eventhouseId=<id>
fab mkdir <workspace>.Workspace/<name>.SQLDatabase

# Cosmos DB — portal only (no fab mkdir support)
# Create via Portal → + New Item → Cosmos DB database
```

### Ingestion

```bash
fab mkdir <workspace>.Workspace/<name>.CopyJob
fab mkdir <workspace>.Workspace/<name>.DataPipeline
fab mkdir <workspace>.Workspace/<name>.Eventstream
```

### Processing

```bash
fab mkdir <workspace>.Workspace/<name>.Environment
fab mkdir <workspace>.Workspace/<name>.Notebook
fab mkdir <workspace>.Workspace/<name>.SparkJobDefinition
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
# Upload file to OneLake
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
# Internal OneLake shortcut
fab ln <ws>.Workspace/<shortcut_path> --type lakehouse --target <ws2>.Workspace/<lh>.Lakehouse

# External shortcut (ADLS Gen2)
fab ln <ws>.Workspace/<shortcut_path> --type adlsGen2 -i '<connection_json>'
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
# Check if an item exists
fab exists <ws>.Workspace/<item>.Type

# List all items in a workspace
fab ls <ws>.Workspace
fab ls <ws>.Workspace -l

# Filter items by name
fab ls <ws>.Workspace -q "[?contains(name, 'Bronze')]"

# Get item details
fab get <ws>.Workspace/<item>.Type
fab get <ws>.Workspace/<item>.Type -q properties

# Inspect table schema
fab table schema Tables/<table_name>
```

## Portal-Only Items (No CLI Support)

The following Fabric item types cannot be created with `fab mkdir`. Use the Fabric Portal or REST API.

| Item Type | Status | Creation Method | Notes |
|-----------|--------|----------------|-------|
| GraphQL API | GA | Portal → + New Item → API for GraphQL | Auto-generates schema from data sources |
| User Data Functions | Preview | Portal → + New Item → User Data Functions | Python functions with `@udf.function()` decorator |
| Variable Library | GA | Portal → + New Item → Variable Library | Git-syncable JSON definition |
| Data Agent | Preview | Portal → + New Item → Fabric Data Agent | Up to 5 data sources, NL2SQL/DAX/KQL |
| Ontology | Preview | Portal → + New Item → Ontology | IQ workload, requires tenant settings |
| Cosmos DB Database (native) | Preview | Portal → + New Item → Cosmos DB database | AI-optimized NoSQL, auto-mirrors to OneLake |
| Cosmos DB Mirroring (external) | GA | Portal → + New Item → Mirrored Azure Cosmos DB | Requires continuous backup on Cosmos account |
| Real-Time Dashboard | GA | Portal → + New Item → Real-Time Dashboard | Backed by Eventhouse/KQL |
| Activator | GA | Portal → + New Item → Activator | Rules-based alerting |

> **Deployment impact:** The `@fabric-engineer` agent should document these as manual portal steps in the deployment handoff. Use `fab exists` and `fab get` to verify after manual creation where item types are supported.
