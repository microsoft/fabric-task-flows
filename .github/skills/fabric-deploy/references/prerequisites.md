# Prerequisites

Common prerequisites for deploying Microsoft Fabric task flows.

## CLI Tools

```bash
# Install the Fabric CLI (requires Python 3.10+)
pip install ms-fabric-cli

# Verify installation
fab --version
```

## Authentication

```bash
# Interactive login (local development)
fab auth login

# Service principal (CI/CD)
fab auth login -u <client_id> -p <client_secret> --tenant <tenant_id>

# Managed identity
fab auth login --identity
```

For the full command reference, see [Fabric CLI Commands](fabric-cli-commands.md).

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
# Find names with: fab ls .capacities
export FABRIC_CAPACITY_NAME="<capacity-display-name>"
```

## Workspace Setup

Create workspaces according to the strategy chosen during architecture:

### Single Workspace (per environment)

```bash
# Create one workspace per environment
fab mkdir my-project-ppe.Workspace
fab mkdir my-project-prod.Workspace
```

### Multi-Workspace (per category × environment)

```bash
# Example: 3 categories × 2 environments = 6 workspaces
fab mkdir my-project-storage-ppe.Workspace
fab mkdir my-project-storage-prod.Workspace
fab mkdir my-project-engineering-ppe.Workspace
fab mkdir my-project-engineering-prod.Workspace
fab mkdir my-project-presentation-ppe.Workspace
fab mkdir my-project-presentation-prod.Workspace
```

Use consistent naming: `{project}-{category}-{environment}`. See `_shared/cicd-practices.md` for workspace strategy guidance.

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

## CI/CD Deployment Tool (Optional)

For automated CI/CD pipelines, install the `fabric-cicd` library (v0.1.23, Public Preview; requires Python 3.10+) alongside the Fabric CLI:

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

See `_shared/cicd-practices.md` for parameterization, per-item considerations, and release pipeline examples.

## Design-Only Mode

When using design-only mode (selected during architecture), the Fabric CLI and authentication are **not required at design time**. The architect and tester agents work normally — only deployment is deferred.

**At design time (no prerequisites):**
- Architecture decisions, task flow selection, and test planning proceed without any CLI or workspace access
- The engineer generates self-contained deploy scripts instead of deploying

**At deploy time (when running the generated scripts):**
- Python 3.10+ and `fab` CLI (`pip install ms-fabric-cli`)
- Valid Fabric authentication — run `fab auth login` before the script (the script verifies auth and exits with instructions if not authenticated)
- Fabric Capacity — the script presents an interactive capacity picker (or set `FABRIC_CAPACITY_NAME` env var to skip)
- Workspace Contributor permissions (the script creates the workspace if needed)

The generated scripts prompt for **workspace name** and present an **interactive capacity picker** (with environment variable fallback). The script runs a preflight check for authentication and exits with clear instructions if `fab auth status` fails.

```bash
# Step 1: Authenticate (one-time)
fab auth login

# Step 2 (optional): Pre-set values as environment variables
export FABRIC_WORKSPACE_NAME="my-project-dev"
export FABRIC_CAPACITY_NAME="My Capacity Name"

# Step 3: Run the deploy script
./deploy-my-project.ps1
```
