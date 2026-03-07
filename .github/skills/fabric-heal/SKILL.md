---
name: fabric-heal
description: >
  Self-healing skill that improves signal mapper keyword coverage through
  iterative problem generation and keyword patching. Use when user says
  "heal signal mapper", "improve keyword coverage", "generate problem
  statements", "run healing loop", "patch signal mapper", or asks about
  "signal mapper gaps". Do NOT use for project architecture or deployment.
# author: task-flows-team
# version: 1.0.0
# category: maintenance
# tags: [fabric, self-healing, signal-mapper, keywords]
# pipeline-phase: standalone
---

# Fabric Signal Mapper Healer

Improve the signal mapper's keyword coverage through iterative problem generation and keyword patching. Invoked by `heal-orchestrator.py`.

## Mode 1: Generate Problem Statements

**Trigger:** Orchestrator passes `--mode generate --batch-num N`.

Write 25 novel problem statements to `problem-statements.md` (in this skill's folder).

### Requirements Per Problem

1. **Realistic** — sounds like an actual enterprise user
2. **Specific** — data volumes, team sizes, tool names, deadlines, compliance
3. **Multi-signal** — touches 2-3 signal categories naturally
4. **Domain-diverse** — industries underrepresented in existing keywords
5. **Varying complexity** — simple to complex mix

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

**Trigger:** Orchestrator passes `--mode heal` with benchmark results.

### Input

Coverage %, zero-candidate count, uncovered terms list.

### Process

1. Map uncovered terms to signal categories (1-11)
2. Edit `scripts/signal-mapper.py` keyword tuples via `edit` tool
3. Log changes to `_shared/learnings.md` under "## Healing History"

### Constraints

- Max 15 new keywords per category per iteration
- Never remove existing keywords
- Never modify the matching algorithm
- Prefer specific terms over generic ones

## References

- `scripts/signal-mapper.py` — current keyword categories
- `problem-statements.md` — existing format (in this skill's folder)
- `_shared/learnings.md` — healing history
- `task-flows.md` — task flow descriptions
