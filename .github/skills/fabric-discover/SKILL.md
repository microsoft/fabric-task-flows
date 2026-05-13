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
---

# Fabric Discovery

## Instructions

### Step 1: Collect Intake

If the problem statement and project name are already provided (e.g., from auto-chain), use them directly — do NOT re-ask.

Otherwise, ask the user for:
- **Project name** — short, creative, descriptive. You MAY suggest examples, but MUST NOT proceed until the user explicitly confirms one.
- **Problem statement** — "What problems does your project need to solve?"

### Step 2: Scaffold and Review Signals

```bash
python _shared/scripts/run-pipeline.py start "Project Name" --problem "problem statement text"
```

The `start` command runs `signal-mapper.py` as pre-compute — review its output above. Do NOT run `signal-mapper.py` again manually.

### Step 3: Close 4 V's Gaps (loop until confidence floor met)

For each V **not already stated in the problem statement**, ask the user one at a time via `ask_user`. Do NOT proceed to Step 4 with any V still unknown.

| V | What to Assess |
|---|---------------|
| Volume | Size per load/day |
| Velocity | Batch / near-real-time / real-time |
| Variety | Sources: DBs, files, APIs, streaming |
| Versatility | Low-code / code-first / mixed |

If the signal mapper generated follow-up questions, use them as templates.

Once all four V's are resolved, persist them:

```bash
python .github/skills/fabric-discover/scripts/intake-writer.py \
  --project <project> \
  --volume "<value>"       --volume-source user|inferred \
  --velocity "<value>"     --velocity-source user|inferred \
  --variety "<value>"      --variety-source user|inferred \
  --versatility "<value>"  --versatility-source user|inferred
```

Use `--*-source user` when the user stated the value, `inferred` when they deferred to your best guess. If `confidence_floor_met` is false in the output, loop back and ask more questions.

### Step 4: Render the Deterministic Discovery Summary

```bash
python _shared/scripts/run-pipeline.py discovery-summary --project <project>
```

Copy-paste the **entire** rendered block into your chat response as a fenced code block — the user cannot see tool output directly.

After the block, `ask_user` with three choices:
- **Confirm** — proceed to write the Discovery Brief (Step 5).
- **Correct** — capture corrections; re-run `intake-writer.py` with updated values, then re-render.
- **Restart** — abandon and re-collect the problem statement.

### Step 5: Produce Discovery Brief

Write to `_projects/[name]/docs/discovery-brief.md` (file is pre-scaffolded — replace full content via `edit` tool):

```markdown
## Problem Statement
[user's exact words]

### Inferred Signals
| Signal | Value | Confidence | Source |

### 4 V's Assessment
| V | Value | Confidence | Source |

### Confirmed with User
- [confirmations/corrections]

### Architectural Judgment Calls
- [max 20 words each]
```

## Constraints

- Use `signal-mapper.py` for all signal lookups — do not access registry files directly
- Use `intake-writer.py` to persist 4 V's — do not hand-edit `.discovery-intake.json`
- Step 4 recap MUST be rendered via `run-pipeline.py discovery-summary` — never improvise the block
- Discovery Brief: max 60 lines
- Signal table cells: max 15 words
- Architectural Judgment Calls: max 20 words each
- Integration-first: assume coexistence unless user says migrate
- Never recommend a final task flow — suggest candidates only
