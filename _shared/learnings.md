# Fabric CLI Operational Learnings

> Operational knowledge captured by `@fabric-engineer` and `@fabric-tester` during deployments and validations. This file is a living document — agents append learnings as they encounter new patterns, gotchas, and workarounds.

<!-- INSTRUCTIONS FOR AGENTS:
  - Append new learnings under the appropriate section heading
  - Keep each entry to 1-2 sentences
  - Include the item type and context
  - Do NOT delete existing entries unless they are confirmed obsolete
  - Periodically consolidate duplicate or redundant entries
-->

## Pipeline Orchestration

- **Always use `run-pipeline.py`** to start projects and advance phases. Calling `new-project.py` directly or manually chaining agents bypasses state tracking, skips pre-compute scripts (signal-mapper, review-prescan, etc.), and leaves `pipeline-state.json` stale — causing the pipeline to lose its place.
- **Never edit `pipeline-state.json` directly.** The runner owns state transitions, output verification, and human gate enforcement. Agents write to `prd/` files only.

## Deployment

<!-- @fabric-engineer appends learnings here after deployment phases -->

- **Mirrored SQL Server Database has no `fab mkdir` support.** Must create via Fabric Portal; document as manual step M-1 with guided portal instructions in deploy scripts.
- **Environment publish delay requires explicit wait.** Add interactive confirmation prompt in deploy scripts between Environment creation and Notebook binding to prevent attachment failures.

## Validation

<!-- @fabric-tester appends learnings here after validation phases -->

## Timing & Propagation

<!-- Learnings about delays, propagation, and ordering constraints -->

## Common Gotchas

<!-- Recurring issues that trip up deployments across projects -->
