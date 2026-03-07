# Copilot Instructions

## Project Overview

This is a **documentation-only** knowledge base — there is no source code, build system, or tests. All content is Markdown. The repo provides pre-defined Microsoft Fabric architectures via one orchestrator agent (`@fabric-advisor`) that delegates to 10 composable skills:

```
Phase 0 — Discover:   @fabric-advisor + /fabric-discover skill
                        │ automatic
Phase 1 — Design:     /fabric-design skill (DRAFT) ──► /fabric-review skill
                      /fabric-finalize skill (incorporates feedback → FINAL)
                        │ automatic
Phase 2 — Plan+Approve+Deploy:
                      /fabric-test-plan skill
                        │
                      ★ User Sign-Off (ONLY human gate)
                        │
                      /fabric-deploy skill
                        │ automatic
Phase 3 — Validate:    /fabric-validate skill
                        (if issues → /fabric-remediate skill)
                        │ automatic
Phase 4 — Document:    /fabric-document skill
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

### Orchestrator agent (`.github/agents/`)

| Agent | Role | Tools | Constraint |
|-------|------|-------|------------|
| `@fabric-advisor` | Orchestrates the full pipeline. Handles discovery directly, delegates all other phases to skills | read, search, edit, execute | Never makes architecture decisions or deploys; delegates via skills |

### Skills (`.github/skills/`)

Skills are composable, auto-activating instruction packs that do the actual work. Each skill has a `SKILL.md` with trigger phrases, bundled references, and focused single-workflow instructions.

| Skill | Phase | Purpose | Constraint |
|-------|-------|---------|------------|
| `/fabric-discover` | 0a | Signal inference from problem statements | Read-only analysis; never decides task flow |
| `/fabric-design` | 1a | DRAFT Architecture Handoff (task flow + decisions) | Never deploys |
| `/fabric-finalize` | 1c | Incorporates review feedback → FINAL | No new design decisions |
| `/fabric-review` | 1b | Combined feasibility + testability review | Review only; never redesigns |
| `/fabric-test-plan` | 2a | Maps acceptance criteria to validation checks | Never invents ACs |
| `/fabric-deploy` | 2c | Wave-based deployment via `fab` CLI | Never makes architecture decisions |
| `/fabric-validate` | 3 | Post-deployment validation against test plan | Never modifies Fabric items |
| `/fabric-remediate` | 3+ | Fixes deployment/config issues from validation | Escalates design issues |
| `/fabric-document` | 4 | Wiki + ADR synthesis from handoffs | Documents only |
| `/fabric-heal` | Standalone | Self-healing signal mapper (problem generation + keyword patching) | Never modifies matching algorithm |

Skills exchange structured **handoff documents** (Discovery Brief → Architecture Handoff → Test Plan → Deployment Handoff → Validation Report → Wiki Documentation). See each skill's `SKILL.md` for instructions. The ADR template is in `_shared/adr-template.md`.

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
