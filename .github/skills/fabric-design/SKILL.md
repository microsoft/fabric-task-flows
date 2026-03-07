---
name: fabric-design
description: >
  Designs Microsoft Fabric architectures by selecting task flows and walking
  through storage, ingestion, processing, and visualization decisions.
  Produces a DRAFT Architecture Handoff. Use when user says "design
  architecture", "which task flow", "medallion vs lambda", "choose storage",
  "lakehouse vs warehouse", "create architecture", or asks about Fabric
  architecture patterns. Do NOT use for finalizing after review (use
  fabric-finalize), deployment (use fabric-deploy), or discovery (use
  fabric-discover).
metadata:
  author: task-flows-team
  version: 1.0.0
  category: architecture
  tags: [fabric, task-flow, architecture-design, decisions]
  pipeline-phase: 1a-design
  pre-compute: [decision-resolver, handoff-scaffolder]
---

# Fabric Architecture Design

Select the best-fit task flow and walk through architectural decisions to produce a DRAFT Architecture Handoff.

## Instructions

### Step 1: Load Discovery Brief

Read `projects/[name]/prd/discovery-brief.md` for inferred signals, 4V's, and task flow candidates.

If no Discovery Brief exists, ask:
1. Project name
2. Problem statement (volume, velocity, variety, versatility)
3. Team skillset (SQL only / Python+SQL / no-code / mixed)
4. Workspace strategy (single / multi-environment)

### Step 2: Select Task Flow

Choose from 11 task flows + general:

| ID | Best For |
|----|----------|
| basic-data-analytics | Simple batch dashboards |
| medallion | Data quality with bronze/silver/gold layers |
| lambda | Batch + real-time combined |
| event-analytics | Real-time streaming focus |
| event-medallion | Streaming + medallion layers |
| sensitive-data-insights | PII masking, compliance |
| basic-machine-learning-models | ML training, feature engineering |
| data-analytics-sql-endpoint | SQL analytics on unstructured data |
| translytical | Operational writeback, CRUD |
| app-backend | APIs, chatbots, embedded analytics |
| conversational-analytics | Natural language queries via Data Agents |

### Step 3: Walk Through Decision Guides

Read `decisions/_index.md` first. For each decision:
1. Check `quick_decision` in YAML frontmatter — resolve from frontmatter if clear
2. Only read full guide body for edge cases
3. Present decision with rationale

Decisions: Storage → Ingestion → Processing → Visualization → Skillset

### Step 4: Produce DRAFT Architecture Handoff

Write to `projects/[name]/prd/architecture-handoff.md`:

- **YAML frontmatter:** phase, task_flow, deployment_mode
- **Architecture diagram:** ASCII data flow with actual item names
- **Decisions table:** Decision | Outcome | Rationale | Alternatives | Trade-offs
- **Items (YAML):** id, name, type, dependencies
- **Deployment Waves (YAML):** wave number, items, parallel eligibility
- **Acceptance Criteria (YAML):** AC-ID, criterion, type, verification method
- **Alternatives Considered** and **Trade-offs** sections

### Step 5: Write ADRs 001-005

Write sequentially with read-back:
1. `001-task-flow.md` — Task flow selection rationale
2. `002-storage.md` — Storage decision (read 001 first)
3. `003-ingestion.md` — Ingestion decision (read 001+002)
4. `004-processing.md` — Processing decision (read 001-003)
5. `005-visualization.md` — Visualization decision (read 001-004)

Use template from `_shared/adr-template.md`.

## Constraints

- Architecture Handoff: max 220 lines
- YAML fields: max 15 words
- Never deploy or create Fabric items
- Never skip "Alternatives Considered" or "Trade-offs"
- Present both single and multi-workspace options

## Pipeline Handoff

> **⚠️ ORCHESTRATION:** Use `run-pipeline.py advance && next` for phase transitions.

After producing DRAFT, advance to Phase 1b (Review).
