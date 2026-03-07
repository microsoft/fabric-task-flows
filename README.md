# Task Flows

> Technical architecture guidance for Microsoft Fabric projects.

A documentation-only knowledge base of pre-defined architectures, decision guides, and deployment validation for Microsoft Fabric. Six GitHub Copilot custom agents collaborate in phases — from problem discovery through deployment and documentation:

```
@fabric-advisor ──► @fabric-architect (DRAFT) ──► @fabric-reviewer (Review)
──► @fabric-architect (FINAL) ──► @fabric-tester (Test Plan) ──► ★ YOU (Sign-Off)
──► @fabric-engineer (Deploy) ──► @fabric-tester (Validate) ──► @fabric-documenter (ADRs)
```

## 🚀 Quick Start

1. **Start a project** — run `python scripts/run-pipeline.py start "Your Project Name" --problem "describe your problem"`
2. **Follow the prompts** — the runner generates agent prompts; paste each into chat. Use `advance` + `next` to progress.
3. **Review & approve** — the only human gate is Phase 2b (architecture + test plan sign-off, via `--approve`)
4. **Everything else is automatic** — design, review, deploy, validate, document

> ⚠️ **Always use `run-pipeline.py`** to start projects and advance phases. Do not call `new-project.py` directly or manually chain agents. See `_shared/workflow-guide.md` for details.

## 📋 Task Flows

| ID | Pattern | Description |
|----|---------|-------------|
| `basic-data-analytics` | Batch | Simple analytics (Warehouse → Pipeline → Semantic Model → Report) |
| `medallion` | Batch | Progressive data quality (Bronze → Silver → Gold) |
| `lambda` | Hybrid | Batch + real-time combined paths |
| `event-analytics` | Streaming | Real-time IoT/logs with Eventhouse |
| `event-medallion` | Streaming | Real-time medallion layers |
| `data-analytics-sql-endpoint` | Batch | Lakehouse with SQL analytics endpoint |
| `basic-machine-learning-models` | Batch | ML training, experiment tracking, prediction |
| `sensitive-data-insights` | Batch | RLS/OLS/CLS for compliant processing |
| `translytical` | Transactional | Operational BI with SQL Database writeback |
| `app-backend` | API | Application APIs + serverless logic (SQL Database / Cosmos DB) |
| `conversational-analytics` | AI | Self-service analytics via Data Agents + Semantic Models |
| `semantic-governance` | Governance | Enterprise vocabulary, knowledge graph, Ontology |
| `general` | All | Comprehensive reference architecture |

See [`task-flows.md`](task-flows.md) for full decision tables, items, and diagram links.

## 📊 Decision Guides

| Guide | Key Decision | Options |
|-------|-------------|---------|
| [Storage](decisions/storage-selection.md) | Where to store data | Lakehouse, Warehouse, Eventhouse, SQL Database, Cosmos DB, PostgreSQL |
| [Ingestion](decisions/ingestion-selection.md) | How data arrives | Copy Job, Dataflow Gen2, Pipeline, Eventstream, Mirroring, Shortcuts, Fabric Link, Notebook |
| [Processing](decisions/processing-selection.md) | How to transform | Notebook, Spark Job Definition, Dataflow Gen2, KQL Queryset |
| [Visualization](decisions/visualization-selection.md) | How to present | Report, Dashboard, Paginated, Real-Time Dashboard, Data Agent |
| [Skillset](decisions/skillset-selection.md) | Team capability | Code-First `[CF]` vs Low-Code `[LC]` |
| [Parameterization](decisions/parameterization-selection.md) | Multi-env config | Variable Library, parameter.yml, Environment Variables |
| [API](decisions/api-selection.md) | Exposing data to apps | GraphQL API, User Data Functions, Direct Connection |

Each guide has YAML frontmatter with structured options, a `quick_decision` tree, comparison tables, and "Choose when" sections. The [Visualization guide](decisions/visualization-selection.md) also covers **Direct Lake** — the recommended Semantic Model query mode for Fabric sources with Delta tables.

## 🤖 Agents

| Agent | Phase | Purpose | Key Output |
|-------|-------|---------|------------|
| **@fabric-advisor** | 0 — Discover | Infers signals from problem description | Discovery Brief |
| **@fabric-architect** | 1 — Design | Selects task flow, walks through decisions | Architecture Handoff (DRAFT → FINAL) |
| **@fabric-reviewer** | 1 — Design | Combined feasibility + testability review | Consolidated feedback |
| **@fabric-tester** | 2a/3 — Plan/Validate | Mode 0: review DRAFT, Mode 1: test plan, Mode 2: post-deploy validation | Test Plan / Validation Report |
| **@fabric-engineer** | 2c — Deploy | Parallel wave deployment via `fab` CLI or `fabric-cicd` | Deployment Handoff |
| **@fabric-documenter** | 4 — Document | Synthesizes handoffs into wiki-style docs | ADRs + architecture docs |
| **@fabric-healer** | Standalone | Self-healing signal mapper — generates problems, benchmarks, patches keywords | Improved keyword coverage |

All agents include: three-tier boundaries (✅/⚠️/🚫), Signs of Drift, Quality Checklists, structured handoff templates, and `⚠️ ORCHESTRATION` blocks (use `run-pipeline.py advance && next` for phase transitions — no manual agent chaining except Phase 2b sign-off).

### Agent Pipeline

```
Phase 0 — Discover:
┌──────────────┐
│   Advisor    │── "What problems does your project need to solve?"
└──────┬───────┘
       │ Discovery Brief
       ▼
Phase 1 — Design:
┌──────────────┐         ┌─────────────┐
│  Architect   │──DRAFT──►│  Reviewer  │── Combined Review
│              │◄─feedback─┘            │
│  (Finalizes) │
└──────┬───────┘
       │ FINAL Architecture Handoff
       ▼
Phase 2a — Test Plan:       ═══ ★ ONLY HUMAN GATE ═══
┌─────────────┐             ┌─────────────┐
│   Tester    │────────────►│     YOU     │── Review & approve
│ (Test Plan) │             │ (Sign-Off)  │
└─────────────┘             └──────┬──────┘
                                   ▼
Phase 2c — Deploy:          Phase 3 — Validate:    Phase 4 — Document:
┌─────────────┐             ┌─────────────┐        ┌──────────────┐
│  Engineer   │────────────►│   Tester    │───────►│  Documenter  │
│  (Deploy)   │             │ (Validate)  │        │  (ADRs/Wiki) │
└─────────────┘             └─────────────┘        └──────────────┘
```

## ⚡ Deployment & CI/CD

| Tool | Best For | Install |
|------|---------|---------|
| **Fabric CLI** (`fab`) | Interactive, ad-hoc | `pip install ms-fabric-cli` |
| **fabric-cicd** library | Automated CI/CD pipelines | `pip install fabric-cicd` (v0.1.23+) |

The engineer agent groups items into **dependency waves** from the "Depends On" column in deployment diagrams. Items within a wave deploy concurrently; waves execute sequentially. In design-only mode, `scripts/deploy-script-gen.py` generates self-contained deploy scripts with idempotency, retry, and deployment summaries.

See `_shared/cicd-practices.md` for CI/CD reference and `_shared/parallel-deployment.md` for wave analysis.

## 🔍 Automation & Quality

| Script | Purpose | Usage |
|--------|---------|-------|
| `check-drift.py` | Documentation drift detection — 204 cross-reference checks across 6 categories | `python scripts/check-drift.py --check` (CI mode, exit 1 on failure) |
| `sync-item-types.py` | Registry ↔ Fabric CLI alignment | `python scripts/sync-item-types.py --check` |
| `run-pipeline.py` | Pipeline orchestrator — tracks phase state, auto-chains agents | `python scripts/run-pipeline.py start "Project"` |
| `new-project.py` | Project scaffolder — creates all template files | `python scripts/new-project.py "Project Name"` |

Drift detection categories: Task Flow Cross-References, Decision Guide Consistency, Ingestion Guide Internal Consistency, Signal Mapping Validity, Registry Cross-References, Integration First / Better Together compliance.

## 📁 Repository Structure

```
task-flows/
├── LICENSE                            # MIT License
├── CONTRIBUTING.md                    # Contributor guidelines (task flows, diagrams, git workflow)
├── PROJECTS.md                        # Mission control — all projects at a glance
├── .gitignore                         # Excludes __pycache__, projects/, .env
├── .github/
│   ├── agents/                         # GitHub Copilot custom agents (7 agents)
│   │   ├── fabric-advisor.agent.md
│   │   ├── fabric-architect.agent.md
│   │   ├── fabric-reviewer.agent.md
│   │   ├── fabric-engineer.agent.md
│   │   ├── fabric-tester.agent.md
│   │   ├── fabric-documenter.agent.md
│   │   └── fabric-healer.agent.md
│   └── copilot-instructions.md         # System-level agent context
├── task-flows.md                       # All 13 task flow patterns (consolidated)
├── decisions/                          # Decision guides (7 guides)
│   ├── _index.md                       # Routing table — agents read this first
│   ├── storage-selection.md            # Lakehouse vs Warehouse vs Eventhouse vs SQL DB vs Cosmos DB vs PostgreSQL
│   ├── ingestion-selection.md          # Copy Job vs Dataflow vs Pipeline vs Eventstream vs Mirroring vs Shortcuts vs Fabric Link vs Notebook
│   ├── processing-selection.md         # Notebook vs Spark Job vs Dataflow vs KQL Queryset
│   ├── visualization-selection.md      # Report vs Dashboard vs Paginated + Direct Lake + Data Agent
│   ├── skillset-selection.md           # Code-First [CF] vs Low-Code [LC]
│   ├── parameterization-selection.md   # Variable Library vs parameter.yml vs env vars
│   └── api-selection.md                # GraphQL API vs User Data Functions vs Direct Connection
├── diagrams/                           # Deployment diagrams per task flow
│   ├── _index.md                       # Routing table with item/wave counts
│   └── {task-flow}.md                  # Phased deployment flow, dependency order, OR blocks
├── validation/                         # Post-deployment checklists
│   ├── _index.md                       # Routing table with phase names
│   └── {task-flow}.md                  # Phase-by-phase validation checklist
├── projects/                           # Per-project documentation (local only — gitignored)
│   └── {workspace-name}/
│       ├── STATUS.md                   # Phase log, blockers, wave progress
│       ├── pipeline-state.json         # Pipeline orchestration state
│       ├── prd/                        # Agent handoff documents
│       │   ├── discovery-brief.md
│       │   ├── architecture-handoff.md
│       │   ├── engineer-review.md
│       │   ├── tester-review.md
│       │   ├── test-plan.md
│       │   ├── deployment-handoff.md
│       │   └── validation-report.md
│       ├── docs/                       # Architecture docs, ADRs
│       └── deployments/                # Generated deploy scripts
├── scripts/                            # Pipeline utilities & code generation
│   ├── new-project.py                  # Project scaffolder
│   ├── run-pipeline.py                 # Pipeline orchestrator
│   ├── deploy-script-gen.py            # Deploy script generator
│   ├── signal-mapper.py                # Problem signal → task flow mapper
│   ├── decision-resolver.py            # Decision guide YAML resolver
│   ├── handoff-scaffolder.py           # Handoff template filler
│   ├── review-prescan.py               # Architecture review pre-scanner
│   ├── test-plan-prefill.py            # Test plan prefiller from acceptance criteria
│   ├── taskflow-gen.py                 # Task flow JSON generator (scaffold + finalize modes)
│   ├── check-drift.py                  # Documentation drift detection (204 checks)
│   ├── sync-item-types.py              # Registry ↔ Fabric CLI sync
│   ├── generate-ps1-types.py           # PowerShell item-type constant generator
│   ├── registry_loader.py              # Shared module — item type metadata loader
│   ├── validate-items.ps1              # PowerShell item validation helper
│   └── validate-items.sh               # Bash item validation helper
├── _shared/                            # Shared reference content
│   ├── item-type-registry.json         # Single source of truth for Fabric item types (45 types)
│   ├── agent-boundaries.md             # Shared agent boundary reference
│   ├── legend.md                       # Diagram symbols ([LC], [CF], ──►, OR)
│   ├── prerequisites.md                # Setup: Fabric CLI, fabric-cicd, capacity
│   ├── adr-template.md                 # Architecture Decision Record template
│   ├── cicd-practices.md               # CI/CD reference: fabric-cicd, parameter.yml
│   ├── parallel-deployment.md          # Dependency-wave analysis
│   ├── fabric-cli-commands.md          # fab CLI command reference
│   ├── deployment-patterns.md          # fab mkdir patterns per item type
│   ├── rollback-protocol.md            # Wave failure recovery
│   ├── validation-patterns.md          # Item-type verification commands
│   ├── validation-report-template.md   # Validation Report output template
│   ├── documentation-templates.md      # Wiki output templates
│   ├── workflow-guide.md               # Pipeline orchestration guide
│   ├── learnings.md                    # Accumulated learnings
│   ├── script-template.ps1             # PowerShell deploy script template (banner source of truth)
│   ├── script-template.sh              # Bash deploy script template (banner source of truth)
│   └── schemas/                        # Handoff document schemas
│       ├── deployment-handoff.md
│       ├── engineer-review.md
│       ├── phase-progress.md
│       ├── remediation-log.md
│       ├── test-plan.md
│       ├── tester-review.md
│       └── validation-report.md
└── README.md
```

## 📂 Content Routing

All content resolves by **task flow ID** (e.g., `medallion`, `lambda`, `event-analytics`):

| Content Type | Path Pattern |
|--------------|-------------|
| Task flow overview | `task-flows.md` → H2 anchor (`## Medallion`) |
| Deployment diagram | `diagrams/{task-flow-id}.md` |
| Validation checklist | `validation/{task-flow-id}.md` |
| Decision guides | `decisions/{decision-id}.md` |
| Project docs | `projects/{workspace}/docs/` |
| Shared references | `_shared/{file}.md` |

## 📝 Contributing

### Adding a New Task Flow

1. Add H2 section to `task-flows.md` with standard structure
2. Create `diagrams/{task-flow-id}.md` with phased deployment flow
3. Create `validation/{task-flow-id}.md` with phase-by-phase checklist
4. Update `diagrams/_index.md` and `validation/_index.md` with the new entry
5. Reference decision guides in the task-flows.md section
6. Run `python scripts/check-drift.py --check` to verify consistency

### Adding a Decision Guide

1. Create `decisions/{guide-id}.md` with YAML frontmatter (`id`, `title`, `description`, `triggers`, `options`, `quick_decision`)
2. Add entry to `decisions/_index.md`
3. Update this README's decision guides table

### Updating Agents

Agent files are in `.github/agents/`. Each includes three-tier boundaries, Signs of Drift, Quality Checklists, structured handoff templates, and an `⚠️ ORCHESTRATION OVERRIDE` block.

See [CONTRIBUTING.md](CONTRIBUTING.md) for full details on scripts, pipeline state, and conventions.

## 📄 License

MIT
