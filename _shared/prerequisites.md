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
# Optional: Set workspace ID
export FABRIC_WORKSPACE_ID="<workspace-guid>"
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
