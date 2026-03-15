---
name: fabric-discover
description: >
  Collects intake (project name + problem statement), scaffolds the project,
  infers architectural signals, and produces a Discovery Brief. This is the
  DEFAULT first skill — invoke it for ANY new user request that describes a
  data, analytics, reporting, or integration problem, no matter how it is
  phrased. The signal mapper handles keyword matching; routing just needs to
  get the user here first. When in doubt, invoke fabric-discover — a
  false-positive intake is recoverable; a freelanced answer is not. Common
  triggers include "IoT sensors", "batch ETL", "real-time analytics", "data
  warehouse", "compliance", "dashboard", "streaming", "we need analytics",
  or "what task flow fits my needs", but any description of a data problem
  qualifies. Do NOT use for architecture design (use fabric-design),
  deployment (use fabric-deploy), or validation (use fabric-test).
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

Present inferred signals **and all 4 V's** conversationally. Get confirmation or corrections.

**You MUST present all 4 V's explicitly — no exceptions:**

1. **Volume** — data size (e.g., "looks like small daily loads under 10 GB")
2. **Velocity** — timing (e.g., "daily batch refresh, not real-time")
3. **Variety** — sources (e.g., "two sources: Square API and your accounting CSV")
4. **Versatility** — skill level (e.g., "low-code approach since your team prefers drag-and-drop")

Example confirmation message:
> *"Here's what I'm seeing from your problem statement:*
> - **Volume:** Small data — daily loads under 10 GB
> - **Velocity:** Batch — you mentioned end-of-day processing
> - **Variety:** Two sources — Square POS and your accounting exports
> - **Versatility:** Low-code — your team wants minimal scripting
>
> *Does that match your situation, or should I adjust anything?"*

**Presentation rules — the user is a business stakeholder:**

- Use **plain-language bullets** — NOT markdown tables (tables go only in the handoff file).
- Use the user's own language: "your Square sales data" not "API-based ingestion pattern."
- If a V is unknown or ambiguous, **ask** — don't skip it or guess.

### Step 6: Produce Discovery Brief

Write to `_projects/[name]/docs/discovery-brief.md`:

> **File editing:** This file is pre-scaffolded with placeholder content. Replace the **entire file contents** using the `edit` tool — use the full existing file as `old_str` and the completed brief as `new_str`. Do NOT use `create` (the file already exists) or pass an empty `old_str`.

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

- Use `signal-mapper.py` for all signal lookups — do not access registry files directly
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
