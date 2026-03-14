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
2. Edit `signal-mapper.py` keyword tuples (max 15 new per category per iteration)
3. Log changes to `_shared/learnings.md`

### Constraints

- Do NOT read `signal-categories.json` directly — use `signal-mapper.py` (69 KB of raw JSON wastes context)
- Never remove existing keywords or modify the matching algorithm
- Clean up generated files: delete `problem-statements-batch*.md` after each loop completes
- Prefer specific terms over generic ones

## References

- `.github/skills/fabric-discover/scripts/signal-mapper.py` — current keyword categories
- `problem-statements.md` — existing format (in this skill's folder)
- `_shared/learnings.md` — healing history
- `task-flows.md` — task flow descriptions
