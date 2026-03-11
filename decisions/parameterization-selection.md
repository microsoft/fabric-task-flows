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
      best_for: ["simple projects", "single environment", "deploy scripts"]
      stage_management: Set vars before running script
      git_integration: Variables not in git (secrets stay out of repo)
quick_decision: |
  Single environment → Environment Variables (or skip)
  Multi-env + Fabric Git → Variable Library
  Multi-env + fabric-cicd → parameter.yml
  Multi-env + deploy scripts → Environment Variables or Variable Library
---

# Parameterization Selection

> Choose the right approach for managing environment-specific configuration across Fabric deployment stages.

## Comparison Table

| Criteria | Variable Library | parameter.yml | Environment Variables |
|----------|-----------------|---------------|----------------------|
| **Tool** | Fabric Portal / REST / Git | fabric-cicd Python library | Shell / Python |
| **Fabric-Native** | ✅ Yes — workspace item | ❌ External file | ❌ External |
| **Item References** | ✅ Workspace + Item ID pairs | ✅ Via replacement rules | ❌ Manual ID management |
| **Value Sets / Stages** | ✅ Built-in — one active per workspace | ✅ Per-environment YAML sections | ⚠️ Manual — set before each run |
| **Runtime Consumption** | ✅ NotebookUtils, Shortcuts, UDFs | ❌ Deploy-time only | ⚠️ Script-time only |
| **Git Integration** | ✅ JSON definition syncs | ✅ YAML in repo | ❌ Not in repo (by design) |
| **Supported Consumers** | Notebooks, Pipelines, Shortcuts, UDFs | Any Fabric item (at deploy time) | Deploy scripts |
| **Max Complexity** | 1,000 variables × 1,000 value sets | Unlimited (file-based) | Unlimited (env-based) |
| **Learning Curve** | Low (portal UI) | Medium (YAML syntax + library) | Low (shell basics) |
| **Secrets Handling** | ⚠️ Not for secrets — values visible | ⚠️ Not for secrets in YAML | ✅ Secrets stay in env/vault |

## Combining Approaches

Approaches are not mutually exclusive:

- **Variable Library + Environment Variables:** Use Variable Library for Fabric item references and value sets; use env vars for secrets (connection strings, API keys) that should not be stored in Fabric
- **Variable Library + parameter.yml:** Use Variable Library for runtime references; use parameter.yml for deployment-time substitutions in the fabric-cicd pipeline
- **Environment Variables + parameter.yml:** Common pattern — env vars hold secrets, parameter.yml holds non-secret configuration
