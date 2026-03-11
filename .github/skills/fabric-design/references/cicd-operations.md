# CI/CD Operations Reference

Operational guides for Git branching, release pipelines, and deployment scripts. For architecture decisions (workspace strategy, parameterization), see [cicd-practices.md](cicd-practices.md).

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
