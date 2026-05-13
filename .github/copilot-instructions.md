# Copilot Instructions

## Project Overview

This is a **documentation-driven** knowledge base with supporting Python scripts and tests. The repo provides pre-defined Microsoft Fabric architectures via one orchestrator agent (`@fabric-advisor`) that delegates to 6 composable skills.

### Architecture

- **Orchestrator:** `@fabric-advisor` (`.github/agents/`) — routes phases to skills, never decides or deploys directly.
- **Skills:** (`.github/skills/`) — composable, auto-activating instruction packs. Each has a `SKILL.md` with trigger phrases and focused workflow.
- **Handoffs:** Skills exchange structured documents stored in `_projects/{workspace}/docs/`.
- **Pipeline flow:** `_shared/workflow-guide.md`

## Conventions

### Parallel Execution

> **⚠️ MUST parallelize independent work.** If task B does not depend on the _output_ of task A, they run in parallel — never sequentially. This applies to tool calls, file operations, and sub-tasks.

### Registry-First

> **`item-type-registry.json` is the single source of truth** for all item metadata. Never hardcode or guess values — read from the registry. If a field is wrong, fix the registry.

### Templates-First

> **Item definitions live in `_shared/templates/{ItemType}/`** and are copied verbatim into project deploy folders. Never invent item definition content.

### Deterministic Execution

> Use existing scripts (`deploy-script-gen.py`, `taskflow-gen.py`, `registry_loader`) and `fabric-cicd`. Never improvise workarounds when a standard tool handles the operation.

### Windows Compatibility

> **Always use `encoding='utf-8'`** when reading or writing JSON, Markdown, and Python files. Windows defaults to `cp1252`, which silently corrupts Unicode.

### Pre-Generated Content

> Skills receive pre-generated output files from `run-pipeline.py`. **Edit in place** — never rewrite from scratch. Fill `<!-- AGENT: FILL -->` markers with judgment; leave structural YAML intact.

### Skill Handoff

> After writing output to `_projects/[name]/docs/`, call `run-pipeline.py advance --project <name> -q`. If output says `🟢 AUTO-CHAIN → <skill>`, invoke immediately. If `🛑 HUMAN GATE`, present sign-off to user.

### Contributor Guidelines

> See [CONTRIBUTING.md](../CONTRIBUTING.md) for scripts, registries, and development workflow.
