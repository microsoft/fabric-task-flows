# CI/CD Reference for Microsoft Fabric

## Deployment Tool

> **⚠️ `fabric-cicd` is the sole deployment tool.** Do NOT use `ms-fabric-cli` (`fab`) for deployment or validation.

```bash
pip install fabric-cicd
```

Key characteristics:
- **Full deployment every time** — no commit diffs
- **Automatic dependency ordering** — handles item creation sequence
- **Same-workspace auto-repointing** — Reports → Semantic Models, Pipelines → items, etc.
- **Cross-workspace references need parameterization** via `parameter.yml`
- Docs: https://microsoft.github.io/fabric-cicd/

Compact deployment script:

```python
from fabric_cicd import FabricWorkspace, publish_all_items, unpublish_all_orphan_items

ws = FabricWorkspace(
    workspace_id="<workspace-id>",
    environment="PPE",                  # matches parameter.yml keys
    repository_directory="./workspace",
    item_type_in_scope=["Notebook", "DataPipeline", "Environment", "SemanticModel", "Report"],
)
publish_all_items(ws)
unpublish_all_orphan_items(ws)
```

> For Azure DevOps pipeline templates, see the [fabric-cicd documentation](https://microsoft.github.io/fabric-cicd/).

---

## Per-Item Deployment Considerations

These behaviors apply regardless of deployment tool and are critical for the engineer to know.

| Item Type | Auto-Repoints (Same Workspace) | Needs Parameterization (Cross-Workspace) | Manual Setup Required | Key Gotcha |
|-----------|-------------------------------|------------------------------------------|----------------------|------------|
| **Notebook** | No | Yes — lakehouse GUID, workspace ID | — | Resources (files) not deployed via source control |
| **Environment** | — | Yes — `spark_pool` section | Publish after creation | Custom pools revert to starter pool without parameterization; libraries cause 20+ min publish times |
| **Semantic Model** | Maybe (test first) | Yes — source connections | **Manual connection config on first deployment** | First refresh fails without manual config |
| **Data Pipeline** | Yes — same-workspace items | Yes — cross-workspace items, connections | Connection creation | Connections not source-controlled |
| **Eventhouse** | — | No (`find_replace` not applied) | — | Use `exclude_path` when attached to KQL Database |
| **KQL Queryset** | — | Yes — KQL database reference | — | Cluster URI auto-handled for same-workspace KQL DBs |
| **Report** | Yes — same-workspace Semantic Model | Yes — cross-workspace Semantic Model | — | — |
| **Eventstream** | Yes — same-workspace destinations | Yes — cross-workspace destinations | Wait for table population | — |
| **Warehouse** | — | No (`find_replace` not applied) | **DDL deployed separately** (DACPAC/dbt) | Only item shell is deployed |
| **Lakehouse** | — | No (`find_replace` not applied) | — | Schemas not deployed unless shortcut present; unpublish disabled by default |
| **Real-Time Dashboard** | — | Yes — KQL database reference | — | Cluster URI auto-handled for same-workspace |
| **SQL Database** | — | No (`find_replace` not applied) | **DDL deployed separately** | Only item shell is deployed |
| **Copy Job** | — | Yes — connections | **Manual connection config on first deployment** | — |

---

## Connection Management

### Connection Dictionary Pattern

For projects with multiple environments, centralize all endpoint references in a shared notebook:

```python
# Util_Connection_Library notebook
env = "ppe"  # parameterized per environment

connection = {
    "lakehouse_default": f"abfss://eng-{env}-storage@onelake.dfs.fabric.microsoft.com/Core.Lakehouse",
    "warehouse_gold": f"abfss://eng-{env}-analytics@onelake.dfs.fabric.microsoft.com/Gold.Warehouse",
}
```

Usage in other notebooks:

```python
%run Util_Connection_Library
df = spark.read.format("delta").load(connection["lakehouse_default"] + "/Tables/transactions")
```

### Connection Pre-Creation

For multi-environment deployments:

1. Create connections in **Manage connections and gateways** portal for each environment (PPE, PROD)
2. Share connections with a **security group** that includes all developers and deployment identities
3. Parameterize connection GUIDs in `parameter.yml` or deployment scripts

---

## Environment & Spark Pools

**Always attach Environment items to capacity pools when using custom Spark pools.**

- **Capacity pool** — referenced by a known, consistent GUID that exists across workspaces. Safe for source control.
- **Workspace pool** — referenced by a GUID tied to a specific workspace. When committed to source control, the GUID is meaningless outside that workspace.

Use consistent naming for capacity pools across environments (e.g., `CapacityPool_Medium`, `CapacityPool_Large`) to simplify parameterization.

### Parameterizing Spark Pools

In `parameter.yml`:

```yaml
spark_pool:
    - instance_pool_id: "dev-workspace-pool-guid"
      replace_value:
          PPE:
              type: "Capacity"
              name: "CapacityPool_Medium"
          PROD:
              type: "Capacity"
              name: "CapacityPool_Large"
```

---

## Git Branching

### PPE-First (Recommended for Multi-Environment)

```
feature/my-work ──► ppe (default branch) ──► main (production)
                         │                        │
                    PPE workspace            PROD workspace
                    (deployed via CI/CD)     (deployed via CI/CD)
```

- PPE is the default branch — in-flight work never accidentally targets production
- Cherry-pick from PPE to main for production promotion
- Feature branches are connected to individual workspaces via Git Sync

---

> **Parameterization:** See [parameterization-selection.md](../../../decisions/parameterization-selection.md) for approach comparison.
