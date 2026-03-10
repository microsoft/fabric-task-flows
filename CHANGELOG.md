# Changelog

All notable changes to this project are documented in this file.

## [1.0.1] — 2026-03-10

### Fixed

- **CI test path broken** — `ci.yml` referenced old `tests/` directory; updated to `_shared/tests/` (post-restructuring regression)
- **check-drift.py crash on Windows** — Unicode box-drawing characters failed with cp1252 encoding; added `sys.stdout.reconfigure(encoding='utf-8')` fallback
- **README stale paths** — Directory tree referenced old `tests/` location and `fab` CLI; updated to `_shared/tests/` and `fabric-cicd`
- **144 ruff lint errors** — Auto-fixed 114 (f-string placeholders, unused imports), manually fixed 30 (unused variables, ambiguous names, import order via per-file-ignores)

### Added

- `_shared/lib/__init__.py` for proper package recognition and CI coverage detection
- **10 new test files** covering all 15 scripts (542 total tests, up from 139):
  - `test_check_drift.py` — 36 tests for documentation drift detection
  - `test_signal_mapper.py` — 45 tests for problem-to-task-flow mapping
  - `test_decision_resolver.py` — 90 tests for decision guide resolution
  - `test_review_prescan.py` — 41 tests for engineer/tester review pre-computation
  - `test_handoff_scaffolder.py` — 51 tests for architecture handoff generation
  - `test_test_plan_prefill.py` — 26 tests for test plan pre-filling
  - `test_validate_items.py` — 20 tests for REST API validation
  - `test_diagram_gen.py` — 24 tests for deployment diagram generation
  - `test_diagram_validator.py` — 22 tests for diagram structural validation
  - `test_taskflow_template_gen.py` — 28 tests for fabric-cicd workspace templates

## [1.0.0] — 2026-03-08

### Summary

First stable release. 13 task flows, 7 decision guides, 6 composable skills, full pipeline automation with `run-pipeline.py`, and 20+ projects processed end-to-end.

### Architecture

- **1 orchestrator agent** (`@fabric-advisor`) + **6 composable skills** (discover, design, test, deploy, document, heal)
- **13 task flows**: basic-data-analytics, medallion, lambda, event-analytics, event-medallion, data-analytics-sql-endpoint, basic-machine-learning-models, sensitive-data-insights, translytical, app-backend, conversational-analytics, semantic-governance, general
- **7 decision guides**: storage, ingestion, processing, visualization, skillset, parameterization, API
- **Item type registry**: 25+ Fabric item types with CLI metadata, phase mapping, and aliases

### Pipeline

- `run-pipeline.py` — full lifecycle orchestrator with `start`, `advance`, `next`, `status`, `reset`, `reconcile`
- Automatic phase chaining with single human gate (Phase 2b sign-off with `--approve` / `--revise`)
- Pre-compute scripts run deterministic analysis before every LLM phase
- Design-only mode generates self-contained deploy scripts (.py, .ps1, .sh)

### Quality

- `check-drift.py` — 26 cross-reference checks across 6 categories
- `fleet-runner.py` — batch stress testing across 20+ problem statements
- Self-healing signal mapper via `fabric-heal` skill (4 healing cycles, 90 problem corpus)
- 20 automated tests (registry, deploy-script-gen, taskflow-gen)

---

## Pre-1.0 History

### 2026-03-07 — JTD Consolidation (`31c46eb`)

Applied jobs-to-be-done principle: moved `_shared/` from 10 to 4 files, `scripts/` from 9 to 4 files. Skill-specific content moved into owning skill folders.

### 2026-03-07 — Skill Consolidation (`f8cff2b`)

Consolidated 10 skills to 6 role-based skills: fabric-review + fabric-finalize → fabric-design, fabric-test-plan + fabric-validate → fabric-test, fabric-remediate → fabric-deploy.

### 2026-03-07 — Skill Architecture (`d2d1928`, `8b66731`)

Migrated from 7 multi-mode agents to 1 orchestrator + 10 composable skills following the Agent Skills open standard.

### 2026-03-07 — Schema & Reference Migration (`a8d28e4`, `20d76ac`)

Moved schemas, references, and assets into owning skill folders. Centralized `registry_loader.py` in `_shared/`.

### 2026-03-06 — Self-Healing Pipeline (`bd4eabc` → `0ad47f8`)

Added signal mapper self-healing: problem generation, keyword patching, 250-problem stress test, 10 healing iterations across 90 problems.

### 2026-03-05 — Fleet Runner & Inefficiency Analyzer (`e212f0e`)

Added `fleet-runner.py` for batch project processing and `analyze-inefficiencies.py` for coverage gap detection.

### 2026-03-04 — Deterministic Diagram Generator (`416983e`)

Added `diagram-gen.py` for generating validated ASCII architecture diagrams at sign-off.

### 2026-03-03 — Self-Contained Deploy Scripts (`acf71d1`)

Deploy scripts embed the `FabricDeployer` utility inline — no external imports needed.
