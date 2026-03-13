# Copilot Instructions

## Project Overview

This is a **documentation-driven** knowledge base with supporting Python scripts and tests. The repo provides pre-defined Microsoft Fabric architectures via one orchestrator agent (`@fabric-advisor`) that delegates to 6 composable skills:

```
Phase 0 — Discover:   @fabric-advisor (handles discovery directly)
                        │ automatic
Phase 1 — Design:     /fabric-design skill (produces FINAL architecture)
                        │ automatic
Phase 2 — Plan+Approve+Deploy:
                      /fabric-test skill (Review + Test Plan)
                        │
                      ★ User Sign-Off (ONLY human gate)
                        │
                      /fabric-deploy skill
                        │ automatic
Phase 3 — Validate:    /fabric-test skill (Validate)
                        (if issues → /fabric-deploy skill remediates)
                        │ automatic
Phase 4 — Document:    /fabric-document skill
```

## Architecture

### Content routing

All content is resolved by **task flow ID** (e.g., `medallion`, `lambda`). Key paths:

| Content | Path |
|---------|------|
| Task flow overview | `task-flows.md` → H2 anchor |
| Decision guides | `decisions/_index.md` → specific guide |
| Project PRDs | `_projects/{workspace}/prd/` |
| Project docs | `_projects/{workspace}/docs/` |

### Directory indexes

Read `_index.md` first, then fetch only the specific file needed. Decision guide YAML frontmatter contains a `quick_decision` field — resolve from frontmatter before reading the full body.

### Agent context efficiency

> **⚠️ Always use `-q` with `advance`** to suppress document echo.

> **⚠️ NEVER read raw JSON, diagram files, or decision guide bodies directly.** Use Python tools:
> - `decision-resolver.py` — resolves all 7 architectural decisions from signals
> - `diagram_parser.get_deployment_items(task_flow)` — deployment order
> - `registry_loader.build_*()` — item type metadata
> - `test-plan-prefill.py` — registry data for test planning
> - `validate-items.py` — validation checklists
> - `signal-mapper.py` — signal category mapping
>
> Only read a decision guide body when `decision-resolver.py` returns `confidence: ambiguous`.

### Orchestrator agent (`.github/agents/`)

| Agent | Role | Tools | Constraint |
|-------|------|-------|------------|
| `@fabric-advisor` | Orchestrates the full pipeline. Handles discovery directly, delegates all other phases to skills | read, search, edit, execute | Never makes architecture decisions or deploys; delegates via skills |

### Skills (`.github/skills/`)

Skills are composable, auto-activating instruction packs that do the actual work. Each skill has a `SKILL.md` with trigger phrases, bundled references, and focused single-workflow instructions.

| Skill | Phase | Constraint |
|-------|-------|------------|
| `/fabric-discover` | 0a | Never decides task flow |
| `/fabric-design` | 1a–1c | Never deploys |
| `/fabric-test` | 2a, 3 | Never invents ACs |
| `/fabric-deploy` | 2c, 3+ | Never makes architecture decisions |
| `/fabric-document` | 4 | Documents only |
| `/fabric-heal` | Standalone | Never modifies matching algorithm |

Skills exchange structured **handoff documents**. See each skill's `SKILL.md` for instructions and `_shared/workflow-guide.md` for the full pipeline.

## Parallel Execution Principle

> **⚠️ MUST parallelize independent work.** When multiple files, tool calls, or sub-tasks have no data dependency on each other, agents MUST execute them in a single parallel batch — never sequentially. This applies to:
>
> - **File writes** — e.g., ADRs 001-005, wiki docs, deployment scripts
> - **File reads** — e.g., reading discovery brief + deployment order + decision guides
> - **Tool calls** — e.g., running signal mapper + reading templates simultaneously
> - **Validation checks** — e.g., verifying multiple deployed items at once
>
> **Rule of thumb:** If task B does not depend on the _output_ of task A, they MUST run in parallel. Sequential execution of independent work wastes tokens and time.

## Key Conventions

> For contributor guidelines, see [CONTRIBUTING.md](../CONTRIBUTING.md).

### Deployment tooling

> **⚠️ `fabric-cicd` is the ONLY deployment dependency.** Do NOT introduce `ms-fabric-cli` or other CLI tools.

### Architecture vs. deployment details

- **Architect** = conceptual blueprint. **Engineer** = implementation details at deploy time.
- **Structural ACs** = verifiable after item creation. **Data Flow ACs** = verifiable after connections configured.

### Deployment practices

- **Deployment + CI/CD:** `fabric-cicd` library — see deploy skill's `references/prerequisites.md` and design skill's `references/cicd-practices.md`
- **Validation:** `validate-items.py` (REST API)
- **Parameterization:** Variable Library (preferred) — see `decisions/parameterization-selection.md`
- **Deployment order:** `diagram_parser.get_deployment_items()` — see deploy skill's `references/parallel-deployment.md`
