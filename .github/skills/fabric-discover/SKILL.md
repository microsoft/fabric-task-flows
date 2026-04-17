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

> **⚠️ The `start` command already runs signal-mapper as pre-compute. Read the output above — do NOT run `signal-mapper.py` again manually.**

### Step 4: Close 4 V's Gaps (loop until confidence floor met)

For each V that is **not already stated in the problem statement**, ask the user
**one at a time** via `ask_user`. Continue asking until every V has either a
concrete user-stated value OR the user has explicitly told you to use your
inferred best guess. **Do NOT proceed to Step 5 with any V still unknown.**

| V | What to Assess |
|---|---------------|
| Volume | Size per load/day |
| Velocity | Batch / near-real-time / real-time |
| Variety | Sources: DBs, files, APIs, streaming |
| Versatility | Low-code / code-first / mixed |

If the signal mapper generated follow-up questions (via `--intake` mode or
low-coverage advisory), use them as question templates.

Once all four V's are resolved, persist the confirmed values:

```bash
python .github/skills/fabric-discover/scripts/intake-writer.py \
  --project <project> \
  --volume "<value>"       --volume-source user|inferred \
  --velocity "<value>"     --velocity-source user|inferred \
  --variety "<value>"      --variety-source user|inferred \
  --versatility "<value>"  --versatility-source user|inferred
```

Use `--*-source user` when the user stated the value outright, `inferred` when
the user deferred to your best guess. Omit (or pass empty string) for anything
still unknown — but the writer will warn if `confidence_floor_met` is false,
which means you must loop back and ask more questions.

### Step 5: Render the Deterministic Discovery Summary

Run the deterministic renderer — this reads `.signal-mapper-cache.json` and
`.discovery-intake.json` and prints a stable, stakeholder-facing recap:

```bash
python _shared/scripts/run-pipeline.py discovery-summary --project <project>
```

**You MUST copy-paste the ENTIRE rendered block into your chat response as a
fenced code block (```).** The user cannot see tool output directly — your
response text is the only thing they see. Do not abbreviate, summarize, or
paraphrase the block.

After the block, issue a single `ask_user` with three choices:

- **Confirm** — proceed to write the Discovery Brief (Step 6).
- **Correct** — capture free-text corrections; re-run `intake-writer.py` with
  the updated values, then re-render (Step 5 again).
- **Restart** — abandon and re-collect the problem statement.

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
- Use `intake-writer.py` to persist 4 V's — do not hand-edit `.discovery-intake.json`
- Step 5 recap MUST be rendered via `run-pipeline.py discovery-summary` — never improvise the block
- Discovery Brief: max 60 lines
- Signal table cells: max 15 words
- Architectural Judgment Calls: max 20 words each
- Integration-first: assume coexistence unless user says migrate
- Never recommend a final task flow — suggest candidates only

## Handoff

> Handoff: see [`_shared/workflow-guide.md`](../../../_shared/workflow-guide.md#handoff) — call `run-pipeline.py advance -q` after writing the output file; AUTO-CHAIN unless a HUMAN GATE fires.
