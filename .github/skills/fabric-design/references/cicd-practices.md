# CI/CD Practices for Microsoft Fabric

Best practices for continuous integration and deployment of Fabric items, drawn from [Microsoft's internal Azure Data team](https://blog.fabric.microsoft.com/en-US/blog/optimizing-for-ci-cd-in-microsoft-fabric) and the [`fabric-cicd` Python library](https://microsoft.github.io/fabric-cicd/0.1.23/).

---

## Workspace Strategy (User Choice)

**This is a decision the user makes, not a default.** The architect must present both options with trade-offs and let the user choose.

### Option A: Single Workspace per Environment

All Fabric items live in one workspace, replicated per environment (e.g., `my-project-ppe`, `my-project-prod`).

| Pros | Cons |
|------|------|
| Simple to manage and navigate | Large workspaces become cluttered |
| Fewer permissions to configure | Feature branch isolation is harder |
| Lower cognitive overhead for small teams | All items share the same capacity settings |
| Easy onboarding for new team members | Item naming must be disciplined to avoid confusion |

**Best for:** Small teams, < 30 items, single-concern projects, teams new to Fabric.

### Option B: Multi-Workspace Segmentation

Items are separated into workspace categories (e.g., storage, engineering, orchestration, presentation), each with PPE and PROD instances.

| Pros | Cons |
|------|------|
| Cleaner separation of concerns | Many workspaces to manage (categories × environments) |
| Feature branch notebooks point to PPE Lakehouse (no data rehydration) | Requires strict naming conventions |
| Independent deployment of categories | Cross-workspace references need parameterization |
| Better access control per concern area | Higher learning curve |

**Best for:** Large teams, > 30 items, multiple concurrent developers, strict access control needs.

### Decision Guidance

| Factor | Favors Single | Favors Multi |
|--------|---------------|--------------|
| Team size | < 5 developers | > 5 developers |
| Item count | < 30 items | > 30 items |
| Feature branches | Rare / none | Frequent |
| Access control | Uniform | Per-concern |
| Lakehouse data | Small / fast to replicate | Large / expensive to replicate |

---

## Deployment Tool

> **⚠️ `fabric-cicd` is the sole deployment tool.** Do NOT use `ms-fabric-cli` (`fab`) for deployment or validation.

```bash
pip install fabric-cicd
```

```python
from fabric_cicd import FabricWorkspace, publish_all_items, unpublish_all_orphan_items

target = FabricWorkspace(
    workspace_id="your-workspace-id",
    environment="PPE",                    # matches parameter.yml keys
    repository_directory="./workspace",   # local repo directory with item folders
    item_type_in_scope=["Notebook", "DataPipeline", "Environment"],
)

publish_all_items(target)                 # deploy all in-scope items
unpublish_all_orphan_items(target)        # remove items not in repo
```

Key characteristics:
- **Full deployment every time** — no commit diffs
- **Automatic dependency ordering** — handles item creation sequence
- **Same-workspace auto-repointing** — Reports → Semantic Models, Pipelines → items, etc.
- **Cross-workspace references need parameterization** via `parameter.yml`
- Docs: https://microsoft.github.io/fabric-cicd/0.1.23/

---

## Parameterization

Three approaches for environment-specific configuration, from Fabric-native to code-driven:

| Approach | Best For | Tool |
|----------|----------|------|
| Variable Library | Fabric-native, multi-env, item references | Portal / REST API / Git |
| `parameter.yml` | Automated `fabric-cicd` pipelines, deployment-time replacement | `fabric-cicd` Python library |
| Environment variables | Single-env, simple deploy scripts | Shell / CI/CD variables |

### Variable Library (Fabric-Native)

> **Preferred for Fabric-native CI/CD.** Variable Libraries are workspace items that centralize configuration across deployment stages without external files or scripts.

**How it works:**
1. Create a Variable Library item in the workspace
2. Define variables (String, Integer, Boolean, Guid, DateTime, Item Reference)
3. Create **value sets** per deployment stage (Dev, PPE, Prod)
4. Activate the appropriate value set per workspace — all consuming items reconfigure automatically

**Item Reference variables** store `workspaceId + itemId` pairs, enabling dynamic binding:
- Notebooks reference different Lakehouses per stage (via `NotebookUtils`)
- Shortcuts point to different source Lakehouses per stage
- User Data Functions connect to stage-specific data sources

**When to use Variable Library:**
- ✅ Multi-environment deployments where items need stage-specific configuration
- ✅ Teams already using Fabric's built-in Git integration
- ✅ Projects where Notebooks, Pipelines, and Shortcuts need dynamic item references
- ✅ When you want parameterization without external tooling

**When to use `parameter.yml` instead:**
- When using the `fabric-cicd` Python library for automated deployment pipelines
- When you need parameterization of item definitions at deployment time (not runtime)

**When to use environment variables instead:**
- Single-environment projects with simple `fab` CLI scripts
- When Variable Library is overkill for the project's complexity

**Limits:** Max 1,000 variables, 1,000 value sets, total cells < 10,000, item size < 1 MB.

**Git integration:** Variable Library definitions are stored as JSON and sync via Fabric's built-in Git. Changes to variables are tracked in source control.

**Deployment order:** Variable Library must be created and populated **before** consuming items (Notebooks, Pipelines, Shortcuts) are deployed. Place it in Wave 1 alongside foundation items.

### parameter.yml (fabric-cicd)

The `parameter.yml` file sits at the root of your repository directory and handles environment-specific value replacement.

#### File Location

```
/repository-directory/
    /item-name.ItemType/
        ...
    /another-item.Notebook/
        ...
    /parameter.yml           ← here
```

#### find_replace (String/Regex Replacement)

For replacing values in text-based files (Notebooks, etc.):

```yaml
find_replace:
    # Replace a Lakehouse GUID across environments
    - find_value: "123e4567-e89b-12d3-a456-426614174000"
      replace_value:
          PPE: "f47ac10b-58cc-4372-a567-0e02b2c3d479"
          PROD: "9b2e5f4c-8d3a-4f1b-9c3e-2d5b6e4a7f8c"
      item_type: "Notebook"

    # Use dynamic variables (resolve at deploy time)
    - find_value: "8f5c0cec-a8ea-48cd-9da4-871dc2642f4c"
      replace_value:
          PPE: "$workspace.id"
          PROD: "$workspace.id"

    # Reference deployed item attributes
    - find_value: "old-lakehouse-guid"
      replace_value:
          PPE: "$items.Lakehouse.my-lakehouse.id"
          PROD: "$items.Lakehouse.my-lakehouse.id"
```

**Dynamic variables:**
- `$workspace.id` — resolves to the target workspace ID
- `$items.Type.Name.id` — resolves to the deployed item's ID
- `$items.Type.Name.sqlendpoint` — resolves to the item's SQL endpoint
- `$ENV:var_name` — resolves from environment variables (requires `enable_environment_variable_replacement` feature flag)

#### key_value_replace (JSONPath Replacement)

For replacing values in JSON/YAML files (Pipelines, Platform files):

```yaml
key_value_replace:
    - find_key: $.properties.activities[?(@.name=="Load_Data")].typeProperties.source.datasetSettings.externalReferences.connection
      replace_value:
          PPE: "ppe-connection-guid"
          PROD: "prod-connection-guid"
      item_type: "DataPipeline"
```

#### spark_pool (Environment Pool Mapping)

For parameterizing custom Spark pool attachments:

```yaml
spark_pool:
    - instance_pool_id: "dev-pool-guid"
      replace_value:
          PPE:
              type: "Capacity"
              name: "CapacityPool_Medium"
          PROD:
              type: "Capacity"
              name: "CapacityPool_Large"
      item_name: "my-environment"
```

#### Feature Flags

```python
from fabric_cicd import append_feature_flag
append_feature_flag("enable_lakehouse_unpublish")     # allow Lakehouse deletion
append_feature_flag("enable_shortcut_publish")         # deploy shortcuts with Lakehouse
append_feature_flag("enable_environment_variable_replacement")  # enable $ENV: vars
append_feature_flag("disable_workspace_folder_publish")  # skip workspace subfolder deploy
```

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

## Environment Items

### Capacity Pools vs. Workspace Pools

**Always attach Environment items to capacity pools when using custom Spark pools.**

- **Capacity pool** — referenced by a known, consistent GUID that exists across workspaces. Safe for source control.
- **Workspace pool** — referenced by a GUID tied to a specific workspace. When committed to source control, the GUID is meaningless outside that workspace.

Use consistent naming for capacity pools across environments (e.g., `CapacityPool_Medium`, `CapacityPool_Large`) to simplify parameterization.

### Autoscale Billing for Spark

For workloads with unpredictable or bursty Spark usage, **Autoscale Billing** is an alternative to fixed capacity SKUs:

| Approach | Best For | How It Works |
|----------|----------|-------------|
| **Fixed Capacity (F-SKU)** | Predictable, steady workloads | Pre-allocated vCores; pay fixed rate regardless of usage |
| **Autoscale Billing** | Bursty, unpredictable workloads | Allocate a small base SKU; Spark jobs scale beyond it and bill per-use (PAYG) |

**When to recommend Autoscale Billing:**
- Spark workloads vary significantly (e.g., 100 cores normally, 8,000+ cores during backfills)
- Development/test workspaces with intermittent heavy usage
- Teams that can't predict peak capacity needs upfront

**Configuration:** Assign a small F-SKU to the workspace, then enable [Autoscale Billing](https://learn.microsoft.com/fabric/data-engineering/configure-autoscale-billing) to allow Spark jobs to burst beyond the base capacity.

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

## Git Branching Strategy

### Option A: PPE-First (Recommended for Multi-Environment)

```
feature/my-work ──► ppe (default branch) ──► main (production)
                         │                        │
                    PPE workspace            PROD workspace
                    (deployed via CI/CD)     (deployed via CI/CD)
```

- PPE is the default branch — in-flight work never accidentally targets production
- Cherry-pick from PPE to main for production promotion
- Feature branches are connected to individual workspaces via Git Sync

### Option B: Main-First (Simpler)

```
feature/my-work ──► main (default branch)
                       │
                  Single workspace
                  (deployed via CI/CD or manual)
```

- Standard Git flow — simpler for single-environment projects
- Direct deployment from main branch

---

## Release Pipeline Examples

### Azure DevOps

```yaml
trigger:
  branches:
    include:
      - dev
      - main

stages:
  - stage: Deploy
    jobs:
      - job: Build
        pool:
          vmImage: windows-latest
        steps:
          - checkout: self
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '3.12'
          - script: pip install fabric-cicd
            displayName: 'Install fabric-cicd'
          - task: AzureCLI@2
            displayName: "Deploy Fabric Workspace"
            inputs:
              azureSubscription: "your-service-connection"
              scriptType: "ps"
              inlineScript: |
                python -u $(System.DefaultWorkingDirectory)/.deploy/fabric_workspace.py
```

### Deployment Script Example

```python
# .deploy/fabric_workspace.py
from fabric_cicd import FabricWorkspace, publish_all_items, unpublish_all_orphan_items

workspace = FabricWorkspace(
    workspace_id="your-workspace-id",
    environment="PPE",
    repository_directory="./workspace",
    item_type_in_scope=[
        "Lakehouse", "Warehouse", "Eventhouse",
        "Environment", "Notebook", "DataPipeline",
        "SemanticModel", "Report"
    ],
)

publish_all_items(workspace)
unpublish_all_orphan_items(workspace)
```

---

## Sources

- [Optimizing for CI/CD in Microsoft Fabric](https://blog.fabric.microsoft.com/en-US/blog/optimizing-for-ci-cd-in-microsoft-fabric) — Microsoft Azure Data team blog
- [fabric-cicd Documentation](https://microsoft.github.io/fabric-cicd/0.1.23/) — Official library docs
- [fabric-cicd GitHub](https://github.com/microsoft/fabric-cicd) — Source code and issues
