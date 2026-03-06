# Copilot Instructions

## Project Overview

This is a **documentation-only** knowledge base — there is no source code, build system, or tests. All content is Markdown. The repo provides pre-defined Microsoft Fabric architectures via five custom Copilot agents that collaborate in phases:

```
Phase 0 — Discover:   @fabric-advisor (Discovery Brief)
                        │ automatic
Phase 1 — Design:     @fabric-architect (DRAFT) ──┬──► @fabric-engineer (Deployment Review)
                                                    └──► @fabric-tester (Testability Review)
                      @fabric-architect (incorporates feedback → FINAL Handoff)
                        │ automatic
Phase 2 — Plan+Approve+Deploy:
                      @fabric-tester (Test Plan)
                        │
                      ★ User Sign-Off (ONLY human gate)
                        │
                      @fabric-engineer (Deploy)
                        │ automatic
Phase 3 — Validate:    @fabric-tester (Validate against checklist)
                        │ automatic
Phase 4 — Document:    @fabric-documenter (ADRs + wiki)
```

## Architecture

### Content routing

All content is resolved by **task flow ID** (e.g., `medallion`, `lambda`, `event-analytics`). The 10 task flow IDs map to:

| Content | Path pattern |
|---------|-------------|
| Project index | `PROJECTS.md` (root-level dashboard) |
| Task flow overview | `task-flows.md` → H2 anchor (`## Medallion`) |
| Deployment diagram | `diagrams/{task-flow-id}.md` |
| Validation checklist | `validation/{task-flow-id}.md` |
| Project status | `projects/{workspace}/STATUS.md` |
| Project documentation | `projects/{workspace}/docs/` |
| Project deployments | `projects/{workspace}/deployments/` |

Decision guides live in `decisions/` and are shared across task flows. Shared reference content (legend, prerequisites, parallel deployment, CI/CD practices, deployment patterns, rollback protocol, validation patterns, documentation templates, workflow guide) lives in `_shared/`.

### Custom agents (`.github/agents/`)

| Agent | Role | Tools | Constraint |
|-------|------|-------|------------|
| `@fabric-advisor` | Discovers the problem, infers architectural signals, produces Discovery Brief | read, search | Read-only; never makes architecture decisions or deploys |
| `@fabric-architect` | Selects task flow, walks through decision guides, produces Architecture Handoff | read, search | Read-only; never deploys |
| `@fabric-tester` | Mode 0: reviews DRAFT architecture for testability; Mode 1: produces Test Plan; Mode 2: validates deployment | read, search, edit | Never modifies Fabric items; edit is for STATUS.md/PROJECTS.md updates |
| `@fabric-engineer` | Deploys Fabric items following diagrams and deployment order | read, edit, execute, search | Never makes architecture decisions |
| `@fabric-documenter` | Synthesizes all handoffs into wiki-style ADRs in `projects/[workspace]/docs/` | read, edit | Never deploys; documents only |

The agents exchange structured **handoff documents** (Discovery Brief → Architecture Handoff → Test Plan → Deployment Handoff → Validation Report → Wiki Documentation). See each agent file for the exact handoff template. The ADR template is in `_shared/adr-template.md`.

### Decision guides (`decisions/`)

Each guide uses **YAML frontmatter** with `id`, `title`, `description`, `triggers` (phrases that should route to this guide), and `options` (structured criteria for each choice). The body contains comparison tables, decision trees, and "when to use" guidance.

## Key Conventions

### Adding a new task flow

1. Add an H2 section to `task-flows.md` following the existing structure: description, task count, ASCII flow diagram, workloads, items, decision table with links, and diagram/validation links.
2. Create `diagrams/{task-flow-id}.md` with phased deployment flow using the symbols from `_shared/legend.md` (`[LC]`/`[CF]` skillset tags, `──►` flow, `OR` for choices).
3. Create `validation/{task-flow-id}.md` with a post-deployment manual steps table and a phase-by-phase checklist (Foundation → Environment → Ingestion → Transformation → Visualization → ML).

### Diagram conventions

Deployment diagrams use ASCII box-drawing characters with phased sections separated by `═════`. Skillset tags (`[LC]`, `[CF]`, `[LC/CF]`) annotate each item. Decision points use `OR` blocks with differentiator comparison tables.

### Deployment tooling

The Fabric CLI (`fab` via `pip install ms-fabric-cli`) is the preferred tool for deploying and verifying Fabric items. The `@fabric-engineer` agent uses `fab mkdir` to create items and `fab set` to configure them; the `@fabric-tester` agent uses `fab exists`, `fab ls`, and `fab get` for verification. See `_shared/fabric-cli-commands.md` for the full command reference and `_shared/prerequisites.md` for setup.

### Architecture vs. deployment details

The architect produces a **conceptual blueprint** — what items to create, which patterns to follow, and how data flows between components. Implementation details (connection GUIDs, source table schemas, credentials, gateway configuration) are collected by the `@fabric-engineer` at deployment time.

Acceptance criteria in the architecture handoff are categorized as:
- **Structural** — verifiable immediately after items are created (item exists, correct type, correct configuration)
- **Data Flow** — verifiable only after implementation details are in place (data lands, transformations run, queries return results)

Pre-deployment blockers are categorized as:
- **Architecture Blockers** — decisions that must be resolved before sign-off (capacity tier, workspace strategy)
- **Deployment Blockers** — infrastructure that must exist before the engineer deploys (connection GUIDs, gateway, credentials)

### Validation checklist structure

Every validation file starts with a "Post-Deployment Manual Steps" table (Item Type → Manual Action Required), followed by phased checklists using `- [ ]` checkboxes. Phases follow the standard order: Foundation, Environment, Ingestion, Transformation, Visualization, ML (if applicable).

### Deployment practices

Two deployment tools are supported: the Fabric CLI (`fab`) for interactive and ad-hoc deployments, and the `fabric-cicd` Python library (`pip install fabric-cicd`) for automated CI/CD pipelines. See `_shared/cicd-practices.md` for the full reference including parameterization with `parameter.yml`, per-item deployment gotchas, and release pipeline examples.

**Parallel deployment:** The `@fabric-engineer` agent analyzes the "Depends On" column in deployment order tables (`diagrams/[task-flow].md`) and groups items into dependency waves for concurrent execution. See `_shared/parallel-deployment.md` for the bash template.

**Workspace strategy is a user choice:** The architect presents single-workspace vs. multi-workspace options with trade-offs and lets the user decide. The engineer implements whichever strategy the architect's handoff specifies. Neither approach is the default.

**CI/CD is optional but well-supported:** Single-environment projects skip CI/CD checks. Multi-environment projects get full parameterization support, connection management guidance, and capacity pool configuration.

### Git workflow

When agents create or modify files in `projects/`:
- **Commit messages:** Use the format `[project-name] action description` (e.g., `[old-style] Add architecture handoff`, `[fraud-detection] Update deployment log`)
- **One project per commit:** Don't mix changes across different projects in a single commit
- **Never commit secrets:** Connection strings, workspace IDs, and credentials must use environment variables or parameter placeholders — never hardcoded values
