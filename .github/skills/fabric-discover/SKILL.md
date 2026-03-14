---
name: fabric-discover
description: >
  Collects intake (project name + problem statement), scaffolds the project,
  infers architectural signals, and produces a Discovery Brief. Use when user
  describes a data problem, mentions "IoT sensors", "batch ETL", "real-time
  analytics", "data warehouse", "compliance", "dashboard", "streaming",
  "we need analytics", or asks "what task flow fits my needs". Do NOT use
  for architecture design (use fabric-design), deployment (use fabric-deploy),
  or validation (use fabric-test).
pre-compute: [signal-mapper]
---

# Fabric Discovery

## Instructions

### Step 1: Collect Intake

If the problem statement and project name are **already provided in the agent prompt** (e.g., from a pipeline re-run or auto-chain), use them directly — do NOT re-ask the user.

Otherwise, ask the user for:
- **Project name** — Ask for a short, creative, and descriptive name. You MAY suggest examples (e.g., "Farm Fleet", "Energy Analytics"), but you MUST NOT proceed until the user explicitly provides or confirms a name. Never infer, synthesize, or assume a project name from context.
- **Problem statement** — "What problems does your project need to solve?"

### Step 2: Scaffold the Project

Once you have both, run:
```bash
python _shared/scripts/run-pipeline.py start "Project Name" --problem "problem statement text"
```

### Step 3: Review Signal Mapper Output

Review the signal mapping output from the `start` command.

### Step 4: Assess 4 V's Gaps

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

If the output shows `🟢 AUTO-CHAIN → <skill>`, **invoke that skill immediately** — do NOT stop and ask the user.
Only `🛑 HUMAN GATE` (Phase 2b sign-off) requires user action.
