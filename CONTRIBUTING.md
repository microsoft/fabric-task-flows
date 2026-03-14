# Contributing to Task Flows

## Adding a new task flow

1. Add an H2 section to `task-flows.md` following the existing structure: description, task count, ASCII flow diagram, workloads, items, decision table with links, and diagram link.
2. Create `diagrams/{task-flow-id}.md` with phased deployment flow using the symbols from `legend.md` (`[LC]`/`[CF]` skillset tags, `──►` flow, `OR` for choices).
3. Add the task flow entry to `_shared/registry/validation-checklists.json` with manual_steps, phases, and checklist items.
4. Update `diagrams/_index.md` with the new entry.
5. Run `python _shared/scripts/new-project.py` to verify scaffolding works with the new task flow.

## Adding a decision guide

1. Create `decisions/{guide-id}.md` with YAML frontmatter: `id`, `title`, `description`, `triggers` (routing phrases), `options` (structured criteria), and `quick_decision` (compact decision tree for fast agent resolution).
2. Add a row to `decisions/_index.md`.
3. Update the decision guides table in `README.md`.

## Diagram conventions

Deployment diagrams use ASCII box-drawing characters with phased sections separated by `═════`. Skillset tags (`[LC]`, `[CF]`, `[LC/CF]`) annotate each item. Decision points use `OR` blocks with differentiator comparison tables. Add `<!-- AGENT: Skip to "## Deployment Order" -->` before the ASCII art section.

## Validation checklist structure

Validation data is consolidated in `_shared/registry/validation-checklists.json`. Each task flow entry contains:
- `manual_steps` — per-item-type actions requiring human configuration
- `phases` — ordered validation stages with detailed checklist items
- `has_shared_ai_governance` — whether to use the shared AI governance checklist

Phases follow the standard order: Foundation, Environment, Ingestion, Transformation, Visualization, ML (if applicable).

## Scripts

Pipeline utilities live in `_shared/scripts/`. Shared library modules live in `_shared/lib/`. Pre-compute scripts live in each skill's `scripts/` subdirectory under `.github/skills/`.

| Script | Location | Purpose |
|--------|----------|---------|
| `run-pipeline.py` | `_shared/scripts/` | Pipeline orchestrator — `start`, `next`, `status`, `advance`, `reset` commands |
| `new-project.py` | `_shared/scripts/` | Scaffolds a new project with all template files + `pipeline-state.json` |
| `fleet-runner.py` | `_shared/scripts/` | Batch runner for multiple problem statements |
| `sync-item-types.py` | `_shared/scripts/` | Syncs `_shared/registry/item-type-registry.json` against Fabric item types |
| `signal-mapper.py` | `fabric-discover/scripts/` | Maps problem signals to task flow candidates |
| `decision-resolver.py` | `fabric-design/scripts/` | Resolves decision guide YAML frontmatter for agents |
| `handoff-scaffolder.py` | `fabric-design/scripts/` | Pre-fills handoff template YAML from diagram metadata |
| `review-prescan.py` | `fabric-design/scripts/` | Pre-scans architecture handoff for review flags |
| `deploy-script-gen.py` | `fabric-deploy/scripts/` | Reads architecture handoff YAML, generates fabric-cicd artifacts and deploy scripts |
| `taskflow-gen.py` | `fabric-deploy/scripts/` | Generates Fabric workspace task flow JSON for import |
| `taskflow-template-gen.py` | `fabric-deploy/scripts/` | Generates task flow template JSON from handoff items |
| `diagram-gen.py` | `fabric-design/scripts/` | Generates validated ASCII architecture diagrams from handoff YAML |
| `diagram-validator.py` | `fabric-design/scripts/` | Validates ASCII diagram structure (balanced boxes, edges) |
| `test-plan-prefill.py` | `fabric-test/scripts/` | Prefills test plan from acceptance criteria |
| `check-drift.py` | `fabric-test/scripts/` | Documentation drift detection (26 cross-reference checks) |
| `validate-items.py` | `fabric-test/scripts/` | Validates deployed items via Fabric REST API |
| `registry_loader.py` | `_shared/lib/` | Shared module — all scripts import item type metadata from here |
| `yaml_utils.py` | `_shared/lib/` | Shared module — YAML extraction and parsing (consolidated from 6 scripts) |
| `text_utils.py` | `_shared/lib/` | Shared module — slugify and text utilities |
| `deployment_loader.py` | `_shared/lib/` | Shared module — deployment order registry loader |

**Registries:** All canonical registry files live in `_shared/registry/`:
- `_shared/registry/item-type-registry.json` — Single source of truth for item type metadata including skillset (LC/CF)
- `_shared/registry/deployment-order.json` — Canonical deployment order for all task flows
- `_shared/registry/validation-checklists.json` — Post-deployment manual steps and phases per task flow

Update these JSON files when adding/modifying task flows — the markdown tables in diagram/validation files are for human visualization only.

> ⚠️ **Enforcement:** These scripts are NOT optional helpers — they are mandatory pre-compute steps. Every pipeline phase has a pre-compute script that MUST run before the LLM adds judgment.

## Deploy script generation

The deploy script generator (`.github/skills/fabric-deploy/scripts/deploy-script-gen.py`) produces `fabric-cicd` workspace directories and a self-contained Python deploy script from architecture handoffs. Key features:

- **`fabric-cicd` integration** — Generates workspace directory structure with `.platform` files and `config.yml` for `fabric-cicd` deployment
- **Workspace selection** — Interactive "Create new or use existing" picker
- **Descriptions file** — Loads `descriptions-{slug}.json` for workspace and item descriptions
- **Folder organization** — Creates workspace folders (Storage, Configuration, Ingestion, Processing, Analytics, Machine Learning) before item deployment
- **Post-deploy metadata** — Exports `post-deploy-metadata-{slug}.json` with workspace and item IDs
- **Variable Library population** — Auto-populates VL with ItemReference variables from deployed items

## Pipeline state

Each project has a `pipeline-state.json` (scaffolded by `new-project.py`) that tracks which phase is current, which phases are complete, and whether transitions are automatic or require human approval. The `run-pipeline.py` script manages this file.

## ADR write-through

Architecture Decision Records (ADRs) are written by the `/fabric-design` skill during Phase 1a (DRAFT) and refined during Phase 1c (FINAL) — not deferred to Phase 4 (Documentation). This ensures:

- Reviewers in Phase 1b can reference the full decision rationale
- The "why" behind each decision is captured while context is fresh
- The `/fabric-document` skill polishes language and adds cross-links rather than writing ADRs from scratch

The 5 standard ADR files (`docs/decisions/001-task-flow.md` through `005-visualization.md`) are scaffolded by `new-project.py`. The architect fills them using the format from `.github/skills/fabric-design/references/adr-template.md`.

## Agent boundaries

Agents operate under strict deterministic-vs-reasoning boundaries. **Every pipeline phase has a pre-compute script that MUST run before the LLM adds judgment.** These rules are inlined into each skill's `SKILL.md`.

Key rules:
- **MUST** use `run-pipeline.py` to orchestrate — not ad-hoc agent chaining
- **MUST** run pre-compute scripts before LLM reasoning (e.g., `signal-mapper.py` before discovery, `review-prescan.py` before review, `deploy-script-gen.py` before deploy)
- **MUST** use each skill's `schemas/` directory for handoff output format
- **MUST** use `fabric-cicd` as the sole deployment and validation dependency — do NOT introduce `ms-fabric-cli` (`fab`) or other CLI tools
- **MUST NOT** hand-write deployment scripts, handoff YAML structure, or pipeline state
- **MUST NOT** skip pre-compute steps even if the LLM "knows" the answer

> **Core principle:** If it's reproducible across 1,000 projects, a script does it — not an agent.

## Agent conventions

### ORCHESTRATION — Pipeline Runner

The single agent file (`.github/agents/fabric-advisor.agent.md`) includes an `⚠️ ORCHESTRATION` section. Skills are invoked via `run-pipeline.py advance && run-pipeline.py next` for all phase transitions — **never** manually chain skills or ask "Want me to continue?". The runner manages `pipeline-state.json`, verifies output files, runs pre-compute scripts, and enforces the human gate at Phase 2b (which supports both `--approve` and `--revise`).

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

- The banner function is embedded inline by `deploy-script-gen.py` — no separate banner file
- The `mode` parameter should reflect the script's purpose
- If the banner design changes, update `deploy-script-gen.py`

## Git workflow

When agents create or modify files in `projects/`:
- **Commit messages:** Use the format `[project-name] action description`
- **One project per commit:** Don't mix changes across different projects
- **Never commit secrets:** Use environment variables or parameter placeholders
