---
name: fabric-design
description: >
  The Architect skill — designs Microsoft Fabric architectures and produces
  the FINAL architecture handoff. Use when user says "design architecture",
  "which task flow", "medallion vs lambda", "create architecture", or asks
  about Fabric architecture patterns. Do NOT use for deployment (use
  fabric-deploy), testing (use fabric-test), or discovery (use
  fabric-discover).
pre-compute: [decision-resolver, handoff-scaffolder]
# author: task-flows-team
# version: 3.0.0
# category: architecture
# tags: [fabric, task-flow, architecture-design, decisions]
# pipeline-phases: [1-design]
---

# Fabric Architecture Design (Architect Role)

## Phase 1-design: Architecture Design

### Step 1: Load Discovery Brief

Read `_projects/[name]/prd/discovery-brief.md` for inferred signals, 4V's, and task flow candidates.

If no Discovery Brief exists, ask:
1. Project name
2. Problem statement (volume, velocity, variety, versatility)
3. Team skillset (SQL only / Python+SQL / no-code / mixed)
4. Workspace strategy (single / multi-environment)

### Step 2: Select Task Flow

Choose from 11 task flows + general:

| ID | Best For |
|----|----------|
| basic-data-analytics | Simple batch analytics + reports |
| medallion | Data quality with bronze/silver/gold layers |
| lambda | Batch + real-time combined |
| event-analytics | Real-time streaming focus |
| event-medallion | Streaming + medallion layers |
| sensitive-data-insights | PII masking, compliance |
| basic-machine-learning-models | ML training, feature engineering |
| data-analytics-sql-endpoint | SQL analytics on unstructured data |
| translytical | Operational writeback, CRUD |
| app-backend | APIs, Data Agents, embedded analytics |
| conversational-analytics | Natural language queries via Data Agents |

### Step 3: Resolve Architectural Decisions

Run `decision-resolver.py` to resolve all 7 decisions programmatically from Discovery Brief signals:

```bash
python .github/skills/fabric-design/scripts/decision-resolver.py --signals-file _projects/[name]/prd/discovery-brief.md --format yaml
```

Returns structured output: `choice`, `confidence`, `rule_matched`, and `guide` reference for each decision (storage, ingestion, processing, visualization, skillset, parameterization, api).

- **High confidence** → accept the choice, present with rationale
- **Ambiguous** → read the referenced `guide` file's comparison table to resolve, then present trade-offs to user
- **Unresolved** → ask user for clarifying input

> **⚠️ Do NOT read decision guide files directly.** Use `decision-resolver.py` — it encodes the same rules as `quick_decision` YAML frontmatter. Only read a guide body for ambiguous cases needing comparison tables.

> **Visualization terminology:** "dashboard" → **Report** (batch) or **Real-Time Dashboard** (streaming/Eventhouse).

### Step 3b: Parameterization (Multi-Environment Only)

If multi-environment: the resolver output includes a `parameterization` decision. If Variable Library is chosen, add it as a **Wave 1 item** — it must exist before consuming items. Define variables for Lakehouse IDs, connection strings, environment names. Create value sets per stage.

Single environment → default to Environment Variables, skip this step.

### Step 4: Produce FINAL Architecture Handoff

Write to `_projects/[name]/prd/architecture-handoff.md`:

- **YAML frontmatter:** phase: FINAL, task_flow, deployment_mode
- **Architecture diagram:** ASCII data flow with actual item names
- **Decisions table:** Decision | Outcome | Rationale | Alternatives | Trade-offs
- **Items (YAML):** id, name, type, dependencies — include Variable Library if multi-env
- **Deployment Waves (YAML):** wave number, items, parallel eligibility — Variable Library in Wave 1
- **Acceptance Criteria (YAML):** AC-ID, criterion, type, verification method
- **Alternatives Considered** and **Trade-offs** sections

### Step 5: Write ADRs 001-005

Write sequentially with read-back (use `references/adr-template.md`):
1. `001-task-flow.md` — Task flow selection rationale
2. `002-storage.md` — Storage decision (read 001 first)
3. `003-ingestion.md` — Ingestion decision (read 001+002)
4. `004-processing.md` — Processing decision (read 001-003)
5. `005-visualization.md` — Visualization decision (read 001-004)

---

## Constraints

- Architecture Handoff: max 220 lines
- YAML fields: max 15 words
- Never deploy or create Fabric items
- Never skip "Alternatives Considered" or "Trade-offs"
- Produce FINAL directly — the Tester reviews at Phase 2a

## Pipeline Handoff

After design → Phase 2a (Test Plan + Review by QA).
