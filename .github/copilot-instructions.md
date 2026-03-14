# Copilot Instructions

## Project Overview

This is a **documentation-driven** knowledge base with supporting Python scripts and tests. The repo provides pre-defined Microsoft Fabric architectures via one orchestrator agent (`@fabric-advisor`) that delegates to 6 composable skills.

## Architecture

### Orchestrator agent (`.github/agents/`)

`@fabric-advisor` orchestrates the full pipeline. It **never** makes architecture decisions or deploys directly — it delegates to skills based on phase.

### Skills (`.github/skills/`)

Skills are composable, auto-activating instruction packs that do the actual work. Each skill has a `SKILL.md` with trigger phrases, bundled references, and focused single-workflow instructions.

> **Skill metadata:** `_shared/registry/skills-registry.json` (consumed by `run-pipeline.py`)  
> **Pipeline flow:** `_shared/workflow-guide.md`

Skills exchange structured **handoff documents** stored in `_projects/{workspace}/docs/`.

## Parallel Execution Principle

> **⚠️ MUST parallelize independent work.** When multiple files, tool calls, or sub-tasks have no data dependency on each other, agents MUST execute them in a single parallel batch — never sequentially.
>
> **Rule of thumb:** If task B does not depend on the _output_ of task A, they MUST run in parallel. Sequential execution of independent work wastes tokens and time.

## Key Conventions

> For contributor guidelines, see [CONTRIBUTING.md](../CONTRIBUTING.md).
