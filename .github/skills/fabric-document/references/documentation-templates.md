# Documentation Templates

Templates used by `/fabric-document` to generate project wiki documentation in `_projects/[workspace]/docs/`.

## Directory Structure

```
_projects/[workspace-name]/
├── docs/
│   ├── README.md              # Project overview with navigation
│   ├── decisions/
│   │   ├── 001-task-flow.md    # Why this task flow was chosen
│   │   ├── 002-storage.md     # Storage decision ADR
│   │   ├── 003-ingestion.md   # Ingestion decision ADR
│   │   ├── 004-processing.md  # Processing decision ADR
│   │   ├── 005-visualization.md # Visualization decision ADR
│   │   └── 006-cicd.md        # CI/CD & deployment strategy (optional — only when multi-env)
│   ├── architecture.md        # Visual diagram + item relationships
│   └── deployment-log.md      # What was deployed, issues, workarounds
└── deployments/
    ├── handoff.md             # Engineer's deployment handoff
    ├── deploy.sh / deploy.py  # Deployment script (bash or Python)
    ├── parameter.yml          # fabric-cicd parameterization (if used)
    ├── notebooks/             # Notebook source files
    └── queries/               # KQL and other query files
```

## 1. Project README (`docs/README.md`)

```markdown
# [Workspace Name] - Architecture Documentation

> Generated: [timestamp]
> Task flow: [task flow name]
> Status: [DEPLOYED | VALIDATED | PARTIAL]

## Overview

[2-3 sentence summary of what this project does and why it exists]

## Quick Links

| Document | Description |
|----------|-------------|
| [Architecture](architecture.md) | System diagram and item relationships |
| [Deployment Log](deployment-log.md) | What was deployed and how |
| [Deployments](../deployments/) | Scripts, notebooks, and queries |

### Decision Records

| ADR | Decision | Outcome |
|-----|----------|---------|
| [001-task-flow](decisions/001-task-flow.md) | Which task flow pattern? | [choice] |
| [002-storage](decisions/002-storage.md) | Storage layer | [choice] |
| ... | ... | ... |

## Architecture Diagram

```mermaid
[Generate from Architecture Handoff items and relationships]
```

## Validation Summary

| Phase | Status |
|-------|--------|
| Foundation | ✅/⚠️/❌ |
| ... | ... |

## Future Considerations

[Pull from Validation Report's Future Considerations section]
```

## 2. ADR Files (`docs/decisions/NNN-*.md`)

Use the template from `.github/skills/fabric-design/references/adr-template.md` for each decision:
- 001-task-flow.md - Why this task flow pattern
- 002-storage.md - Storage layer decision
- 003-ingestion.md - Ingestion approach
- 004-processing.md - Processing/transformation choice
- 005-visualization.md - Visualization layer (if applicable)
- 006-cicd.md - CI/CD & deployment strategy (if multi-environment)

## 3. Architecture Page (`docs/architecture.md`)

```markdown
# Architecture

## System Diagram

```mermaid
flowchart LR
    subgraph Ingestion
        [items]
    end
    subgraph Storage
        [items]
    end
    ...
```

## Items

| Item | Type | Purpose | Dependencies |
|------|------|---------|--------------|
| [from deployment] | [type] | [from architecture] | [relationships] |

## Data Flow

[Describe how data moves through the system]

## Deployment Strategy

| Aspect | Choice |
|--------|--------|
| Workspace approach | [Single / Multi-workspace — from Architect handoff] |
| Environments | [DEV, PPE, PROD — from Architect handoff] |
| CI/CD tool | fabric-cicd |
| Branching model | [PPE-first / Main-first / N/A] |

[If multi-environment: describe workspace naming, connection management, parameterization approach]

## Configuration Summary

[Pull Configuration Rationale from Engineer's handoff]
```

## 4. Deployment Log (`docs/deployment-log.md`)

```markdown
# Deployment Log

**Deployed:** [timestamp]
**Task flow:** [name]
**Validation Status:**[from Validation Report]

## Items Deployed

| Order | Item | Type | Status | Notes |
|-------|------|------|--------|-------|
| 1 | [name] | [type] | ✅ | [from Engineer] |

## Implementation Notes

[Pull from Engineer's Implementation Notes - deviations, workarounds, CLI commands]

## Configuration Rationale

[Pull Engineer's Configuration Rationale table]

## Manual Steps

### Completed
- [list from Engineer]

### Pending
- [list from Engineer]

## Issues & Resolutions

| Issue | Resolution | Status |
|-------|-----------|--------|
| [from Engineer/Tester] | [how resolved] | [fixed/open] |

## CI/CD Configuration

**Deployment Tool:** fabric-cicd
**Parameterization:** [parameter.yml / Variable Library / environment variables / none]

- parameter.yml location and key replacements configured
- Spark pool mappings applied
- Dynamic variables used ($workspace.id, $items references)

## Lessons Learned

[Pull from Validation Report's Future Considerations]
```
