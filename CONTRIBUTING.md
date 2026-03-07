# Contributing to Task Flows

## Adding a new task flow

1. Add an H2 section to `task-flows.md` following the existing structure: description, task count, ASCII flow diagram, workloads, items, decision table with links, and diagram/validation links.
2. Create `diagrams/{task-flow-id}.md` with phased deployment flow using the symbols from `_shared/legend.md` (`[LC]`/`[CF]` skillset tags, `──►` flow, `OR` for choices).
3. Create `validation/{task-flow-id}.md` with a post-deployment manual steps table and a phase-by-phase checklist (Foundation → Environment → Ingestion → Transformation → Visualization → ML).
4. Update `diagrams/_index.md` and `validation/_index.md` with the new entry.
5. Run `python scripts/new-project.py` to verify scaffolding works with the new task flow.

## Adding a decision guide

1. Create `decisions/{guide-id}.md` with YAML frontmatter: `id`, `title`, `description`, `triggers` (routing phrases), `options` (structured criteria), and `quick_decision` (compact decision tree for fast agent resolution).
2. Add a row to `decisions/_index.md`.
3. Update the decision guides table in `README.md`.

## Diagram conventions

Deployment diagrams use ASCII box-drawing characters with phased sections separated by `═════`. Skillset tags (`[LC]`, `[CF]`, `[LC/CF]`) annotate each item. Decision points use `OR` blocks with differentiator comparison tables. Add `<!-- AGENT: Skip to "## Deployment Order" -->` before the ASCII art section.

## Validation checklist structure

Every validation file starts with a "Post-Deployment Manual Steps" table (Item Type → Manual Action Required), followed by phased checklists using `- [ ]` checkboxes. Phases follow the standard order: Foundation, Environment, Ingestion, Transformation, Visualization, ML (if applicable).

## Scripts

The `scripts/` directory contains pipeline utilities. Key scripts:

| Script | Purpose |
|--------|---------|
| `new-project.py` | Scaffolds a new project with all template files + `pipeline-state.json` |
| `run-pipeline.py` | Pipeline orchestrator — `start`, `next`, `status`, `advance`, `reset` commands |
| `deploy-script-gen.py` | Reads architecture handoff YAML, generates `.ps1` and `.sh` deploy scripts |
| `signal-mapper.py` | Maps problem signals to task flow candidates |
| `decision-resolver.py` | Resolves decision guide YAML frontmatter for agents |
| `review-prescan.py` | Pre-scans architecture handoff for review flags |
| `test-plan-prefill.py` | Prefills test plan from acceptance criteria |
| `validate-items.ps1/.sh` | Runs `fab exists` per deployed item, outputs validation YAML |
| `taskflow-gen.py` | Generates Fabric workspace task flow JSON for import |
| `handoff-scaffolder.py` | Pre-fills handoff template YAML from diagram metadata |
| `sync-item-types.py` | Syncs `_shared/item-type-registry.json` against installed Fabric CLI |
| `generate-ps1-types.py` | Regenerates PowerShell item-type constants in `validate-items.ps1` from registry |
| `registry_loader.py` | Shared module — all scripts import item type metadata from here |

> ⚠️ **Enforcement:** These scripts are NOT optional helpers — they are mandatory pre-compute steps. See `_shared/agent-boundaries.md` for the MUST/MUST NOT rules that govern when and how agents use each script.

## Deploy script templates

The deploy script templates (`_shared/script-template.ps1` and `_shared/script-template.sh`) use `{{PLACEHOLDER}}` tokens filled by `deploy-script-gen.py`. Template features:

- **`Fab-Mkdir` / `fab_mkdir` wrapper** — Adds idempotency (`fab exists` check), retry with backoff (3 attempts), and result tracking
- **Preflight check** — Verifies `fab` CLI is installed before proceeding
- **Workspace auto-creation** — Creates workspace if it doesn't exist
- **Deployment summary** — Final ✅/⏭️/❌ report per item
- **Brand banner** — `print_banner` / `Print-Banner` function embedded in each template (single source of truth)

Only **workspace name** is prompted by the script (with env var fallback). Authentication, capacity, and tenant are delegated to the `fab` CLI.

## Pipeline state

Each project has a `pipeline-state.json` (scaffolded by `new-project.py`) that tracks which phase is current, which phases are complete, and whether transitions are automatic or require human approval. The `run-pipeline.py` script manages this file.

## ADR write-through

Architecture Decision Records (ADRs) are written by the `@fabric-architect` during Phase 1a (DRAFT) and refined during Phase 1c (FINAL) — not deferred to Phase 4 (Documentation). This ensures:

- Reviewers in Phase 1b can reference the full decision rationale
- The "why" behind each decision is captured while context is fresh
- The `@fabric-documenter` polishes language and adds cross-links rather than writing ADRs from scratch

The 5 standard ADR files (`docs/decisions/001-task-flow.md` through `005-visualization.md`) are scaffolded by `new-project.py`. The architect fills them using the format from `_shared/adr-template.md`.

## Agent boundaries

Agents operate under strict deterministic-vs-reasoning boundaries. **Every pipeline phase has a pre-compute script that MUST run before the LLM adds judgment.** See `_shared/agent-boundaries.md` for the complete enforcement rules.

Key rules:
- **MUST** use `run-pipeline.py` to orchestrate — not ad-hoc agent chaining
- **MUST** run pre-compute scripts before LLM reasoning (e.g., `signal-mapper.py` before discovery, `review-prescan.py` before review, `deploy-script-gen.py` before deploy)
- **MUST** use `_shared/schemas/` for all handoff output format
- **MUST NOT** hand-write deployment scripts, handoff YAML structure, or pipeline state
- **MUST NOT** skip pre-compute steps even if the LLM "knows" the answer

> **Core principle:** If it's reproducible across 1,000 projects, a script does it — not an agent.

## Agent conventions

### ORCHESTRATION — Pipeline Runner

All six agent files (`.github/agents/fabric-*.agent.md`) include an `⚠️ ORCHESTRATION` block in their Pipeline Handoff section. This instructs agents to use `run-pipeline.py advance && run-pipeline.py next` for all phase transitions — **never** manually chain to another agent via `AUTO-CHAIN` or ask "Want me to continue?". The runner manages `pipeline-state.json`, verifies output files, runs pre-compute scripts, and enforces the human gate at Phase 2b.

> ⚠️ **Bypassing the runner** (e.g., calling `new-project.py` directly, manually editing `pipeline-state.json`, or telling agents to invoke each other) leaves pipeline state stale and breaks phase tracking.

### Agent tool lists

Keep the `tools:` frontmatter in each agent file synchronized with the agent table in `.github/copilot-instructions.md`.

## Script generation

All generated scripts (deploy, validation, rollback) MUST display the branded banner as the first thing the user sees. The `print_banner` (bash) and `Print-Banner` (PowerShell) functions in the script templates are the **single source of truth** for the banner. Agents copy the function from the matching template into each generated script so scripts remain self-contained.

### Banner placeholders

| Placeholder | Source | Example |
|-------------|--------|---------|
| `{PROJECT_NAME}` | Architecture Handoff → project name | `Energy Field Intelligence` |
| `{TASK_FLOW}` | Architecture Handoff → task flow ID | `medallion` |
| `{MODE}` | Script purpose | `Deploy to Fabric`, `Validation`, `Rollback` |

### Rules

- Copy the banner function from `_shared/script-template.sh` or `_shared/script-template.ps1` — do not maintain a separate banner file
- The `mode` parameter should reflect the script's purpose
- If the banner design changes, update only the two template files

## Git workflow

When agents create or modify files in `projects/`:
- **Commit messages:** Use the format `[project-name] action description`
- **One project per commit:** Don't mix changes across different projects
- **Never commit secrets:** Use environment variables or parameter placeholders
