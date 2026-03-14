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

## Guardrails: Project Scaffolding is a Hard Gate

**This skill depends on project scaffolding via `run-pipeline.py start`.**

- ❌ Do NOT run `signal-mapper.py` without `--project` pointing to a valid scaffolded project
- ❌ Do NOT bypass the `start` command — the user MUST provide a project name first
- ✅ `signal-mapper.py` enforces this at the code level and will exit with an error if no valid project exists
- ✅ Use `--intake` flag only for standalone signal exploration outside the pipeline

If signal-mapper.py fails with "Project not found", scaffold the project first:
```bash
python _shared/scripts/run-pipeline.py start "Your Project Name" --problem "Your problem statement"
```

## Instructions

> **Input from orchestrator:** Project name and problem statement are passed via `run-pipeline.py start`. Do NOT re-ask for these.

### Step 1: Review Signal Mapper Output

The pipeline runner pre-computed signal mapping. Review the output in the prompt or run:
```bash
python .github/skills/fabric-discover/scripts/signal-mapper.py --project <project-name> --text "<problem>" --format json
```

### Step 2: Assess 4 V's Gaps

Only ask about gaps NOT already in the problem statement:

| V | What to Assess |
|---|---------------|
| Volume | Size per load/day |
| Velocity | Batch / near-real-time / real-time |
| Variety | Sources: DBs, files, APIs, streaming |
| Versatility | Low-code / code-first / mixed |

### Step 3: Confirm with User

Present inferred signals and 4V's assessment. Get confirmation or corrections.

### Step 4: Produce Discovery Brief

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

- Do NOT read `signal-categories.json` directly — use `signal-mapper.py`
- Discovery Brief: max 60 lines
- Signal table cells: max 15 words
- Architectural Judgment Calls: max 20 words each
- Integration-first: assume coexistence unless user says migrate
- Never recommend a final task flow — suggest candidates only

## Handoff

After producing the output file, advance:
```bash
python _shared/scripts/run-pipeline.py advance --project <project-name> -q
```
