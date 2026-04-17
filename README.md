# Task Flows for Microsoft Fabric

[![CI](https://github.com/microsoft/fabric-task-flows/actions/workflows/ci.yml/badge.svg)](https://github.com/microsoft/fabric-task-flows/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**From problem to production in minutes. Less guessing. More building.**

<video src="https://github.com/microsoft/fabric-task-flows/raw/main/task-flows-video.mp4" controls width="100%"></video>

---

It starts the same way every time — a messy whiteboard and a simple question: *"What can we build?"*

But what if you didn't need to know Microsoft Fabric? What if you only needed to know what your business needs to solve?

With the `@fabric-advisor` agent, you describe the problem. After a few prompts, the whole solution is mapped, everything deployed, and everyone can see how the pieces connect — so you can start building, and stop guessing.

## Who is this for?

- **Teams with a problem to solve** — who don't have time to become platform experts first
- **Architects** who want pre-validated patterns instead of starting from scratch
- **Anyone new to Fabric** who needs opinionated guidance without the guesswork

## How it works

The agent walks you through seven pipeline phases that chain together automatically, with two moments where you stay in the driver's seat:

| Phase | What happens |
|-------|-------------|
| **Discover** | You describe your problem — the agent asks questions and recommends an architecture |
| **Design** | A detailed architecture, with decision records explaining every trade-off |
| **Test** | A test plan validates against your acceptance criteria |
| **Sign-Off** | 🛑 You review the architecture + test plan and either approve or request revisions (max 3 cycles) |
| **Deploy** | The agent generates dependency-ordered scripts, CI/CD-ready — you pick live deployment or artifacts-only |
| **Validate** | Post-deployment checks against the test plan, with a remediation loop for any findings |
| **Document** | Everything synthesizes into a human-readable brief |

## What you get

Each project produces **two deliverables** — one doc, one deployment:

```
_projects/your-project/
├── docs/project-brief.md     ← ONE human-readable doc (problem, architecture, decisions, validation)
└── deploy/                   ← CI/CD-ready deployment scripts
```

No sprawl — one project brief and the scripts to make it real.

## Quick start

**Prerequisites:** Python 3.11+, [GitHub Copilot](https://github.com/features/copilot) with agent mode

```bash
python _shared/scripts/run-pipeline.py start "My Project" --problem "describe your business problem"
```

The pipeline runner generates agent prompts — paste each into Copilot chat. Use `advance` and `next` to progress through phases. See [`_shared/workflow-guide.md`](_shared/workflow-guide.md) for the full pipeline reference.

## Copilot hooks (policy + observability)

This repository includes optional GitHub Copilot hooks in `.github/hooks/` to enforce pipeline guardrails and capture runtime audit events.

- `01-policy.json` — `preToolUse` policy checks (for example, blocks direct `pipeline-state.json` edits and destructive commands)
- `02-observability.json` — `sessionStart`, `userPromptSubmitted`, `postToolUse`, `errorOccurred`, `sessionEnd` logging
- Hook scripts live in `.github/hooks/scripts/`
- Runtime logs are written to `.github/hooks/logs/` (gitignored)

These hooks complement, but do not replace, CI checks in `.github/workflows/ci.yml`.

## What's inside

| Resource | Description |
|----------|-------------|
| [**13 Task Flows**](task-flows.md) | Pre-defined architectures for common scenarios — batch, streaming, hybrid, ML, API, governance, and more |
| [**7 Decision Guides**](decisions/_index.md) | Opinionated guidance on the choices that matter |
| [**Deployment Diagrams**](diagrams/_index.md) | Visual maps showing how pieces connect and deploy in order |
| [**Item Registry**](_shared/registry/item-type-registry.json) | 45 Fabric item types with API paths, CI/CD strategies, and deployment order |
| [**Templates**](_shared/templates/) | Definition files for every deployable Fabric item type |

## Repository structure

```
.github/agents/         → The @fabric-advisor orchestrator
.github/skills/         → Composable skills for each phase
decisions/              → Decision guides (the "why" behind each choice)
diagrams/               → Deployment diagrams (how pieces connect)
_shared/registry/       → Canonical registries the agent uses
_shared/templates/      → Starting point templates
_shared/lib/            → Shared Python modules
_shared/scripts/        → Pipeline CLI tools
_shared/tests/          → Test suite
_projects/              → Your project workspaces (gitignored)
```

## Contributing

We welcome contributions — especially to the **[Item Type Registry](_shared/registry/item-type-registry.json)**. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding task flows, decision guides, skills, and more.

## License

[MIT](LICENSE)
