# Task flows for Microsoft Fabric

[![CI](https://github.com/microsoft/fabric-task-flows/actions/workflows/ci.yml/badge.svg)](https://github.com/microsoft/fabric-task-flows/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Pre-defined architectures for [Microsoft Fabric](https://learn.microsoft.com/fabric/) — powered by an AI agent that guides you step by step.

Microsoft Fabric is powerful — but knowing which services to combine and how to wire them together takes time. `@fabric-advisor` asks the right questions about your business problem, picks the architecture, and hands you a fully deployable script. Zero to deployed in the cloud in minutes.

```
Describe Problem → Pick Architecture → ★ You Approve → Deploy
```

## Quick Start

**Prerequisites:** Python 3.11+, [GitHub Copilot](https://github.com/features/copilot) with agent mode

```bash
python _shared/scripts/run-pipeline.py start "My Project" --problem "describe your business problem"
```

The pipeline runner generates agent prompts — paste each into Copilot chat. Use `advance` and `next` to progress through phases. See [`_shared/workflow-guide.md`](_shared/workflow-guide.md) for the full pipeline reference.

## What's Inside

| Resource | Description |
|----------|-------------|
| [**13 Task flows**](task-flows.md) | Pre-defined architectures — batch, streaming, hybrid, ML, API, governance |
| [**7 Decision Guides**](decisions/_index.md) | Storage, ingestion, processing, visualization, skillset, parameterization, API |
| [**Deployment Diagrams**](diagrams/_index.md) | Dependency-ordered wave plans for each task flow |

### Skills

| Skill | Purpose | Status |
|-------|---------|--------|
| `/fabric-discover` | Understand your problem, recommend an architecture | ✅ Available |
| `/fabric-design` | Design your architecture with decision records | ✅ Available |
| `/fabric-deploy` | Generate deployment scripts via [`fabric-cicd`](https://pypi.org/project/fabric-cicd/) | ✅ Available |
| `/fabric-heal` | Improve pattern matching over time | ✅ Available |
| `/fabric-test` | Test plans and post-deployment validation | 🔜 Next release |
| `/fabric-document` | Wiki and ADR synthesis from pipeline handoffs | 🔜 Next release |

## Repository Structure

```
.github/agents/         → Orchestrator agent (@fabric-advisor)
.github/skills/         → Composable skills with pre-compute scripts
decisions/              → 7 decision guides (YAML frontmatter + decision trees)
diagrams/               → 13 deployment diagrams (dependency-ordered)
_shared/registry/       → Canonical JSON registries (item types, deployment order, skills)
_shared/lib/            → Shared Python modules
_shared/scripts/        → Pipeline CLI (run-pipeline, new-project, fleet-runner)
_shared/tests/          → Test suite
_projects/              → Per-project workspaces (gitignored)
```

## Item Type Registry

The **[Item Type Registry](_shared/registry/item-type-registry.json)** is the single source of truth for all Fabric item types — 25+ items with metadata including API paths, CI/CD deployment strategies, and wave ordering. This registry drives task flow diagrams, deployment scripts, and decision resolution.

## Contributing

We welcome contributions — especially to the **[Item Type Registry](_shared/registry/item-type-registry.json)**. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding task flows, decision guides, skills, and more.

## License

[MIT](LICENSE)
