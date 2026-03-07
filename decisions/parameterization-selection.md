---
id: parameterization-selection
title: Parameterization Selection
description: Choose the right parameterization approach for multi-environment Fabric deployments
triggers:
  - "variable library vs parameter.yml"
  - "how to parameterize"
  - "multi-environment configuration"
  - "CI/CD variables"
  - "deployment stages"
options:
  - id: variable-library
    label: Variable Library
    criteria:
      tool: Fabric Portal / REST API / Git
      approach: Fabric-native workspace item
      value_types: ["String", "Integer", "Boolean", "Guid", "DateTime", "Item Reference"]
      best_for: ["Fabric-native CI/CD", "item reference binding", "teams using Fabric Git"]
      stage_management: Value sets — one active per workspace
      git_integration: JSON definition syncs via Fabric Git
  - id: parameter-yml
    label: parameter.yml (fabric-cicd)
    criteria:
      tool: fabric-cicd Python library
      approach: YAML file with per-environment overrides
      value_types: ["workspace names", "connection strings", "capacity pools", "item references"]
      best_for: ["automated pipelines", "Azure DevOps/GitHub Actions", "deployment-time substitution"]
      stage_management: Separate YAML sections per environment
      git_integration: YAML file in repo
  - id: environment-variables
    label: Environment Variables
    criteria:
      tool: Shell / Python scripts
      approach: OS-level environment variables in deployment scripts
      value_types: ["any string value"]
      best_for: ["simple projects", "single environment", "fab CLI scripts"]
      stage_management: Set vars before running script
      git_integration: Variables not in git (secrets stay out of repo)
quick_decision: |
  Single environment → Environment Variables (or skip)
  Multi-env + Fabric Git → Variable Library
  Multi-env + fabric-cicd → parameter.yml
  Multi-env + fab CLI → Environment Variables or Variable Library
---

# Parameterization Selection

> Choose the right approach for managing environment-specific configuration across Fabric deployment stages.

## Quick Decision Guide

```
How many deployment environments?
│
├─► Single environment ──────────► ENVIRONMENT VARIABLES (or skip parameterization)
│
└─► Multiple environments (Dev/PPE/Prod)
    │
    ├─► Using Fabric Git integration? ──► VARIABLE LIBRARY
    │
    ├─► Using fabric-cicd library? ──────► parameter.yml
    │
    └─► Using fab CLI scripts? ──────────► ENVIRONMENT VARIABLES or VARIABLE LIBRARY
```

## Comparison Table

| Criteria | Variable Library | parameter.yml | Environment Variables |
|----------|-----------------|---------------|----------------------|
| **Tool** | Fabric Portal / REST / Git | fabric-cicd Python library | Shell / Python |
| **Fabric-Native** | ✅ Yes — workspace item | ❌ External file | ❌ External |
| **Item References** | ✅ Workspace + Item ID pairs | ✅ Via replacement rules | ❌ Manual ID management |
| **Value Sets / Stages** | ✅ Built-in — one active per workspace | ✅ Per-environment YAML sections | ⚠️ Manual — set before each run |
| **Runtime Consumption** | ✅ NotebookUtils, Shortcuts, UDFs | ❌ Deploy-time only | ⚠️ Script-time only |
| **Git Integration** | ✅ JSON definition syncs | ✅ YAML in repo | ❌ Not in repo (by design) |
| **Supported Consumers** | Notebooks, Pipelines, Shortcuts, UDFs | Any Fabric item (at deploy time) | fab CLI scripts |
| **Max Complexity** | 1,000 variables × 1,000 value sets | Unlimited (file-based) | Unlimited (env-based) |
| **Learning Curve** | Low (portal UI) | Medium (YAML syntax + library) | Low (shell basics) |
| **Secrets Handling** | ⚠️ Not for secrets — values visible | ⚠️ Not for secrets in YAML | ✅ Secrets stay in env/vault |

## When to Choose Each

### Choose VARIABLE LIBRARY when:

- ✅ You're deploying to **multiple Fabric environments** (Dev, PPE, Prod)
- ✅ Items need **runtime references** to stage-specific resources (e.g., Notebook → different Lakehouse per stage)
- ✅ Your team uses **Fabric's built-in Git integration** for source control
- ✅ You want **one-click stage switching** — activate a value set and all consumers reconfigure
- ✅ You need **Item Reference** variables to dynamically bind Notebooks, Shortcuts, or User Data Functions

### Choose parameter.yml when:

- ✅ You're using the **`fabric-cicd` Python library** for automated deployment pipelines
- ✅ Parameterization must happen **at deployment time** (substituting values in item definitions before pushing to Fabric)
- ✅ You have **Azure DevOps or GitHub Actions** pipelines orchestrating deployments
- ✅ You need to parameterize **item definitions** (not just runtime references)

### Choose ENVIRONMENT VARIABLES when:

- ✅ **Single environment** project — parameterization is minimal
- ✅ You use **`fab` CLI scripts** and want to inject values at script execution time
- ✅ Project is simple enough that a formal parameterization tool is overkill
- ✅ You need to keep **secrets out of source control** (combine with Azure Key Vault or similar)

## Combining Approaches

Approaches are not mutually exclusive:

- **Variable Library + Environment Variables:** Use Variable Library for Fabric item references and value sets; use env vars for secrets (connection strings, API keys) that should not be stored in Fabric
- **Variable Library + parameter.yml:** Use Variable Library for runtime references; use parameter.yml for deployment-time substitutions in the fabric-cicd pipeline
- **Environment Variables + parameter.yml:** Common pattern — env vars hold secrets, parameter.yml holds non-secret configuration
