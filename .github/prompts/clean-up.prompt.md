---
name: clean-up
description: Compact audit for code, instructions, and process
agent: agent
---

Use /grill-with-docs and /superpowers:receiving-code-review to conduct a brutally honest audit of this codebase, its instructions, and associated engineering processes.

Goal: reduce complexity without changing behavior.
Assume flaws exist; keep nothing by habit.

Check:
- Verbose instructions
- Contradictions and unclear guidance
- Redundancy, dead code, duplication
- Unneeded abstraction/indirection
- Fragile or over-complex implementations
- Process vs usage gaps

Output (required):
1. Core Problems
- What is wrong, unclear, or inefficient

2. Redundancy and Bloat
- What to remove, merge, or simplify, with examples

3. Contradictions and Confusion
- Where guidance or patterns conflict or mislead

4. Bugs and Risks
- Found issues and likely failure points

5. Streamlining Opportunities
- Where simpler patterns replace complex ones

6. Recommended Changes (Action Plan)
- Prioritized, concrete steps

7. Skills and Process Re-evaluation
- What to keep, replace, or redesign

Constraints:
- Prefer clarity over completeness
- Prefer simplicity over flexibility
- Prefer explicitness over abstraction
- Preserve functionality; challenge everything else