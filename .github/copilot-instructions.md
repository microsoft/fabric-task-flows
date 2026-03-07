# Copilot Instructions

## Project Overview

This is a **documentation-only** knowledge base — there is no source code, build system, or tests. All content is Markdown. The repo provides pre-defined Microsoft Fabric architectures via six custom Copilot agents that collaborate in phases:

```
Phase 0 — Discover:   @fabric-advisor (Discovery Brief)
                        │ automatic
Phase 1 — Design:     @fabric-architect (DRAFT) ──► @fabric-reviewer (Combined Review)
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

All content is resolved by **task flow ID** (e.g., `medallion`, `lambda`, `event-analytics`). The 11 task flow IDs map to:

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

### Directory indexes

Each content directory has an `_index.md` routing table that agents should read first:

| Directory | Index | Purpose |
|-----------|-------|---------|
| `decisions/` | `decisions/_index.md` | Find decision guides by ID; use `quick_decision` in YAML frontmatter for fast resolution |
| `diagrams/` | `diagrams/_index.md` | Find deployment diagram by task flow; includes item/wave counts |
| `validation/` | `validation/_index.md` | Find validation checklist by task flow; includes phase names |

**Agent context loading rule:** Read the `_index.md` first, then fetch only the specific file needed. Do not scan entire directories. Decision guide YAML frontmatter contains a `quick_decision` field with a compact decision tree — resolve from frontmatter before reading the full guide body.

**Diagram skip markers:** Diagram files contain `<!-- AGENT: Skip to "## Deployment Order" -->` markers. Agents should jump past the ASCII visual diagram to the structured deployment order table.

### Project scaffolding

New projects are scaffolded via `python scripts/run-pipeline.py start "Project Name" --problem "description"`, which calls `new-project.py` internally to create all directories and template files, then initializes `pipeline-state.json` for phase tracking. Agents edit pre-existing files — they do not create directories or boilerplate. See `_shared/workflow-guide.md` for details.

### Custom agents (`.github/agents/`)

| Agent | Role | Tools | Constraint |
|-------|------|-------|------------|
| `@fabric-advisor` | Discovers the problem, infers architectural signals, produces Discovery Brief | read, search, edit, execute | Read-only analysis; never makes architecture decisions or deploys |
| `@fabric-architect` | Selects task flow, walks through decision guides, produces Architecture Handoff | read, search, edit | Never deploys |
| `@fabric-tester` | Mode 0: reviews DRAFT architecture for testability; Mode 1: produces Test Plan; Mode 2: validates deployment | read, search, edit, execute | Never modifies Fabric items; edit is for STATUS.md/PROJECTS.md updates |
| `@fabric-reviewer` | Combined engineer + tester DRAFT review in a single pass (replaces parallel Mode 0 calls) | read, search, edit | Review only; never deploys or makes architecture decisions |
| `@fabric-engineer` | Deploys Fabric items following diagrams and deployment order | read, edit, execute, search | Never makes architecture decisions |
| `@fabric-documenter` | Synthesizes all handoffs into wiki-style ADRs in `projects/[workspace]/docs/` | read, edit | Never deploys; documents only |
| `@fabric-healer` | Self-healing signal mapper — generates diverse problem statements (LLM), benchmarks against signal mapper (scripts), patches keyword gaps | read, search, edit, execute | Never modifies matching algorithm; only expands keyword tuples; standalone workflow via `heal-orchestrator.py` |

The agents exchange structured **handoff documents** (Discovery Brief → Architecture Handoff → Test Plan → Deployment Handoff → Validation Report → Wiki Documentation). See each agent file for the exact handoff template. The ADR template is in `_shared/adr-template.md`.

### Decision guides (`decisions/`)

Each guide uses **YAML frontmatter** with `id`, `title`, `description`, `triggers` (phrases that should route to this guide), and `options` (structured criteria for each choice). The body contains comparison tables, decision trees, and "when to use" guidance.

## Key Conventions

> For contributor guidelines (adding task flows, diagram conventions, git workflow), see [CONTRIBUTING.md](../CONTRIBUTING.md).

### Deployment tooling

The Fabric CLI (`fab` via `pip install ms-fabric-cli`) is the preferred tool for deploying and verifying Fabric items. The `@fabric-engineer` agent uses `fab mkdir` to create items and `fab set` to configure them; the `@fabric-tester` agent uses `fab exists`, `fab ls`, and `fab get` for verification. See `_shared/fabric-cli-commands.md` for the full command reference and `_shared/prerequisites.md` for setup.

### Architecture vs. deployment details

- **Architect** produces the conceptual blueprint (items, patterns, data flow). **Engineer** collects implementation details (connection GUIDs, credentials) at deploy time.
- **Structural ACs** = verifiable after item creation. **Data Flow ACs** = verifiable after connections/data are configured.
- **Architecture Blockers** = block sign-off. **Deployment Blockers** = block engineer only.

### Deployment practices

- **CLI:** `fab` (preferred) — see `_shared/fabric-cli-commands.md`
- **CI/CD:** `fabric-cicd` library — see `_shared/cicd-practices.md`
- **Parameterization:** Variable Library (preferred), parameter.yml, or env vars — see `decisions/parameterization-selection.md`
- **Parallel deployment:** Waves from `diagrams/[task-flow].md` — see `_shared/parallel-deployment.md`
