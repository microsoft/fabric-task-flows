# Task Flows

> Technical architecture guidance for Microsoft Fabric projects.

Task flows is a documentation-only knowledge base of pre-defined architectures, decision guides, and deployment validation for Microsoft Fabric. It includes four GitHub Copilot custom agents that collaborate in phases:

```
@fabric-architect (DRAFT) ──► @fabric-engineer + @fabric-tester (Design Review)
@fabric-architect (FINAL) ──► @fabric-tester (Test Plan) + @fabric-engineer (Deploy)
                               @fabric-tester (Validate) → @fabric-documenter (ADRs)
```

## 📁 Repository Structure

```
task-flows/
├── PROJECTS.md                    # Mission control — all projects at a glance
├── .github/
│   ├── agents/                     # GitHub Copilot custom agents
│   │   ├── fabric-architect.agent.md   # Architecture decisions (core/advanced prompting)
│   │   ├── fabric-engineer.agent.md    # Deployment execution (parallel waves, CI/CD)
│   │   ├── fabric-tester.agent.md      # Validation & testing (3 modes)
│   │   └── fabric-documenter.agent.md  # Wiki & ADR generation
│   └── copilot-instructions.md     # System-level agent context
├── task-flows.md                   # All 10 task flow patterns (consolidated)
├── decisions/                      # Decision guides (5 guides)
│   ├── storage-selection.md            # Lakehouse vs Warehouse vs Eventhouse vs SQL DB
│   ├── ingestion-selection.md          # Copy Job vs Dataflow vs Pipeline vs Eventstream
│   ├── processing-selection.md         # Notebook vs Spark Job vs Dataflow
│   ├── visualization-selection.md      # Report vs Dashboard vs Paginated + Direct Lake guidance
│   └── skillset-selection.md           # Code-First [CF] vs Low-Code [LC]
├── diagrams/                       # Deployment diagrams per task flow
│   └── {task-flow}.md                  # Phased deployment flow, dependency order, OR blocks
├── validation/                     # Post-deployment checklists
│   └── {task-flow}.md                  # Phase-by-phase validation with Direct Lake guidance
├── projects/                       # Per-project documentation & deployments
│   └── {workspace-name}/
│       ├── STATUS.md                    # Project status tracker (phase log, blockers, wave progress)
│       ├── docs/                       # Architecture docs, test plans, ADRs
│       │   ├── test-plan.md
│       │   ├── architecture.md
│       │   ├── deployment-log.md
│       │   └── decisions/              # ADR files (001-task-flow.md, 002-storage.md, etc.)
│       └── deployments/                # Handoff, scripts, notebooks, queries
│           ├── handoff.md
│           └── ...
├── _shared/                        # Shared reference content
│   ├── legend.md                       # Diagram symbols ([LC], [CF], ──►, OR)
│   ├── prerequisites.md                # Setup: Fabric CLI, fabric-cicd, capacity, connections
│   ├── adr-template.md                 # Architecture Decision Record template
│   ├── cicd-practices.md               # CI/CD reference: fabric-cicd, parameter.yml, gotchas
│   ├── parallel-deployment.md          # Dependency-wave analysis, bash template, timing
│   ├── fabric-cli-commands.md          # fab CLI command reference
│   ├── deployment-patterns.md          # fab mkdir patterns per item type
│   ├── rollback-protocol.md            # Wave failure recovery and cleanup
│   ├── validation-patterns.md          # Item-type verification commands
│   ├── validation-report-template.md   # Validation Report output template
│   ├── documentation-templates.md      # Wiki output templates (README, architecture, deploy log)
│   └── workflow-guide.md               # Step-by-step pipeline orchestration with copy-paste prompts
└── README.md
```

## 🚀 Quick Start

### Check Project Status

Open [`PROJECTS.md`](PROJECTS.md) at the repo root to see all projects and their current phase. Each project also has a detailed `STATUS.md` tracker at `projects/{name}/STATUS.md`.

### Using the Agents

From VS Code / GitHub.com with GitHub Copilot, mention an agent in chat:

1. **@fabric-architect** — Describe your requirements → get a task flow recommendation and Architecture Handoff
2. **@fabric-tester** (Mode 1) — Receive the handoff → produce a Test Plan with acceptance criteria and pre-deployment blockers
3. **@fabric-engineer** — Deploy items using dependency-wave parallelism with `fab` CLI or `fabric-cicd`
4. **@fabric-tester** (Mode 2) — Validate the deployment against the task flow checklist
5. **@fabric-documenter** — Generate wiki-style ADRs explaining the "why" behind each decision

### Core vs Advanced Mode

The **@fabric-architect** uses a two-tier prompting model:

- **Core** (5 questions, always asked): Project name, development velocity, skillset + language follow-up, primary use case, workspace (existing or new)
- **Advanced** (opt-in): Capacity pools, environment names, Event Hub config, source connections, alert thresholds

Values not collected by the architect are prompted just-in-time by the **@fabric-engineer** at deployment time, with sensible defaults.

### Agent Pipeline (Collaborative Phases)

```
Phase 1 — Design:
┌──────────────┐         ┌─────────────┐
│  Architect   │──DRAFT──►│  Engineer  │── Deployment Feasibility Review
│  (Leads)     │         │  (Reviews)  │
│              │         └─────────────┘
│              │         ┌─────────────┐
│              │──DRAFT──►│   Tester   │── Testability Review
│              │         │  (Reviews)  │
│              │         └─────────────┘
│              │◄── feedback ──────────┘
│  (Finalizes) │
└──────┬───────┘
       │ FINAL Architecture Handoff
       ▼
Phase 2 — Plan + Deploy:
┌─────────────┐         ┌─────────────┐
│   Tester    │         │  Engineer   │
│ (Test Plan) │         │  (Deploy)   │
└──────┬──────┘         └──────┬──────┘
       │                       │
       ▼                       ▼
Phase 3 — Validate:     Phase 4 — Document:
┌─────────────┐         ┌──────────────┐
│   Tester    │────────►│  Documenter  │
│ (Validate)  │         │  (ADRs/Wiki) │
└─────────────┘         └──────────────┘
```

The architect leads design but collaborates with the engineer (deployment expertise) and tester (testability expertise) before finalizing. Each agent produces structured **handoff documents** — the architect's includes a Design Review section documenting what feedback was incorporated.

## 📋 Available Task Flows

| ID | Name | Pattern | Description |
|----|------|---------|-------------|
| `basic-data-analytics` | Basic Data Analytics | Batch | Simple 4-item analytics (Warehouse → Pipeline → Semantic Model → Report) |
| `medallion` | Medallion | Batch | Progressive data quality (Bronze → Silver → Gold) |
| `lambda` | Lambda | Hybrid | Batch + real-time combined paths |
| `event-analytics` | Event Analytics | Streaming | Real-time IoT/logs with Eventhouse |
| `event-medallion` | Event Medallion | Streaming | Real-time medallion layers |
| `data-analytics-sql-endpoint` | SQL Endpoint | Batch | Lakehouse with SQL analytics endpoint |
| `basic-machine-learning-models` | Basic ML | Batch | ML training, experiment tracking, prediction |
| `sensitive-data-insights` | Sensitive Data | Batch | RLS/OLS/CLS for compliant processing |
| `translytical` | Translytical | Transactional | Operational BI with SQL Database writeback |
| `general` | General | All | Comprehensive reference architecture |

## 📊 Decision Guides

| Guide | Key Decision | Options |
|-------|-------------|---------|
| [Storage](decisions/storage-selection.md) | Where to store data | Lakehouse, Warehouse, Eventhouse, SQL Database, PostgreSQL |
| [Ingestion](decisions/ingestion-selection.md) | How data arrives | Copy Job, Dataflow Gen2, Pipeline, Eventstream |
| [Processing](decisions/processing-selection.md) | How to transform | Notebook, Spark Job Definition, Dataflow Gen2 |
| [Visualization](decisions/visualization-selection.md) | How to present | Report, Dashboard, Paginated, Scorecard, Real-Time Dashboard |
| [Skillset](decisions/skillset-selection.md) | Team capability | Code-First `[CF]` vs Low-Code `[LC]` |

### Direct Lake Guidance

The [Visualization Selection](decisions/visualization-selection.md) guide includes comprehensive **Direct Lake** guidance — the recommended Semantic Model query mode for any Fabric source with Delta tables in OneLake:

| Fabric Source | Direct Lake Support | How Data Reaches OneLake |
|--------------|-------------------|--------------------------|
| Lakehouse | ✅ Native | Delta tables stored directly |
| Warehouse | ✅ Native | Tables stored as Delta/Parquet |
| SQL Database | ✅ Via mirroring | Automatic mirroring to Delta format |
| Eventhouse / KQL Database | ✅ Via OneLake availability | Enable OneLake availability |
| Mirrored Databases | ✅ Via mirroring | Fabric mirroring from external sources |

## 🤖 Custom Agents

### @fabric-architect

**Purpose:** Guide architecture decisions before deployment

**Responsibilities:**
- Ask core questions (5) with optional advanced deep-dive
- Follow up on code-first language (T-SQL, Python/PySpark, Spark/Scala, Mixed)
- Recommend task flow + walk through decision guides
- Recommend Semantic Model query mode (Direct Lake by default)
- Produce Architecture Handoff with decisions, items, deployment order, acceptance criteria, alternatives considered, and trade-offs

### @fabric-tester

**Purpose:** Test planning (pre-deployment) and validation (post-deployment)

**Mode 1 (Pre-Deployment):**
- Receive Architecture Handoff → produce Test Plan
- Map acceptance criteria to validation checklist phases
- Identify pre-deployment blockers and edge cases

**Mode 2 (Post-Deployment):**
- Receive Deployment Handoff → execute validation checklist from `validation/{task-flow}.md`
- Verify items with `fab exists`, `fab ls`, `fab get`
- Report validation status (PASSED / PARTIAL / FAILED)

### @fabric-engineer

**Purpose:** Deploy Fabric items based on architecture

**Key capabilities:**
- **Parallel deployment** — Analyzes dependency graph and deploys items in concurrent waves (see `_shared/parallel-deployment.md`)
- **Sub-agent delegation** — Orchestrates waves sequentially but delegates items within a wave to parallel sub-agents
- **Dual tooling** — Supports `fab` CLI (interactive) and `fabric-cicd` library (automated CI/CD)
- **Direct Lake configuration** — Configures optimal query mode for all Fabric sources
- **Rollback & error recovery** — Wave failure protocol with cleanup decision table
- **Just-in-time prompting** — Only asks for values when needed per item, with sensible defaults

### @fabric-documenter

**Purpose:** Synthesize all pipeline handoffs into wiki-style documentation

**Produces in `projects/{workspace}/docs/`:**
- Architecture Decision Records (ADRs) explaining the "why" behind each choice
- System architecture overview with item relationships
- Deployment log with configuration rationale
- CI/CD ADR (006-cicd.md) when multi-environment

## ⚡ Deployment & CI/CD

### Deployment Tooling

| Tool | Best For | Install |
|------|---------|---------|
| **Fabric CLI** (`fab`) | Interactive, ad-hoc, learning | `pip install ms-fabric-cli` |
| **fabric-cicd** library | Automated CI/CD pipelines | `pip install fabric-cicd` (v0.1.23+) |

### Parallel Deployment

The engineer agent groups items into **dependency waves** based on the "Depends On" column in deployment diagrams. Items within a wave deploy concurrently; waves execute sequentially:

```
Wave 1: Foundation items (no dependencies)     ─── parallel ───►
Wave 2: Items depending only on Wave 1         ─── parallel ───►
Wave 3: Items depending on Wave 2              ─── parallel ───►
```

### CI/CD Practices

See `_shared/cicd-practices.md` for the full reference:
- Workspace strategy presented as a user choice (single vs multi-workspace)
- `fabric-cicd` integration with `parameter.yml` for environment-specific values
- Per-item deployment gotchas (Notebook lakehouse binding, Environment publish time, Semantic Model manual connection)
- Connection management and capacity pool configuration
- Autoscale Billing as alternative to fixed capacity SKUs

## 📂 Content Routing

All content resolves by **task flow ID** (e.g., `medallion`, `lambda`, `event-analytics`):

| Content Type | Path Pattern |
|--------------|-------------|
| Task flow overview | `task-flows.md` → H2 anchor (`## Medallion`) |
| Deployment diagram | `diagrams/{task-flow-id}.md` |
| Validation checklist | `validation/{task-flow-id}.md` |
| Project docs | `projects/{workspace}/docs/` |
| Project deployments | `projects/{workspace}/deployments/` |
| Decision guides | `decisions/{decision-id}.md` |
| Shared references | `_shared/{file}.md` |

## 📝 Contributing

### Adding a New Task Flow

1. Add H2 section to `task-flows.md` with standard structure
2. Create `diagrams/{task-flow-id}.md` with phased deployment flow
3. Create `validation/{task-flow-id}.md` with phase-by-phase checklist
4. Reference decision guides in the task-flows.md section

### Terminology Rules

- Path templates use hyphenated form: `{task-flow-id}`

### Updating Agents

Agent files are in `.github/agents/`. Each includes:
- Three-tier boundaries (✅ Always / ⚠️ Ask first / 🚫 Never)
- Signs of Drift (role-specific indicators)
- Quality Checklists (pre-handoff self-review)
- Structured handoff templates

## 📄 License

MIT
