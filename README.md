# Task Flows for Microsoft Fabric

[![CI](https://github.com/microsoft/fabric-task-flows/actions/workflows/ci.yml/badge.svg)](https://github.com/microsoft/fabric-task-flows/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Pre-defined architectures for [Microsoft Fabric](https://learn.microsoft.com/fabric/) — powered by one AI orchestrator agent and six composable skills.

Describe your data problem, and `@fabric-advisor` walks you through discovery, architecture design, testing, deployment, and documentation — with a single human approval gate.

```
Discover → Design (DRAFT → Review → FINAL) → Test Plan → ★ You Approve → Deploy → Validate → Document
```

## Item Type Registry

The **[Item Type Registry](_shared/registry/item-type-registry.json)** is the single source of truth for all Fabric item types — 25+ items with metadata including skillset tags (Code-First / Low-Code), API paths, CI/CD deployment strategies, and wave ordering.

This registry drives everything in the project: task flow diagrams, deployment scripts, validation checks, and decision resolution. **Contributions and corrections are especially welcome here** — missing item types, incorrect API paths, new Fabric capabilities.

## Quick Start

**Prerequisites:** Python 3.11+, [GitHub Copilot](https://github.com/features/copilot) with agent mode

```bash
python _shared/scripts/run-pipeline.py start "My Project" --problem "describe your data problem"
```

The pipeline runner generates agent prompts — paste each into Copilot chat. Use `advance` and `next` to progress through phases. See [`_shared/workflow-guide.md`](_shared/workflow-guide.md) for the full pipeline reference.

## What's Inside

| Resource | Description |
|----------|-------------|
| [**13 Task Flows**](task-flows.md) | Pre-defined architectures — batch, streaming, hybrid, ML, API, governance |
| [**7 Decision Guides**](decisions/_index.md) | Storage, ingestion, processing, visualization, skillset, parameterization, API |
| [**Deployment Diagrams**](diagrams/_index.md) | Dependency-ordered wave plans for each task flow |
| [**6 Skills**](.github/skills/) | Composable agents — discover, design, test, deploy, document, heal |

## Repository Structure

```
.github/agents/         → Orchestrator agent (@fabric-advisor)
.github/skills/         → 6 composable skills with pre-compute scripts
decisions/              → 7 decision guides (YAML frontmatter + decision trees)
diagrams/               → 13 deployment diagrams (dependency-ordered)
_shared/registry/       → Canonical JSON registries (item types, deployment order, skills)
_shared/lib/            → Shared Python modules
_shared/scripts/        → Pipeline CLI (run-pipeline, new-project, fleet-runner)
_shared/tests/          → Test suite
_projects/              → Per-project workspaces (gitignored)
```

## Contributing

We welcome contributions — especially to the **[Item Type Registry](_shared/registry/item-type-registry.json)**. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding task flows, decision guides, skills, and more.

## License

[MIT](LICENSE)
