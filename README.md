# Task Flows

> Technical architecture guidance for Microsoft Fabric projects.

A documentation-only knowledge base of pre-defined architectures, decision guides, and deployment validation for Microsoft Fabric. One orchestrator agent (`@fabric-advisor`) delegates to six composable skills — from problem discovery through deployment and documentation:

```
@fabric-advisor ──► /fabric-discover ──► /fabric-design (DRAFT → Review → FINAL)
──► /fabric-test (Plan) ──► ★ YOU (Approve or Revise ↩ max 3) ──► /fabric-deploy
──► /fabric-test (Validate) ──► /fabric-document (ADRs)
```

## 🚀 Quick Start

1. **Start a project** — run `python _shared/scripts/run-pipeline.py start "Your Project Name" --problem "describe your problem"`
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
| `/fabric-deploy` | 2c | Wave-based deployment via `fabric-cicd` | "deploy items", "run deployment" |
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

| Tool | Purpose | Install |
|------|---------|---------|
| **fabric-cicd** library | Deployment + validation | `pip install fabric-cicd` (v0.1.23+) |

The `/fabric-deploy` skill groups items into **dependency waves** from the "Depends On" column in deployment diagrams. Items within a wave deploy concurrently; waves execute sequentially. The `deploy-script-gen.py` pre-compute script generates `fabric-cicd` workspace directories and self-contained deploy scripts with idempotency, retry, and deployment summaries. Post-deployment validation uses `validate-items.py` to verify items via the Fabric REST API — no additional dependencies beyond `fabric-cicd`.

See the fabric-deploy skill's `references/` for CI/CD practices and parallel deployment guidance.

## 🔍 Automation & Quality

| Script | Purpose | Usage |
|--------|---------|-------|
| `run-pipeline.py` | Pipeline orchestrator — tracks phase state, auto-chains skills | `python _shared/scripts/run-pipeline.py start "Project"` |
| `new-project.py` | Project scaffolder — creates all template files | `python _shared/scripts/new-project.py "Project Name"` |
| `fleet-runner.py` | Batch runner — runs all problem statements through the pipeline | `python _shared/scripts/fleet-runner.py --problem-file ...` |
| `sync-item-types.py` | Registry alignment | `python _shared/scripts/sync-item-types.py --check` |

Each skill also bundles pre-compute scripts (e.g., `signal-mapper.py`, `deploy-script-gen.py`, `check-drift.py`) in its own `scripts/` subdirectory. The `check-drift.py` script (in `/fabric-test`) runs 26 cross-reference checks across 6 categories: Task Flow Cross-References, Decision Guide Consistency, Ingestion Guide Internal Consistency, Signal Mapping Validity, Registry Cross-References, Integration First / Better Together compliance.

## 📁 Repository Structure

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full directory tree and contributor guidelines.

Key directories:

| Directory | Purpose |
|-----------|---------|
| `.github/agents/` | Orchestrator agent (`@fabric-advisor`) |
| `.github/skills/` | 6 composable skills (discover, design, test, deploy, document, heal) |
| `decisions/` | 7 decision guides with YAML frontmatter |
| `diagrams/` | 13 deployment diagrams (human reference — use `diagram_parser` for programmatic access) |
| `_shared/registry/` | Canonical JSON data (use Python tools, not raw reads) |
| `_shared/lib/` | Shared Python modules (`registry_loader`, `diagram_parser`, etc.) |
| `_shared/scripts/` | Pipeline utilities (`run-pipeline.py`, `new-project.py`, `file-audit.py`) |
| `_projects/` | Per-project documentation (gitignored) |

## 📂 Content Routing

All content resolves by **task flow ID** (e.g., `medallion`, `lambda`, `event-analytics`):

| Content Type | Path Pattern |
|--------------|-------------|
| Task flow overview | `task-flows.md` → H2 anchor (`## Medallion`) |
| Deployment diagram | `diagrams/{task-flow-id}.md` |
| Validation checklist | `_shared/registry/validation-checklists.json` |
| Decision guides | `decisions/{decision-id}.md` |
| Project docs | `_projects/{workspace}/docs/` |
| Shared references | `_shared/{file}.md` |

## 📝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding task flows, decision guides, updating skills, and git workflow conventions.

## 📄 License

MIT
