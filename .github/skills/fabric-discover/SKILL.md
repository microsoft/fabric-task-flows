---
name: fabric-discover
description: >
  Infers architectural signals from enterprise data problem statements and
  produces a Discovery Brief. Use when user describes a data problem, mentions
  "IoT sensors", "batch ETL", "real-time analytics", "data warehouse",
  "compliance", "dashboard", "streaming", "we need analytics", or asks
  "what task flow fits my needs", "help me figure out our data architecture",
  or "analyze my problem statement". Do NOT use for architecture design
  decisions (use fabric-design), deployment (use fabric-deploy), or
  validation (use fabric-test).
pre-compute: [signal-mapper]
# author: task-flows-team
# version: 1.0.0
# category: discovery
# tags: [fabric, signal-mapping, discovery, problem-analysis]
# pipeline-phase: 0a-discovery
---

# Fabric Discovery

Infer architectural signals from a user's data problem statement and produce a structured Discovery Brief that the `fabric-design` skill consumes.

## Instructions

### Step 1: Gather Problem Statement

Ask exactly two questions:
1. **Project name** — short, descriptive (e.g., "Energy Field Intelligence")
2. **Problem statement** — what data challenge are you trying to solve?

### Step 2: Run Signal Mapper (Pre-Compute)

If shell is available, the pipeline runner executes:
```bash
python .github/skills/fabric-discover/scripts/signal-mapper.py --text "<problem>" --format json
```
This produces a draft signal table with keyword coverage and task flow candidates.

### Step 3: Infer Signals

Map the problem to the 11 signal categories:

| Category | Velocity | Task Flow Candidates |
|----------|----------|---------------------|
| 1. Real-time / Streaming | Real-time | event-analytics, event-medallion |
| 2. Batch / Scheduled | Batch | basic-data-analytics, medallion |
| 3. Both / Mixed (Lambda) | Both | lambda, event-medallion |
| 4. Machine Learning | Batch (typically) | basic-machine-learning-models |
| 5. Sensitive Data | Varies | sensitive-data-insights |
| 6. Transactional | Real-time | translytical |
| 7. Unstructured / Semi-structured | Batch | data-analytics-sql-endpoint |
| 8. Data Quality / Layered | Varies | medallion |
| 9. Application Backend | Varies | app-backend |
| 10. Document / NoSQL / AI-ready | Varies | app-backend, translytical |
| 11. Semantic Governance | Varies | (governance overlay) |

### Step 4: Assess 4 V's

Only ask about gaps NOT already in the problem statement:

| V | What to Assess |
|---|---------------|
| Volume | Size per load/day |
| Velocity | Batch / near-real-time / real-time |
| Variety | Sources: DBs, files, APIs, streaming |
| Versatility | Low-code / code-first / mixed |

### Step 5: Confirm with User

Present inferred signals and 4V's assessment. Get confirmation or corrections.

### Step 6: Produce Discovery Brief

Write to `_projects/[name]/prd/discovery-brief.md`:

```markdown
## Problem Statement
[user's exact words]

### Inferred Signals
| Signal | Value | Confidence | Source |
| Data Velocity | batch/real-time/both | high/medium/low | quote |

### 4 V's Assessment
| V | Value | Confidence | Source |

### Confirmed with User
- [confirmations/corrections]

### Architectural Judgment Calls
- [design trade-offs requiring architect expertise — max 20 words each]
```

## Constraints

- Discovery Brief: max 60 lines
- Signal table cells: max 15 words
- Architectural Judgment Calls: max 20 words each
- Integration-first: assume coexistence with non-Microsoft platforms unless user says migrate
- Never recommend a final task flow — suggest candidates only
- Never ask about workspace, capacity, CI/CD, or deployment

## Pipeline Handoff

> **⚠️ ORCHESTRATION:** Use `run-pipeline.py advance && next` for phase transitions.

After producing the Discovery Brief, advance the pipeline to Phase 1a (Design).
