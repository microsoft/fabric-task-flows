# Prerequisites

Common prerequisites for deploying Microsoft Fabric task flows.

## Deployment Tool

```bash
# Install fabric-cicd (requires Python 3.10+)
pip install fabric-cicd

# Verify installation
python -c "import fabric_cicd; print('fabric-cicd installed')"
```

> **⚠️ `fabric-cicd` is the sole deployment dependency.** It provides deployment, and its transitive dependencies (`azure-identity`, `requests`) power REST API validation. Do NOT install `ms-fabric-cli` for new projects.

## Authentication

Authentication is handled by `DefaultAzureCredential` (provided by `azure-identity`, a transitive dependency of `fabric-cicd`). It automatically tries:

1. **Environment variables** — `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET` (for CI/CD)
2. **Managed Identity** — when running on Azure
3. **Azure CLI** — `az login` (for local development)
4. **Interactive browser** — fallback

For local development, authenticate with `az login` before running deploy or validation scripts.

## Required Permissions

| Resource | Permission |
|----------|------------|
| Fabric Workspace | Contributor or higher |
| Semantic Model | Build permission for binding |
| Data Sources | Appropriate credentials configured |

## Environment Variables

```bash
# Optional: Pre-set workspace name (skips interactive prompt in deploy scripts)
export FABRIC_WORKSPACE_NAME="<workspace-name>"

# Optional: Pre-set capacity name (skips interactive picker in deploy scripts)
export FABRIC_CAPACITY_NAME="<capacity-display-name>"
```

## Workspace Setup

Workspaces are created automatically by the generated deploy scripts via the Fabric REST API. The strategy is chosen during architecture:

### Single Workspace (per environment)

The deploy script creates one workspace per environment (e.g., `my-project-ppe`, `my-project-prod`) with an interactive picker.

### Multi-Workspace (per category × environment)

Items are separated into workspace categories (e.g., storage, engineering, presentation), each with PPE and PROD instances.

Use consistent naming: `{project}-{category}-{environment}`. See `cicd-practices.md` for workspace strategy guidance.

## Connection Setup

For multi-environment deployments, pre-create connections before deploying items:

1. Go to **Manage connections and gateways** in the Fabric portal
2. Create connections for each environment (PPE, PROD) — e.g., SQL Server, ADLS Gen2, Event Hubs
3. Share connections with a **security group** that includes all developers and deployment service principals
4. Record connection GUIDs for use in `parameter.yml` or deployment scripts

## Capacity Pools

When using custom Spark pools with Environment items:

1. Create capacity pools with **consistent names** across environments (e.g., `CapacityPool_Medium`, `CapacityPool_Large`)
2. Attach Environment items to **capacity pools** (not workspace pools) — workspace pool references create unresolvable GUIDs in source control
3. Parameterize pool references in `parameter.yml` for cross-environment promotion

## CI/CD Pipelines

For automated CI/CD pipelines using `fabric-cicd`:

```bash
# Install fabric-cicd (v0.1.23, Public Preview)
pip install fabric-cicd

# Verify installation
python -c "import fabric_cicd; print('fabric-cicd installed')"
```

Basic usage:

```python
from fabric_cicd import FabricWorkspace, publish_all_items

workspace = FabricWorkspace(
    workspace_id="your-workspace-id",
    environment="PPE",
    repository_directory="./workspace",
    item_type_in_scope=["Notebook", "DataPipeline", "Environment"],
)

publish_all_items(workspace)
```

Full documentation: https://microsoft.github.io/fabric-cicd/0.1.23/

See `fabric-design/references/cicd-practices.md` for parameterization, per-item considerations, and release pipeline examples.

## Design-Only Mode

When using design-only mode (selected during architecture), authentication and deployment tools are **not required at design time**. The architect and tester agents work normally — only deployment is deferred.

**At design time (no prerequisites):**
- Architecture decisions, task flow selection, and test planning proceed without any workspace access
- The engineer generates self-contained deploy scripts instead of deploying

**At deploy time (when running the generated scripts):**
- Python 3.10+ and `fabric-cicd` (`pip install fabric-cicd`)
- Valid Azure authentication — run `az login` before the script, or set service principal env vars
- Fabric Capacity — the script presents an interactive capacity picker (or set `FABRIC_CAPACITY_NAME` env var to skip)
- Workspace Contributor permissions (the script creates the workspace if needed)

The generated scripts prompt for **workspace name** and present an **interactive capacity picker** (with environment variable fallback). The script runs a preflight check for authentication and exits with instructions if not authenticated.

```bash
# Step 1: Authenticate (one-time)
az login

# Step 2 (optional): Pre-set values as environment variables
export FABRIC_WORKSPACE_NAME="my-project-dev"
export FABRIC_CAPACITY_NAME="My Capacity Name"

# Step 3: Run the deploy script
python deploy-my-project.py
```
