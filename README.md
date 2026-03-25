# Task Flows for Microsoft Fabric

[![CI](https://github.com/microsoft/fabric-task-flows/actions/workflows/ci.yml/badge.svg)](https://github.com/microsoft/fabric-task-flows/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**You describe your business problem. The agent picks the architecture, wires the services, and deploys it — all inside [Microsoft Fabric](https://learn.microsoft.com/fabric/).**

---

Fabric gives you a warehouse, a lakehouse, notebooks, pipelines, real-time streams, semantic models, and dozens more services — but knowing *which* to combine and *how* to wire them together is the hard part. That's what Task Flows solves.

`@fabric-advisor` is an AI agent that walks you through the entire journey:

```
You describe the problem  →  Agent recommends architecture  →  ★ You approve  →  Agent deploys  →  One brief
```

Zero to deployed in minutes. No guesswork, no YAML wrestling, no wiki sprawl.

## Who is this for?

- **Data engineers** who want a faster path from "we need analytics" to deployed infrastructure
- **Architects** who want pre-validated patterns instead of starting from scratch
- **Teams new to Fabric** who need opinionated guidance on which services to use

## How it works

The agent operates through **six skills** that chain together automatically:

| Skill | What it does for you |
|-------|---------------------|
| **Discover** | Asks about your problem, data sources, and team skills — recommends candidate architectures |
| **Design** | Produces a detailed architecture with decision records for every trade-off |
| **Test** | Creates a test plan from your acceptance criteria and validates the deployment |
| **Deploy** | Generates dependency-ordered deployment scripts via [`fabric-cicd`](https://pypi.org/project/fabric-cicd/) |
| **Document** | Synthesizes everything into one brief a CTO can read in 10 minutes |
| **Heal** | Improves the signal mapper over time so recommendations get sharper |

## What you get

Each project produces **two deliverables** — one doc, one deployment:

```
_projects/your-project/
├── docs/project-brief.md     ← ONE human-readable doc (problem, architecture, decisions, validation)
└── deploy/                   ← Deployable scripts (fabric-cicd, .platform files, config)
```

No 17-file documentation explosion. One brief plus the scripts to make it real.

## Quick start

**Prerequisites:** Python 3.11+, [GitHub Copilot](https://github.com/features/copilot) with agent mode

```bash
python _shared/scripts/run-pipeline.py start "My Project" --problem "describe your business problem"
```

The pipeline runner generates agent prompts — paste each into Copilot chat. Use `advance` and `next` to progress through phases. See [`_shared/workflow-guide.md`](_shared/workflow-guide.md) for the full pipeline reference.

## What's inside

| Resource | Description |
|----------|-------------|
| [**13 Task Flows**](task-flows.md) | Pre-defined architectures — batch, streaming, hybrid, ML, API, governance |
| [**7 Decision Guides**](decisions/_index.md) | Storage, ingestion, processing, visualization, skillset, parameterization, API |
| [**Deployment Diagrams**](diagrams/_index.md) | Dependency-ordered wave plans for each task flow |
| [**45 Item Types**](_shared/registry/item-type-registry.json) | Full Fabric item registry — API paths, CI/CD strategies, and wave ordering |
| [**Item Templates**](_shared/templates/) | Empty-state definition files for every deployable Fabric item ([source](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/item-definition-overview)) |

## Repository structure

```
.github/agents/         → Orchestrator agent (@fabric-advisor)
.github/skills/         → Composable skills with pre-compute scripts
decisions/              → 7 decision guides (YAML frontmatter + decision trees)
diagrams/               → 13 deployment diagrams (dependency-ordered)
_shared/registry/       → Canonical JSON registries (item types, deployment order, skills)
_shared/templates/      → Empty-state item definition files (source of truth for fabric-cicd)
_shared/lib/            → Shared Python modules
_shared/scripts/        → Pipeline CLI (run-pipeline, new-project, fleet-runner)
_shared/tests/          → Test suite (838 tests)
_projects/              → Per-project workspaces (gitignored)
```

## Contributing

We welcome contributions — especially to the **[Item Type Registry](_shared/registry/item-type-registry.json)**. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding task flows, decision guides, skills, and more.

## License

[MIT](LICENSE)
