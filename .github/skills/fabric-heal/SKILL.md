---
name: fabric-heal
description: >
  Self-healing skill that improves signal mapper keyword coverage through
  iterative problem generation and keyword patching. Use when user says
  "heal signal mapper", "improve keyword coverage", "generate problem
  statements", "run healing loop", "patch signal mapper", or asks about
  "signal mapper gaps". Do NOT use for project architecture or deployment.
---

# Fabric Signal Mapper Healer

## Mode 1: Generate Problem Statements

Orchestrator passes `--mode generate --batch-num N`. Write 25 novel problem statements to `problem-statements.md`.

### Requirements

Realistic (enterprise user), specific (volumes/tools/deadlines), multi-signal (2-3 categories), domain-diverse, varying complexity.

### Output Format (parser-dependent)

```markdown
# Problem Statements for Stress Testing

> Auto-generated batch N — 25 problems for self-healing loop.

## Category Name

1. "Problem statement text in quotes."

2. "Another problem in same category."
```

Use 5-8 categories per batch, 3-5 problems per category.

## Mode 2: Analyze Gaps and Patch Keywords

Orchestrator passes `--mode heal` with benchmark results (coverage %, zero-candidate count, uncovered terms).

1. Map uncovered terms to signal categories (1-11)
2. Update `_shared/registry/signal-categories.json` using `signal-categories-cli.py` (max 15 new keywords per category per iteration)
3. Log changes to `_shared/learnings.md`

## Orchestrator Reporting (Verbose Distribution)

`heal-orchestrator.py` prints a verbose, deterministic distribution report with ASCII bar charts:

- Task flow suggestion rate
- Top candidate distribution
- Pattern-category distribution (batch/streaming/hybrid/governance/app-api)
- Skillset distribution (LC/CF/mixed tendencies)
- Item type frequency across suggested flows
- Recommendations derived from benchmark thresholds and recurring uncovered terms

Detailed analytics are persisted to:

- `.github/skills/fabric-heal/scripts/_heal-loop-results.json`

### Constraints

- Use `signal-mapper.py` for all signal lookups.
- For keyword maintenance, use `_shared/scripts/signal-categories-cli.py` (add/remove/move/list) instead of manual raw JSON edits.
- Never remove existing keywords or modify the matching algorithm
- Clean up generated files: delete `problem-statements-batch*.md` after each loop completes
- Prefer specific terms over generic ones

## References

- `.github/skills/fabric-discover/scripts/signal-mapper.py` — current keyword categories
- `_shared/scripts/signal-categories-cli.py` — safe keyword maintenance helper for signal categories registry
- `problem-statements.md` — existing format (in this skill's folder)
- `_shared/learnings.md` — healing history
- `task-flows.md` — task flow descriptions
