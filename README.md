# Task Flows for Microsoft Fabric

[![CI](https://github.com/microsoft/fabric-task-flows/actions/workflows/ci.yml/badge.svg)](https://github.com/microsoft/fabric-task-flows/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Pre-defined architectures for [Microsoft Fabric](https://learn.microsoft.com/fabric/) — powered by one AI orchestrator agent and six composable skills.

Describe your data problem, and `@fabric-advisor` walks you through discovery, architecture design, testing, deployment, and documentation — with a single human approval gate. Everything else is automated.

```
Discover → Design (DRAFT → Review → FINAL) → Test Plan → ★ You Approve → Deploy → Validate → Document
```

## Quick Start

**Prerequisites:** Python 3.11+, [GitHub Copilot](https://github.com/features/copilot) with agent mode

```bash
python _shared/scripts/run-pipeline.py start "My Project" --problem "describe your data problem"
```

The pipeline runner generates agent prompts — paste each into Copilot chat. Use `advance` and `next` to progress through phases. The only human gate is architecture + test plan sign-off (Phase 2b, via `--approve`).

> See [`_shared/workflow-guide.md`](_shared/workflow-guide.md) for the full pipeline reference.

## Task Flows

13 pre-defined architectures covering common Fabric patterns:

| Task Flow | Pattern | Best For |
|-----------|---------|----------|
| `basic-data-analytics` | Batch | Simple analytics — Warehouse → Semantic Model → Report |
| `medallion` | Batch | Progressive data quality (Bronze → Silver → Gold) |
| `lambda` | Hybrid | Combined batch + real-time paths |
| `event-analytics` | Streaming | Real-time IoT / logs with Eventhouse |
| `event-medallion` | Streaming | Streaming with medallion layers |
| `data-analytics-sql-endpoint` | Batch | Lakehouse with SQL analytics endpoint |
| `basic-machine-learning-models` | Batch | ML training, experiment tracking, prediction |
| `sensitive-data-insights` | Batch | RLS / OLS / CLS for compliant processing |
| `translytical` | Transactional | Operational BI with SQL Database writeback |
| `app-backend` | API | Application APIs via SQL Database / Cosmos DB |
| `conversational-analytics` | AI | Self-service analytics via Data Agents |
| `semantic-governance` | Governance | Enterprise vocabulary and knowledge graph |
| `general` | All | Comprehensive reference architecture |

Each task flow includes a deployment diagram (`diagrams/`), item inventory, and dependency-ordered wave plan. See [`task-flows.md`](task-flows.md) for full decision tables and diagram links.

## Decision Guides

Seven structured guides to help choose the right Fabric components:

| Guide | Question It Answers |
|-------|-------------------|
| [Storage](decisions/storage-selection.md) | Lakehouse, Warehouse, Eventhouse, SQL Database, or Cosmos DB? |
| [Ingestion](decisions/ingestion-selection.md) | Copy Job, Dataflow Gen2, Pipeline, Eventstream, or Mirroring? |
| [Processing](decisions/processing-selection.md) | Notebook, Spark Job Definition, Dataflow Gen2, or KQL? |
| [Visualization](decisions/visualization-selection.md) | Report, Dashboard, Real-Time Dashboard, or Data Agent? |
| [Skillset](decisions/skillset-selection.md) | Code-First or Low-Code team? |
| [Parameterization](decisions/parameterization-selection.md) | Variable Library, parameter.yml, or Environment Variables? |
| [API](decisions/api-selection.md) | GraphQL API, User Data Functions, or Direct Connection? |

Each guide includes YAML frontmatter, a quick-decision tree, comparison tables, and "Choose when" guidance.

## Skills

One orchestrator (`@fabric-advisor`) delegates to six composable skills that activate automatically via [GitHub Copilot agent mode](https://docs.github.com/copilot/using-github-copilot/using-copilot-coding-agent):

| Skill | Phase | Purpose |
|-------|-------|---------|
| `/fabric-discover` | Discovery | Infer signals from problem statements, suggest task flows |
| `/fabric-design` | Design | DRAFT → Review → FINAL architecture with ADRs |
| `/fabric-test` | Test & Validate | Create test plans, validate post-deployment |
| `/fabric-deploy` | Deploy | Wave-based deployment via [`fabric-cicd`](https://pypi.org/project/fabric-cicd/) |
| `/fabric-document` | Document | Wiki and ADR synthesis from pipeline handoffs |
| `/fabric-heal` | Maintenance | Self-healing signal mapper with keyword patching |

Skills are composable instruction packs in `.github/skills/`, each with trigger phrases, bundled references, and deterministic pre-compute scripts.

## Item Type Registry

The **[Item Type Registry](_shared/registry/item-type-registry.json)** is the single source of truth for all Fabric item types used across the project — 25+ item types with metadata including:

- **Skillset tags** — Code-First `[CF]` vs Low-Code `[LC]`
- **API paths and aliases** — for programmatic access and CLI tooling
- **CI/CD strategy** — deployment file patterns and `fabric-cicd` compatibility
- **Phase ordering** — canonical deployment wave positions

This registry drives task flow diagrams, deployment scripts, and validation checks. **Contributions and corrections are welcome** — if you spot a missing item type, an incorrect API path, or a new Fabric capability, this is the best place to start.

## Repository Structure

```
.github/agents/         → Orchestrator agent (@fabric-advisor)
.github/skills/         → 6 composable skills with pre-compute scripts
decisions/              → 7 decision guides (YAML frontmatter + decision trees)
diagrams/               → 13 deployment diagrams (ASCII, dependency-ordered)
_shared/registry/       → Canonical JSON registries (item types, deployment order, skills)
_shared/lib/            → Shared Python modules
_shared/scripts/        → Pipeline CLI tools (run-pipeline, new-project, fleet-runner)
_shared/tests/          → Test suite
_projects/              → Per-project workspaces (gitignored)
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full directory tree, conventions, and how to add task flows, decision guides, or skills.

## Contributing

We welcome contributions! Whether it's correcting item type metadata, adding a new task flow, improving decision guides, or fixing bugs in scripts — see [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

The **Item Type Registry** (`_shared/registry/item-type-registry.json`) is an especially good entry point for first contributions.

## License

[MIT](LICENSE)
