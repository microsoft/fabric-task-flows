# Documentation Templates

Templates used by `/fabric-document` to generate a single project brief in `_projects/[workspace]/docs/`.

## Directory Structure

```
_projects/[workspace-name]/
├── docs/
│   └── project-brief.md          # ONE human-readable deliverable
└── deploy/
    ├── deploy-[name].py           # Deployment script
    ├── config.yml                 # Deployment config
    ├── workspace/                 # Fabric item definitions
    └── taskflow-[name].json       # Task flow import file
```

> **Pipeline-internal files** (architecture-handoff.md, deployment-handoff.md, test-plan.md,
> validation-report.md, pipeline-state.json) are consumed by pipeline scripts only.
> They are NOT documentation — do NOT duplicate their content into separate human-facing files.

## Project Brief (`docs/project-brief.md`)

The single human deliverable. A CTO reads it in 10 minutes.

```markdown
# [Project Name]

> [Task flow] architecture on Microsoft Fabric | [Date] | [Status: VALIDATED ✅ / DEPLOYED / PARTIAL]

## The Problem

[2-3 sentences from discovery brief — what business problem are we solving and why now?]

## What We Built

[Architecture diagram — ASCII or Mermaid showing data flow from sources through storage,
processing, and visualization layers]

### Fabric Items ([count] items, [wave count] deployment waves)

| Wave | Items | Purpose |
|------|-------|---------|
| 1: Foundation | Lakehouse, Warehouse, Eventhouse | Storage layers |
| 2: Compute | Environment, Variable Library | Spark runtime, config |
| ... | ... | ... |

## Why This Architecture

### Task Flow: [name]

[1-2 sentences: why this pattern over alternatives]

| Alternative | Why Not |
|-------------|---------|
| [other flow] | [1 sentence] |

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Storage | [choice] | [1 sentence why] |
| Ingestion | [choice] | [1 sentence why] |
| Processing | [choice] | [1 sentence why] |
| Visualization | [choice] | [1 sentence why] |
| CI/CD | [choice] | [1 sentence why] |

## How to Deploy

**Tool:** fabric-cicd
**Environments:** [Dev / Test / Prod]
**Script:** `deploy/deploy-[name].py`

### Manual Steps (Post-Deploy)

| Step | Item | Action | Blocked By |
|------|------|--------|------------|
| M-1 | [item] | [action] | [dependency] |

### Configuration

| Item | Setting | Why |
|------|---------|-----|
| [item] | [setting] | [≤10 words] |

## Validation Summary

| Check | Result |
|-------|--------|
| All [N] items deployed | ✅ |
| Smoke tests passed | ✅ |
| Config checklist confirmed | ✅ |

### Edge Cases Tested

- [edge case 1]
- [edge case 2]

## What's Next

- [Future consideration 1]
- [Future consideration 2]
```

## Rules

1. **ONE file.** Do not create README.md, architecture.md, deployment-log.md, or separate ADR files.
2. **No duplication.** Every fact appears exactly once. If it's in the items table, don't repeat it in prose.
3. **Decisions inline.** Architecture decisions go in the "Key Decisions" table — not separate files.
4. **~1,500 words max.** If you need more, you're duplicating something.
5. **Pull from pipeline files.** Read architecture-handoff.md, deployment-handoff.md, test-plan.md, validation-report.md, discovery-brief.md — synthesize, don't copy.

