# Task Flows

> Technical architecture guidance for Microsoft Fabric projects.

A documentation-only knowledge base of pre-defined architectures, decision guides, and deployment validation for Microsoft Fabric. One orchestrator agent (`@fabric-advisor`) delegates to six composable skills — from problem discovery through deployment and documentation:

```
@fabric-advisor ──► /fabric-discover ──► /fabric-design (DRAFT → Review → FINAL)
──► /fabric-test (Plan) ──► ★ YOU (Approve or Revise ↩ max 3) ──► /fabric-deploy
──► /fabric-test (Validate) ──► /fabric-document (ADRs)
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

## 🤖 Agent & Skills

A single orchestrator agent (`@fabric-advisor`) handles discovery directly and delegates all other phases to six composable skills. Use `run-pipeline.py advance && next` for phase transitions — no manual agent chaining except Phase 2b sign-off.

### Skills

Skills are composable, auto-activating instruction packs stored in `.github/skills/`. Each skill is a focused, single-workflow unit with trigger phrases, bundled references, and pre-compute scripts. Skills follow the [Agent Skills open standard](https://github.com/agentskills/agentskills) and activate automatically when Copilot detects a relevant prompt.

| Skill | Phase(s) | Purpose | Trigger Examples |
|-------|----------|---------|-----------------|
| `/fabric-discover` | 0a | Signal inference from problem statements | "analyze my data problem", "what task flow fits" |
| `/fabric-design` | 1a, 1b, 1c | DRAFT → Review → FINAL architecture | "design architecture", "medallion vs lambda" |
| `/fabric-test` | 2a, 3 | Test plan + post-deployment validation | "create test plan", "map acceptance criteria" |
| `/fabric-deploy` | 2c | Wave-based deployment via `fab` CLI | "deploy items", "run deployment" |
| `/fabric-document` | 4 | Wiki + ADR synthesis from handoffs | "generate docs", "write ADRs" |
| `/fabric-heal` | Standalone | Signal mapper self-healing | "heal signal mapper", "improve coverage" |

### Pipeline

```
Phase 0 — Discover:
┌──────────────┐
│   Advisor    │── "What problems does your project need to solve?"
└──────┬───────┘
       │ Discovery Brief
       ▼
Phase 1 — Design:
┌──────────────┐          ┌────────────┐
│ /fab-design  │──DRAFT──►│ /fab-design│── Combined Review (1b)
│   (1a)       │◄─feedback─┘           │
│ (Finalizes 1c)│
└──────┬───────┘
       │ FINAL Architecture Handoff
       ▼
Phase 2a — Test Plan:       ═══ ★ ONLY HUMAN GATE ═══
┌─────────────┐             ┌─────────────┐
│ /fab-test   │────────────►│     YOU     │── Approve or revise
│ (Test Plan) │             │ (Sign-Off)  │
└─────────────┘             └──────┬──────┘
                              ┌────┴────┐
                              ▼         ▼
                          approved   revise (max 3)
                              │         │
                              ▼         └──► 1c Finalize ──► 2a ──► 2b
Phase 2c — Deploy:          Phase 3 — Validate:    Phase 4 — Document:
┌─────────────┐             ┌─────────────┐        ┌──────────────┐
│ /fab-deploy │────────────►│  /fab-test  │───────►│  /fab-document│
│  (Deploy)   │             │ (Validate)  │        │  (ADRs/Wiki)  │
└─────────────┘             └─────────────┘        └──────────────┘
```

## ⚡ Deployment & CI/CD

| Tool | Best For | Install |
|------|---------|---------|
| **Fabric CLI** (`fab`) | Interactive, ad-hoc | `pip install ms-fabric-cli` |
| **fabric-cicd** library | Automated CI/CD pipelines | `pip install fabric-cicd` (v0.1.23+) |

The `/fabric-deploy` skill groups items into **dependency waves** from the "Depends On" column in deployment diagrams. Items within a wave deploy concurrently; waves execute sequentially. In design-only mode, the `deploy-script-gen.py` pre-compute script generates self-contained deploy scripts with idempotency, retry, and deployment summaries.

See the fabric-deploy skill's `references/` for CI/CD practices and parallel deployment guidance.

## 🔍 Automation & Quality

| Script | Purpose | Usage |
|--------|---------|-------|
| `run-pipeline.py` | Pipeline orchestrator — tracks phase state, auto-chains skills | `python scripts/run-pipeline.py start "Project"` |
| `new-project.py` | Project scaffolder — creates all template files | `python scripts/new-project.py "Project Name"` |
| `fleet-runner.py` | Batch runner — runs all problem statements through the pipeline | `python scripts/fleet-runner.py --problem-file ...` |
| `sync-item-types.py` | Registry ↔ Fabric CLI alignment | `python scripts/sync-item-types.py --check` |

Each skill also bundles pre-compute scripts (e.g., `signal-mapper.py`, `deploy-script-gen.py`, `check-drift.py`) in its own `scripts/` subdirectory. The `check-drift.py` script (in `/fabric-test`) runs 26 cross-reference checks across 6 categories: Task Flow Cross-References, Decision Guide Consistency, Ingestion Guide Internal Consistency, Signal Mapping Validity, Registry Cross-References, Integration First / Better Together compliance.

## 📁 Repository Structure

```
task-flows/
├── LICENSE                            # MIT License
├── CONTRIBUTING.md                    # Contributor guidelines (task flows, diagrams, git workflow)
├── PROJECTS.md                        # Mission control — all projects at a glance
├── legend.md                          # Diagram symbols ([LC], [CF], ──►, OR)
├── task-flows.md                      # All 13 task flow patterns (consolidated)
├── .gitignore                         # Excludes __pycache__, projects/, .env
├── .github/
│   ├── copilot-instructions.md        # System-level agent context
│   ├── agents/                        # GitHub Copilot custom agent
│   │   └── fabric-advisor.agent.md    # Orchestrator — discovery + skill delegation
│   └── skills/                        # Composable skills (6 skills)
│       ├── fabric-discover/           # Phase 0a — signal inference
│       │   ├── SKILL.md
│       │   └── scripts/signal-mapper.py
│       ├── fabric-design/             # Phases 1a, 1b, 1c — architecture lifecycle
│       │   ├── SKILL.md
│       │   ├── scripts/               # decision-resolver, handoff-scaffolder, review-prescan, diagram-gen, diagram-validator
│       │   ├── references/            # adr-template, cicd-practices
│       │   └── schemas/               # engineer-review, tester-review
│       ├── fabric-test/               # Phases 2a, 3 — test plan + validation
│       │   ├── SKILL.md
│       │   ├── scripts/               # check-drift, test-plan-prefill, validate-items (.ps1/.sh)
│       │   ├── references/            # validation-patterns, validation-report-template
│       │   └── schemas/               # test-plan, validation-report, remediation-log
│       ├── fabric-deploy/             # Phase 2c — wave-based deployment
│       │   ├── SKILL.md
│       │   ├── scripts/               # deploy-script-gen, taskflow-gen, generate-ps1-types
│       │   ├── assets/                # fabric_deploy.py, script-template (.ps1/.sh)
│       │   ├── references/            # prerequisites, fabric-cli-commands, deployment-patterns, parallel-deployment, rollback-protocol
│       │   └── schemas/               # deployment-handoff, phase-progress
│       ├── fabric-document/           # Phase 4 — wiki + ADR synthesis
│       │   ├── SKILL.md
│       │   └── references/            # documentation-templates, adr-template
│       └── fabric-heal/               # Standalone — signal mapper self-healing
│           ├── SKILL.md
│           ├── problem-statements.md
│           └── scripts/               # analyze-inefficiencies, heal-orchestrator, self-heal
├── decisions/                         # Decision guides (7 guides)
│   ├── _index.md                      # Routing table — agents read this first
│   ├── storage-selection.md
│   ├── ingestion-selection.md
│   ├── processing-selection.md
│   ├── visualization-selection.md
│   ├── skillset-selection.md
│   ├── parameterization-selection.md
│   └── api-selection.md
├── diagrams/                          # Deployment diagrams per task flow
│   ├── _index.md                      # Routing table with item/wave counts
│   └── {task-flow}.md                 # 13 diagrams — phased deployment flow, dependency order
├── validation/                        # Post-deployment checklists
│   ├── _index.md                      # Routing table with phase names
│   └── {task-flow}.md                 # 13 checklists — phase-by-phase validation
├── scripts/                           # Pipeline utilities
│   ├── run-pipeline.py                # Pipeline orchestrator
│   ├── new-project.py                 # Project scaffolder
│   ├── fleet-runner.py                # Batch project runner
│   └── sync-item-types.py            # Registry ↔ Fabric CLI sync
├── tests/                             # Automated tests
│   ├── test_registry_loader.py        # Item-type registry validation
│   ├── test_deploy_script_gen.py      # Deploy script correctness
│   └── test_taskflow_gen.py           # Task flow JSON schema compliance
├── _shared/                           # Shared reference content
│   ├── item-type-registry.json        # Single source of truth for Fabric item types
│   ├── registry_loader.py             # Shared module — item type metadata loader
│   ├── workflow-guide.md              # Pipeline orchestration guide
│   └── learnings.md                   # Accumulated operational learnings
├── projects/                          # Per-project documentation (local only — gitignored)
│   └── {workspace-name}/
│       ├── STATUS.md                  # Phase log, blockers, wave progress
│       ├── pipeline-state.json        # Pipeline orchestration state
│       ├── prd/                       # Skill handoff documents
│       │   ├── discovery-brief.md
│       │   ├── architecture-handoff.md
│       │   ├── engineer-review.md
│       │   ├── tester-review.md
│       │   ├── test-plan.md
│       │   ├── deployment-handoff.md
│       │   └── validation-report.md
│       ├── docs/                      # Architecture docs, ADRs
│       └── deployments/               # Generated deploy scripts
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
6. Run `python .github/skills/fabric-test/scripts/check-drift.py --check` to verify consistency

### Adding a Decision Guide

1. Create `decisions/{guide-id}.md` with YAML frontmatter (`id`, `title`, `description`, `triggers`, `options`, `quick_decision`)
2. Add entry to `decisions/_index.md`
3. Update this README's decision guides table

### Updating Skills

Skill files are in `.github/skills/`. Each SKILL.md includes trigger phrases, bundled references, and pre-compute script declarations. The single agent (`@fabric-advisor`) is in `.github/agents/`.

See [CONTRIBUTING.md](CONTRIBUTING.md) for full details on scripts, pipeline state, and conventions.

## 📄 License

MIT
