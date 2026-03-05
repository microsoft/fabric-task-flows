# Task Flows

> Technical architecture guidance for Microsoft Fabric projects.

Task Flows is a knowledge base of pre-defined architectures, decision guides, and deployment validation for Microsoft Fabric. It includes four GitHub Copilot custom agents that work as a pipeline: **Architect** → **Tester** (Test Plan) → **Engineer** (Deploy) → **Tester** (Validate) → **Documenter** (ADRs).

## 📁 Repository Structure

```
task-flows/
├── .github/agents/             # GitHub Copilot custom agents
│   ├── fabric-architect.agent.md   # Architecture decisions
│   ├── fabric-engineer.agent.md    # Deployment execution
│   ├── fabric-tester.agent.md      # Validation & testing
│   └── fabric-documenter.agent.md  # Wiki & ADR generation
├── task-flows.md               # All 10 task flows (consolidated)
├── decisions/                  # Decision guides (5 guides)
│   ├── storage-selection.md
│   ├── ingestion-selection.md
│   ├── processing-selection.md
│   ├── visualization-selection.md
│   └── skillset-selection.md
├── diagrams/                   # Deployment diagrams per task flow
│   └── {task-flow}.md           # Flow, order, architecture
├── validation/                 # Post-deployment checklists
│   └── {task-flow}.md           # Phase-by-phase validation
├── projects/                   # Per-project documentation & deployments
│   └── {workspace-name}/
│       ├── docs/               # Architecture docs & ADRs
│       │   ├── README.md
│       │   ├── architecture.md
│       │   ├── deployment-log.md
│       │   └── decisions/      # ADR files
│       └── deployments/        # Scripts, notebooks, queries
│           ├── handoff.md
│           ├── deploy.sh
│           ├── notebooks/
│           └── queries/
├── _shared/                    # Shared reference content
│   ├── legend.md               # Diagram symbols
│   ├── prerequisites.md        # Common prerequisites
│   └── adr-template.md         # ADR template
└── README.md
```

## 🚀 Quick Start

### Using the Agents

From VS Code with GitHub Copilot, select an agent from the dropdown:

1. **@fabric-architect** - Describe your requirements, get task flow recommendation
2. **@fabric-tester** (Mode 1) - Receive architecture, produce Test Plan
3. **@fabric-engineer** - Deploy items using diagrams + Test Plan awareness
4. **@fabric-tester** (Mode 2) - Validate deployment against checklist
5. **@fabric-documenter** - Generate wiki-style ADRs explaining the "why"

### Agent Pipeline

```
Architect → Tester (Test Plan) → Engineer (Deploy) → Tester (Validate) → Documenter
                                      ↑                                       ↑
                          Receives both inputs              Receives all handoffs
```

The **Documenter** generates human-readable wiki documentation in `docs/[workspace]/` with:
- Architecture Decision Records (ADRs) explaining the "why" behind each choice
- System architecture diagram with item relationships
- Deployment log with configuration rationale

### Example: Medallion Architecture

```
User: I need a medallion architecture with Bronze, Silver, Gold layers 
      for batch data engineering. Team uses Spark/Python.

@fabric-architect:
  Task flow: Medallion
  Storage: Lakehouse (Gold can be Warehouse for BI)
  Ingestion: Pipeline (batch orchestration)
  Processing: Notebook (Spark/Python)
  
  [Architecture Handoff document]

@fabric-tester (Mode 1):
  [Test Plan with acceptance criteria]

@fabric-engineer:
  [Deploys items per diagrams/medallion.md]
  [Deployment Handoff document]

@fabric-tester (Mode 2):
  [Validation Report - PASSED/FAILED]

@fabric-documenter:
  [Generates docs/FraudDetection/ wiki with ADRs]
```

## 📋 Available Task Flows

| ID | Name | Pattern | Description |
|----|------|---------|-------------|
| `medallion` | Medallion | Batch | Progressive data quality (Bronze → Silver → Gold) |
| `general` | General | All | Comprehensive reference architecture |
| `basic-data-analytics` | Basic Data Analytics | Batch | Simple 4-task analytics |
| `basic-machine-learning-models` | Basic ML | Batch | ML training and prediction |
| `lambda` | Lambda | Hybrid | Batch + real-time combined |
| `event-analytics` | Event Analytics | Streaming | Real-time IoT/logs |
| `event-medallion` | Event Medallion | Streaming | Real-time medallion |
| `data-analytics-sql-endpoint` | SQL Endpoint | Batch | Lakehouse with SQL |
| `sensitive-data-insights` | Sensitive Data | Batch | Secure/compliant processing |
| `translytical` | Translytical | Transactional | Operational BI with writeback |

## 📊 Decision Guides

Each decision guide provides comparison tables, decision trees, and "when to use" guidance:

| Guide | Compares |
|-------|----------|
| [Storage Selection](decisions/storage-selection.md) | Lakehouse vs Warehouse vs Eventhouse vs SQL Database |
| [Ingestion Selection](decisions/ingestion-selection.md) | Copy Job vs Dataflow Gen2 vs Pipeline vs Eventstream |
| [Processing Selection](decisions/processing-selection.md) | Notebook vs Spark Job Definition vs Dataflow Gen2 |
| [Visualization Selection](decisions/visualization-selection.md) | Report vs Dashboard vs Paginated vs Scorecard vs Real-Time |
| [Skillset Selection](decisions/skillset-selection.md) | Code-First [CF] vs Low-Code [LC] |

## 🤖 Custom Agents

### fabric-architect

**Purpose:** Guide architecture decisions before deployment

**Tools:** `read`, `search` (read-only)

**Responsibilities:**
- Ask clarifying questions about requirements
- Recommend appropriate task flow
- Walk through relevant decision guides
- Produce Architecture Handoff document

### fabric-tester

**Purpose:** Test planning and validation (shift-left testing)

**Tools:** `read`, `search` (read-only)

**Mode 1 (Pre-Deployment):**
- Receive Architecture Handoff from Architect
- Map acceptance criteria to validation checklist
- Produce Test Plan for Engineer awareness

**Mode 2 (Post-Deployment):**
- Receive Deployment Handoff from Engineer
- Execute validation checklist from `validation/{task-flow}.md`
- Report validation status (PASSED/PARTIAL/FAILED)

### fabric-engineer

**Purpose:** Deploy Fabric items based on architecture

**Tools:** `read`, `edit`, `execute`, `search` (full access)

**Responsibilities:**
- Review Architecture Handoff + Test Plan
- Follow deployment order from `diagrams/{task-flow}.md`
- Configure items per architecture decisions
- Produce Deployment Handoff document

## 📂 Routing Reference

| Content Type | Path | Format |
|--------------|------|--------|
| Task flow overview | `task-flows.md#{task-flow}` | H2 anchor |
| Architecture diagrams | `diagrams/{task-flow}.md` | Deployment flow, order |
| Decision guides | `decisions/{decision-id}.md` | YAML frontmatter + markdown |
| Validation checklists | `validation/{task-flow}.md` | Phase-by-phase checklist |
| Shared content | `_shared/{file}.md` | Legend, prerequisites |

### Task Flow IDs

| ID | Section in task-flows.md |
|----|---------------------|
| `basic-data-analytics` | ## Basic Data Analytics |
| `basic-machine-learning-models` | ## Basic Machine Learning Models |
| `data-analytics-sql-endpoint` | ## Data Analytics SQL Endpoint |
| `event-analytics` | ## Event Analytics |
| `event-medallion` | ## Event Medallion |
| `general` | ## General |
| `lambda` | ## Lambda |
| `medallion` | ## Medallion |
| `sensitive-data-insights` | ## Sensitive Data Insights |
| `translytical` | ## Translytical |

## 🏗️ Decision Logic

### Task Flow Selection

| If you need... | Use |
|----------------|-----|
| Simple batch analytics | `basic-data-analytics` |
| Progressive quality layers | `medallion` |
| Real-time event processing | `event-analytics` |
| Streaming + batch combined | `lambda` |
| Machine learning | `basic-machine-learning-models` |
| Sensitive/compliant data | `sensitive-data-insights` |
| Operational writeback | `translytical` |

### Storage Selection

| If you use... | Choose |
|---------------|--------|
| Spark/Python | Lakehouse |
| T-SQL analytics | Warehouse |
| KQL/time-series | Eventhouse |
| Transactional OLTP | SQL Database |

### Ingestion Selection

| If data arrives... | Choose |
|-------------------|--------|
| Real-time streaming | Eventstream |
| Batch, no transform | Copy Job |
| Batch, visual ETL | Dataflow Gen2 |
| Batch, complex logic | Pipeline |

## 📝 Contributing

### Adding a New Task Flow

1. Add H2 section to `task-flows.md` with standard structure
2. Create `diagrams/{task-flow-id}.md` with deployment flow/order
3. Create `validation/{task-flow-id}.md` with phase checklist
4. Add Decision Guides references in the task-flows.md section

### Adding a New Decision Guide

1. Create `decisions/{decision-id}.md` with YAML frontmatter
2. Include comparison table, decision tree, and "when to use" sections
3. Reference from relevant task flow sections in `task-flows.md`

### Updating Agents

Agent prompts are in `.github/agents/`. Update:
- `fabric-architect.agent.md` for architecture guidance changes
- `fabric-engineer.agent.md` for deployment patterns
- `fabric-tester.agent.md` for validation criteria

## 📄 License

MIT
