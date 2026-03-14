---
id: parameterization-selection
title: Parameterization Selection
---

# Parameterization Selection

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

| Combination | Use Case |
|-------------|----------|
| **Variable Library + Env Vars** | Library for item references/value sets; env vars for secrets |
| **Variable Library + parameter.yml** | Library for runtime refs; YAML for deploy-time substitutions |
| **Env Vars + parameter.yml** | Env vars for secrets; YAML for non-secret config |
