# Task Flows

> Technical architecture guidance for Microsoft Fabric projects.

Task flows is a documentation-only knowledge base of pre-defined architectures, decision guides, and deployment validation for Microsoft Fabric. It includes six GitHub Copilot custom agents that collaborate in phases:

```
@fabric-advisor ──► @fabric-architect (DRAFT) ──► @fabric-reviewer (Combined Review)
──► @fabric-architect (FINAL) ──► @fabric-tester (Test Plan) ──► ★ YOU (Sign-Off) ──►
@fabric-engineer (Deploy) ──► @fabric-tester (Validate) ──► @fabric-documenter (ADRs)
```

## 📁 Repository Structure

```
task-flows/
├── LICENSE                            # MIT License
├── PROJECTS.md                        # Mission control — all projects at a glance
├── .github/
│   ├── agents/                         # GitHub Copilot custom agents
│   │   ├── fabric-advisor.agent.md     # Problem discovery & Discovery Brief
│   │   ├── fabric-architect.agent.md   # Architecture decisions (accepts Discovery Brief)
│   │   ├── fabric-reviewer.agent.md    # Combined deployment + testability review (single pass)
│   │   ├── fabric-engineer.agent.md    # Deployment execution (parallel waves, CI/CD)
│   │   ├── fabric-tester.agent.md      # Validation & testing (3 modes)
│   │   └── fabric-documenter.agent.md  # Wiki & ADR generation
│   └── copilot-instructions.md         # System-level agent context
├── task-flows.md                       # All 13 task flow patterns (consolidated)
├── decisions/                          # Decision guides (7 guides)
│   ├── _index.md                       # Routing table — agents read this first
│   ├── storage-selection.md            # Lakehouse vs Warehouse vs Eventhouse vs SQL DB vs Cosmos DB
│   ├── ingestion-selection.md          # Copy Job vs Dataflow vs Pipeline vs Eventstream vs Mirroring
│   ├── processing-selection.md         # Notebook vs Spark Job vs Dataflow vs KQL Queryset
│   ├── visualization-selection.md      # Report vs Dashboard vs Paginated + Direct Lake guidance
│   ├── skillset-selection.md           # Code-First [CF] vs Low-Code [LC]
│   ├── parameterization-selection.md   # Variable Library vs parameter.yml vs env vars
│   └── api-selection.md                # GraphQL API vs User Data Functions vs Direct Connection
├── diagrams/                           # Deployment diagrams per task flow
│   └── {task-flow}.md                  # Phased deployment flow, dependency order, OR blocks
├── validation/                         # Post-deployment checklists
│   └── {task-flow}.md                  # Phase-by-phase validation with Direct Lake guidance
├── projects/                           # Per-project documentation & deployments (local only — gitignored)
│   └── {workspace-name}/
│       ├── STATUS.md                   # Project status tracker (phase log, blockers, wave progress)
│       ├── pipeline-state.json         # Pipeline orchestration state (phase tracking, auto-chain)
│       ├── prd/                        # Agent handoff documents
│       │   ├── discovery-brief.md
│       │   ├── architecture-handoff.md
│       │   ├── engineer-review.md
│       │   ├── tester-review.md
│       │   ├── test-plan.md
│       │   ├── deployment-handoff.md
│       │   └── validation-report.md
│       ├── docs/                       # Architecture docs, ADRs
│       │   ├── README.md
│       │   ├── architecture.md
│       │   ├── deployment-log.md
│       │   └── decisions/              # ADR files (001-task-flow.md, 002-storage.md, etc.)
│       └── deployments/                # Generated deploy scripts
│           └── deploy-{project}.ps1/.sh
├── scripts/                            # Pipeline utilities & code generation
│   ├── new-project.py                  # Project scaffolder (creates all template files)
│   ├── run-pipeline.py                 # Pipeline orchestrator (start/next/status/advance/reset)
│   ├── deploy-script-gen.py            # Deploy script generator (reads architecture → PS1/bash)
│   ├── signal-mapper.py                # Maps problem signals to task flow candidates
│   ├── decision-resolver.py            # Resolves decision guide YAML frontmatter
│   ├── handoff-scaffolder.py           # Fills handoff template sections
│   ├── review-prescan.py               # Pre-scans architecture for review flags
│   ├── test-plan-prefill.py            # Prefills test plan from acceptance criteria
│   ├── taskflow-gen.py                 # Generates task flow Markdown sections
│   ├── fabric-logo.py                  # ASCII logo generator for banners
│   ├── check-drift.py                  # Documentation drift detection (cross-reference checks)
│   ├── sync-item-types.py              # Syncs item-type-registry.json against Fabric CLI
│   ├── generate-ps1-types.py           # Regenerates PowerShell item-type constants from registry
│   ├── registry_loader.py              # Shared module — all scripts import item type metadata from here
│   ├── validate-items.ps1              # PowerShell item validation helper
│   └── validate-items.sh               # Bash item validation helper
├── _shared/                            # Shared reference content
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
│   ├── item-type-registry.json         # Single source of truth for all Fabric item type metadata
│   ├── workflow-guide.md               # Pipeline orchestration, design-only mode, pipeline runner
│   ├── script-banner.md                # Canonical Fabric Task Flows brand banner for all scripts
│   ├── script-template.ps1             # PowerShell deploy script template (idempotency, retry, summary)
│   ├── script-template.sh              # Bash deploy script template (idempotency, retry, summary)
│   └── schemas/                        # Handoff document schemas
└── README.md
```

## 🚀 Quick Start

### Check Project Status

Open [`PROJECTS.md`](PROJECTS.md) at the repo root to see all projects and their current phase. Each project also has a detailed `STATUS.md` tracker at `projects/{name}/STATUS.md`.

### Using the Agents

Start a project by mentioning **@fabric-advisor** in chat and describing your problem. The pipeline flows automatically through these phases:

- **@fabric-advisor** — Discovers your problem, infers architectural signals, produces a Discovery Brief
- **@fabric-architect** — Selects task flow, walks through decisions, produces Architecture Handoff
- **@fabric-reviewer** — Reviews the DRAFT handoff for deployment feasibility and testability in a single pass
- **@fabric-architect** — Incorporates review feedback into FINAL handoff
- **@fabric-tester** — Produces Test Plan from FINAL handoff
- **YOU** — Review architecture + test plan and approve (Phase 2b — the only human gate)
- **@fabric-engineer** — Deploys items by dependency wave
- **@fabric-tester** — Validates deployment against checklist
- **@fabric-documenter** — Generates wiki-style ADRs

### Problem-First Discovery

The **@fabric-advisor** agent starts every new project by asking: *"What problems does your project need to solve?"* It infers architectural signals (data velocity, use case, task flow candidates) from the user's natural-language description and produces a **Discovery Brief**.

The pipeline then continues automatically — **@fabric-architect** receives the brief, confirms the inferred signals, fills in remaining gaps (skillset, workspace), and proceeds with the full decision walkthrough. If no Discovery Brief is available, the architect can also start fresh with its core questions.

Values not collected by the architect are prompted just-in-time by the **@fabric-engineer** at deployment time, with sensible defaults.

### Agent Pipeline (Continuous Flow)

```
═══════════════════════  AUTOMATIC FLOW  ═══════════════════════

Phase 0 — Discover:
┌──────────────┐
│   Advisor    │── "What problems does your project need to solve?"
│  (Discovers) │
└──────┬───────┘
       │ Discovery Brief
       ▼
Phase 1 — Design:
┌──────────────┐         ┌─────────────┐
│  Architect   │──DRAFT──►│  Reviewer  │── Combined Feasibility + Testability Review
│  (Leads)     │         │ (Reviews)   │
│              │         └─────────────┘
│              │◄── feedback ──────────┘
│  (Finalizes) │
└──────┬───────┘
       │ FINAL Architecture Handoff
       ▼
Phase 2a — Test Plan:
┌─────────────┐
│   Tester    │
│ (Test Plan) │
└──────┬──────┘
       │
       ▼
═══════════════  ★ ONLY HUMAN GATE  ════════════════════════════

Phase 2b — Sign-Off:
┌─────────────┐
│     YOU     │── Review architecture + test plan and approve
│ (Sign-Off)  │
└──────┬──────┘
       │ ✅ Approved
       ▼
═══════════════════════  AUTOMATIC FLOW  ═══════════════════════

Phase 2c — Deploy:
┌─────────────┐
│  Engineer   │
│  (Deploy)   │
└──────┬──────┘
       │
       ▼
Phase 3 — Validate:     Phase 4 — Document:
┌─────────────┐         ┌──────────────┐
│   Tester    │────────►│  Documenter  │
│ (Validate)  │         │  (ADRs/Wiki) │
└─────────────┘         └──────────────┘
```

The advisor discovers the problem, and the pipeline flows automatically through design, review, and test planning. **You review and approve** the architecture and test plan (the only manual step), then deployment, validation, and documentation continue automatically. Each agent produces structured **handoff documents** — the architect's includes a Design Review section documenting what feedback was incorporated.

### Pipeline Runner

Use `scripts/run-pipeline.py` to manage the full pipeline lifecycle — it tracks phase state, runs pre-compute scripts, and generates agent prompts automatically. See `_shared/workflow-guide.md` for details.

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
| `app-backend` | App Backend | API | Application APIs + serverless logic on SQL Database / Cosmos DB |
| `conversational-analytics` | Conversational Analytics | AI | Self-service analytics via Data Agents + Semantic Models |
| `semantic-governance` | Semantic Governance | Governance | Enterprise vocabulary, knowledge graph, Ontology |
| `general` | General | All | Comprehensive reference architecture |

## 📊 Decision Guides

| Guide | Key Decision | Options |
|-------|-------------|---------|
| [Storage](decisions/storage-selection.md) | Where to store data | Lakehouse, Warehouse, Eventhouse, SQL Database, Cosmos DB, PostgreSQL |
| [Ingestion](decisions/ingestion-selection.md) | How data arrives | Copy Job, Dataflow Gen2, Pipeline, Eventstream, Mirroring, Shortcuts, Fabric Link, Notebook |
| [Processing](decisions/processing-selection.md) | How to transform | Notebook, Spark Job Definition, Dataflow Gen2, KQL Queryset |
| [Visualization](decisions/visualization-selection.md) | How to present | Report, Dashboard, Paginated, Real-Time Dashboard |
| [Skillset](decisions/skillset-selection.md) | Team capability | Code-First `[CF]` vs Low-Code `[LC]` |
| [Parameterization](decisions/parameterization-selection.md) | Multi-env config | Variable Library, parameter.yml, Environment Variables |
| [API](decisions/api-selection.md) | Exposing data to apps | GraphQL API, User Data Functions, Direct Connection |

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

### @fabric-advisor

**Purpose:** Problem discovery and scoping — the first agent users interact with

**Responsibilities:**
- Ask what problems the project needs to solve
- Infer architectural signals (data velocity, use case, task flow candidates) from the problem description
- Confirm inferences with the user
- Produce a Discovery Brief for `@fabric-architect`

### @fabric-architect

**Purpose:** Guide architecture decisions before deployment

**Responsibilities:**
- Accept Discovery Brief (or gather requirements directly if invoked without one)
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

### @fabric-reviewer

**Purpose:** Combined deployment feasibility + testability review in a single pass

**Responsibilities:**
- Receive DRAFT Architecture Handoff from `@fabric-architect`
- Evaluate deployment feasibility (engineer perspective) and testability (tester perspective) together
- Return consolidated feedback — the architect incorporates it into the FINAL handoff
- Replaces the previous parallel `@fabric-engineer` + `@fabric-tester` Mode 0 review pattern

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

### Deploy Script Generation

In design-only mode, the engineer generates self-contained deploy scripts via `scripts/deploy-script-gen.py`. Generated scripts include:

| Feature | Description |
|---------|-------------|
| **Preflight check** | Verifies `fab` CLI is installed before prompting |
| **Workspace auto-creation** | Checks if workspace exists; creates it if not |
| **Item idempotency** | Skips items that already exist (`fab exists` check) |
| **Retry with backoff** | 3 attempts with 10s/20s/30s delays on failure |
| **Environment publish wait** | Polls for Environment readiness (30s intervals, 30min timeout) |
| **Notebook binding** | Auto-binds lakehouse + environment via `fab set` after creation |
| **Item ID resolution** | Captures SemanticModel/Eventhouse IDs for dependent items (Report, KQLDatabase) |
| **Deployment summary** | Final report showing ✅/⏭️/❌ status per item |

The scripts prompt only for **workspace name** (with environment variable fallback). Authentication, capacity, and tenant are handled natively by the `fab` CLI.

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
4. Update `diagrams/_index.md` and `validation/_index.md` with the new entry
5. Reference decision guides in the task-flows.md section

### Adding a Decision Guide

1. Create `decisions/{guide-id}.md` with YAML frontmatter (`id`, `title`, `description`, `triggers`, `options`, `quick_decision`)
2. Add entry to `decisions/_index.md`
3. Update this README's decision guides table

### Terminology Rules

- Path templates use hyphenated form: `{task-flow-id}`

### Updating Agents

Agent files are in `.github/agents/`. Each includes:
- Three-tier boundaries (✅ Always / ⚠️ Ask first / 🚫 Never)
- Signs of Drift (role-specific indicators)
- Quality Checklists (pre-handoff self-review)
- Structured handoff templates
- `⚠️ ORCHESTRATION OVERRIDE` block (never ask "Want me to continue?" — auto-chain to next phase)

See [CONTRIBUTING.md](CONTRIBUTING.md) for full details on scripts, pipeline state, and conventions.

## 📄 License

MIT
