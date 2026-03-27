# Copilot Instructions

## Project Overview

This is a **documentation-driven** knowledge base with supporting Python scripts and tests. The repo provides pre-defined Microsoft Fabric architectures via one orchestrator agent (`@fabric-advisor`) that delegates to 6 composable skills.

## Architecture

### Orchestrator agent (`.github/agents/`)

`@fabric-advisor` orchestrates the full pipeline. It **never** makes architecture decisions or deploys directly — it delegates to skills based on phase.

### Skills (`.github/skills/`)

Skills are composable, auto-activating instruction packs that do the actual work. Each skill has a `SKILL.md` with trigger phrases, bundled references, and focused single-workflow instructions.

> **Skill metadata:** managed by `run-pipeline.py` (do not access registry files directly)  
> **Pipeline flow:** `_shared/workflow-guide.md`

Skills exchange structured **handoff documents** stored in `_projects/{workspace}/docs/`.

## Parallel Execution Principle

> **⚠️ MUST parallelize independent work.** When multiple files, tool calls, or sub-tasks have no data dependency on each other, agents MUST execute them in a single parallel batch — never sequentially.
>
> **Rule of thumb:** If task B does not depend on the _output_ of task A, they MUST run in parallel. Sequential execution of independent work wastes tokens and time.

## Scope Limits

> **`@fabric-advisor` is a task-flow specialist — not a general-purpose assistant.** It must NEVER answer user questions directly, provide tutorials, or offer how-to guidance. Every user interaction routes through the skill pipeline: discovery → design → test → deploy → validate → document. If no phase is active and the user describes a data problem, route to `/fabric-discover`. If the query is out of scope, decline politely.

## Registry-First Principle

> **`item-type-registry.json` is the single source of truth** for all item metadata — types, task types, phases, aliases, API fields, and CICD strategy. Agents must **always read from the registry**; never hardcode or guess these values. If a field seems wrong, fix the registry — don't add mapping tables or overrides in scripts.

## Templates-First Principle

> **Item definition files live in `_shared/templates/{ItemType}/`** and are copied verbatim into project deploy folders. Agents must **never invent item definition content** — copy from the template directory. If a template is missing or empty, that reflects the Fabric REST API reality (some items have no definition endpoint).

## Deterministic Execution

> **All deployment and generation work is deterministic.** Use the existing scripts (`deploy-script-gen.py`, `taskflow-gen.py`, `taskflow-template-gen.py`), the `registry_loader` library, and `fabric-cicd` — never improvise workarounds, manual polling gates, or REST API bypasses when a standard tool already handles the operation.

## Sign-Off Gate

> **The sign-off gate is a mandatory human checkpoint.** Always display the **full ASCII architecture diagram** and item summary in the chat response — never abbreviate, truncate, or skip. The user's chat window is their only interface; tool output alone is not visible.

## Windows Compatibility

> **Always use `encoding='utf-8'`** when reading or writing JSON, Markdown, and Python files. Windows defaults to `cp1252`, which silently corrupts Unicode characters and BOM-prefixed files.

## Key Conventions

> For contributor guidelines, see [CONTRIBUTING.md](../CONTRIBUTING.md).
