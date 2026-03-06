# Contributing to Task Flows

## Adding a new task flow

1. Add an H2 section to `task-flows.md` following the existing structure: description, task count, ASCII flow diagram, workloads, items, decision table with links, and diagram/validation links.
2. Create `diagrams/{task-flow-id}.md` with phased deployment flow using the symbols from `_shared/legend.md` (`[LC]`/`[CF]` skillset tags, `──►` flow, `OR` for choices).
3. Create `validation/{task-flow-id}.md` with a post-deployment manual steps table and a phase-by-phase checklist (Foundation → Environment → Ingestion → Transformation → Visualization → ML).
4. Update `diagrams/_index.md` and `validation/_index.md` with the new entry.
5. Run `python scripts/new-project.py` to verify scaffolding works with the new task flow.

## Diagram conventions

Deployment diagrams use ASCII box-drawing characters with phased sections separated by `═════`. Skillset tags (`[LC]`, `[CF]`, `[LC/CF]`) annotate each item. Decision points use `OR` blocks with differentiator comparison tables. Add `<!-- AGENT: Skip to "## Deployment Order" -->` before the ASCII art section.

## Validation checklist structure

Every validation file starts with a "Post-Deployment Manual Steps" table (Item Type → Manual Action Required), followed by phased checklists using `- [ ]` checkboxes. Phases follow the standard order: Foundation, Environment, Ingestion, Transformation, Visualization, ML (if applicable).

## Git workflow

When agents create or modify files in `projects/`:
- **Commit messages:** Use the format `[project-name] action description`
- **One project per commit:** Don't mix changes across different projects
- **Never commit secrets:** Use environment variables or parameter placeholders
