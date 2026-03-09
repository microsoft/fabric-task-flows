---
name: fabric-design
description: >
  The Architect skill — designs Microsoft Fabric architectures, reviews drafts
  for feasibility and testability, and finalizes based on feedback. Use when
  user says "design architecture", "which task flow", "medallion vs lambda",
  "review DRAFT", "finalize architecture", "incorporate feedback", or asks
  about Fabric architecture patterns. Do NOT use for deployment (use
  fabric-deploy), testing (use fabric-test), or discovery (use
  fabric-discover).
pre-compute: [decision-resolver, handoff-scaffolder, review-prescan]
# author: task-flows-team
# version: 2.0.0
# category: architecture
# tags: [fabric, task-flow, architecture-design, review, decisions]
# pipeline-phases: [1a-design, 1b-review, 1c-finalize]
---

# Fabric Architecture Design (Architect Role)

Covers the full architect lifecycle: design the DRAFT, review it, finalize it.

## Mode 1: DRAFT Design (Phase 1a)

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

### Step 3: Walk Through Decision Guides

Read `decisions/_index.md` first. For each decision:
1. Check `quick_decision` in YAML frontmatter — resolve from frontmatter if clear
2. Only read full guide body for edge cases
3. Present decision with rationale

Decisions: Storage → Ingestion → Processing → Visualization → Skillset

> **⚠️ Visualization terminology:** When users say "dashboard", map to **Report** (batch) or **Real-Time Dashboard** (streaming with Eventhouse). In Fabric, "Dashboard" only means Real-Time Dashboard — an RTI item for sub-second streaming. Power BI Reports serve the "dashboard" use case for batch data.

### Step 3b: Parameterization Decision (Multi-Environment Only)

If the user selected **multi-environment** workspace strategy (Dev/PPE/Prod):
1. Read `decisions/parameterization-selection.md` — use `quick_decision` in frontmatter
2. **Variable Library** is preferred for Fabric-native CI/CD with runtime item references
3. If Variable Library is chosen, add it as a **Wave 1 item** (foundation) — it must exist before consuming items (Notebooks, Pipelines, Shortcuts)
4. Define variables for: workspace-specific Lakehouse IDs, connection strings, environment names, capacity settings
5. Create value sets per deployment stage (Dev, PPE, Prod)
6. Record the choice in the Deployment Strategy table of the architecture handoff

If the user selected **single environment**, default to Environment Variables and skip this step.

### Step 4: Produce DRAFT Architecture Handoff

Write to `projects/[name]/prd/architecture-handoff.md`:

- **YAML frontmatter:** phase, task_flow, deployment_mode
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

## Mode 2: Review DRAFT (Phase 1b)

Perform BOTH deployment feasibility AND testability review in a single pass.

### Step 1: Load Context (Read Each File ONCE)

1. `projects/[name]/prd/architecture-handoff.md` — the DRAFT
2. `diagrams/[task-flow].md` — skip to `## Deployment Order`
3. `_shared/item-type-registry.json` — REST API creation support per item type
4. `validation/[task-flow].md` — task-flow-specific validation checklist

### Step 2: Engineer Review (Deployment Feasibility)

Assess: dependency graph, per-item gotchas, wave optimization, prerequisites, CLI commands.

### Step 3: Tester Review (Testability)

Assess: AC specificity, test coverage, untestable criteria, edge cases, CLI syntax.

### Step 4: Write Both Reviews

1. **Engineer Review** → `projects/[name]/prd/engineer-review.md` (schema: `schemas/engineer-review.md`)
2. **Tester Review** → `projects/[name]/prd/tester-review.md` (schema: `schemas/tester-review.md`)

Set `review_outcome`: ANY red → `revise`, NO red → `approved`.

---

## Mode 3: Finalize (Phase 1c)

Incorporate review feedback into the DRAFT to produce the FINAL handoff.

### Step 1: Read Reviews

Load `projects/[name]/prd/engineer-review.md` and `projects/[name]/prd/tester-review.md`.

### Step 2: Address Findings

- `severity: red` → address the concern, update items/waves/ACs
- `severity: yellow` → document acknowledgment and mitigation

### Step 3: Update Architecture Handoff

1. Add `## Design Review` section with table: Finding | Severity | Action Taken
2. Update items/waves/ACs if design changed
3. Change phase from `DRAFT` to `FINAL` in frontmatter

### Step 4: Update ADRs if decisions changed

Max 3 review iterations. After 3 cycles, proceed to FINAL regardless.

---

## Constraints

- Architecture Handoff: max 220 lines
- YAML fields: max 15 words
- Review fields: max 15 words
- Never deploy or create Fabric items
- Never skip "Alternatives Considered" or "Trade-offs"
- Read each reference file ONCE during review

## Pipeline Handoff

> **⚠️ ORCHESTRATION:** Use `run-pipeline.py advance && next` for phase transitions.
