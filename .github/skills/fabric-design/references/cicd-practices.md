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

> Parameterization choice is resolved by `decision-resolver.py`. Variable Library must be in **Wave 1** (before consuming items).

**Limits:** Max 1,000 variables, 1,000 value sets, total cells < 10,000, item size < 1 MB.

**Git integration:** Variable Library definitions sync as JSON via Fabric's built-in Git.

### parameter.yml (fabric-cicd)

The `parameter.yml` file sits at the root of your repository directory and handles environment-specific value replacement. It supports three replacement modes:

- **`find_replace`** — String/regex replacement in text-based files (Notebooks, etc.)
- **`key_value_replace`** — JSONPath replacement in JSON/YAML files (Pipelines, Platform files)
- **`spark_pool`** — Spark pool attachment mapping per environment

**Dynamic variables available:** `$workspace.id`, `$items.Type.Name.id`, `$items.Type.Name.sqlendpoint`, `$ENV:var_name` (requires feature flag).

**Feature flags:** `enable_lakehouse_unpublish`, `enable_shortcut_publish`, `enable_environment_variable_replacement`, `disable_workspace_folder_publish` — enabled via `append_feature_flag()`.

> Full syntax examples and usage patterns: see [fabric-cicd docs](https://microsoft.github.io/fabric-cicd/0.1.23/).

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

## Git Branching & Release Pipelines

See [cicd-operations.md](cicd-operations.md) for Git branching strategies (PPE-First vs Main-First), Azure DevOps pipeline templates, and deployment script examples.

---

## Sources

- [Optimizing for CI/CD in Microsoft Fabric](https://blog.fabric.microsoft.com/en-US/blog/optimizing-for-ci-cd-in-microsoft-fabric) — Microsoft Azure Data team blog
- [fabric-cicd Documentation](https://microsoft.github.io/fabric-cicd/0.1.23/) — Official library docs
- [fabric-cicd GitHub](https://github.com/microsoft/fabric-cicd) — Source code and issues
