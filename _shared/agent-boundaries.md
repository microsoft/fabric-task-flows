# Agent Boundaries: Deterministic vs Reasoning

> **Core principle:** If it's reproducible across 1,000 projects, a script does it — not an agent. LLMs reason; tools produce.

## The Boundary

| Category | Tool does it | LLM does it |
|----------|-------------|-------------|
| **Scaffolding** | `new-project.py` creates dirs + templates | Never |
| **Signal mapping** | `signal-mapper.py` maps keywords → candidates | Confirm/adjust with user |
| **Decision resolution** | `decision-resolver.py` applies YAML frontmatter rules | Add judgment when ambiguous |
| **Handoff structure** | `handoff-scaffolder.py` pre-fills YAML from diagram | Fill in naming, purpose, rationale |
| **Review pre-scan** | `review-prescan.py` runs mechanical checks | Add nuanced findings |
| **Test plan mapping** | `test-plan-prefill.py` maps ACs → phases | Add edge cases, critical checks |
| **Deploy scripts** | `deploy-script-gen.py` generates from templates | Never hand-write |
| **Validation checks** | `validate-items.ps1/.sh` runs `fab exists` per item | Interpret partial results |
| **Task flow JSON** | `taskflow-gen.py` generates Fabric import JSON | Never |
| **Pipeline state** | `run-pipeline.py` manages `pipeline-state.json` | Never touch directly |
| **Output schemas** | `_shared/schemas/` define YAML structure | Fill in content fields |

## MUST Rules (All Phases)

1. **MUST** use `run-pipeline.py` to orchestrate pipeline phases — not ad-hoc agent chaining
2. **MUST** run the pre-compute script for each phase before LLM reasoning (see Phase Rules below)
3. **MUST** use `_shared/schemas/` for all handoff output format — do not invent structure
4. **MUST** use `new-project.py` to scaffold projects — do not create directories or template files manually
5. **MUST** follow filename conventions — `deploy-{project-name}.ps1/.sh`
6. **MUST** generate both `.ps1` and `.sh` deploy scripts (via `deploy-script-gen.py`)
7. **MUST** update `pipeline-state.json` only through `run-pipeline.py` — never edit directly

## MUST NOT Rules (All Phases)

1. **MUST NOT** hand-write deployment scripts — use `deploy-script-gen.py`
2. **MUST NOT** write handoff YAML structure from scratch — use the schema + pre-compute output as base
3. **MUST NOT** skip pre-compute steps — even if the LLM "knows" the answer
4. **MUST NOT** manually manage phase transitions — `run-pipeline.py` handles this
5. **MUST NOT** create project directories or boilerplate files manually — `new-project.py` does this
6. **MUST NOT** modify template functions (`Fab-Mkdir`, `Prompt-Value`, `Print-Banner`) — they come from `_shared/script-template.ps1/.sh`
7. **MUST NOT** produce free-form prose where a schema expects structured YAML

## Phase-by-Phase Rules

### Phase 0a — Discovery (`@fabric-advisor`)

| Step | Tool | What it produces |
|------|------|-----------------|
| Pre-compute | `signal-mapper.py --text "<problem>"` | Draft signal table (JSON) |
| LLM adds | Confirm signals with user, fill discovery brief | User-facing conversation |

**Signs of drift:** Agent infers signals without running `signal-mapper.py`. Agent writes signal table from scratch instead of using pre-computed output.

### Phase 1a — Design (`@fabric-architect`)

| Step | Tool | What it produces |
|------|------|-----------------|
| Pre-compute (after task flow selected) | `decision-resolver.py --signals '{...}'` | Resolved decisions (YAML) |
| Pre-compute (after task flow selected) | `handoff-scaffolder.py --task-flow <id> --project "<name>"` | Pre-filled handoff YAML |
| LLM adds | Architectural judgment, naming, rationale, ACs | Fills in the pre-computed structure |

**Signs of drift:** Agent reads decision guides manually and resolves choices in prose. Agent writes `items_to_deploy` and `deployment_waves` YAML from scratch instead of using scaffolder output.

### Phase 1b — Review (`@fabric-reviewer`)

| Step | Tool | What it produces |
|------|------|-----------------|
| Pre-compute | `review-prescan.py --handoff <path>` | Mechanical findings (YAML) |
| Schema | `_shared/schemas/engineer-review.md` | YAML structure for output |
| Schema | `_shared/schemas/tester-review.md` | YAML structure for output |
| LLM adds | Judgment-based findings beyond mechanical checks | Nuanced review items |

**Signs of drift:** Agent writes all review findings from scratch without running prescan. Agent produces prose instead of structured YAML per schema. Agent invents output format instead of using `_shared/schemas/`.

### Phase 2a — Test Plan (`@fabric-tester`)

| Step | Tool | What it produces |
|------|------|-----------------|
| Pre-compute | `test-plan-prefill.py --handoff <path>` | AC → phase mapping (YAML) |
| Schema | `_shared/schemas/test-plan.md` | YAML structure for output |
| LLM adds | Critical verification items, edge cases | Testing judgment |

**Signs of drift:** Agent maps ACs to phases manually. Agent writes criteria_mapping from scratch. Agent produces markdown table instead of YAML per schema.

### Phase 2c — Deploy (`@fabric-engineer`)

| Step | Tool | What it produces |
|------|------|-----------------|
| Pre-compute | `deploy-script-gen.py --handoff <path> --project "<name>"` | `.ps1` + `.sh` deploy scripts |
| Schema | `_shared/schemas/deployment-handoff.md` | YAML structure for handoff |
| LLM adds | Nothing to the scripts — they are fully generated | Deployment handoff content |

**Signs of drift:** Agent hand-writes deploy scripts. Agent uses custom function names instead of template functions. Agent creates scripts without using `deploy-script-gen.py`. Agent produces a single script instead of both `.ps1` and `.sh`.

### Phase 3 — Validate (`@fabric-tester`)

| Step | Tool | What it produces |
|------|------|-----------------|
| Pre-compute | `validate-items.ps1 <handoff-path>` | Per-item `fab exists` results (YAML) |
| Schema | `_shared/schemas/validation-report.md` | YAML structure for report |
| LLM adds | Interpretation of partial results, issue severity | Validation judgment |

**Signs of drift:** Agent writes validation report without running `validate-items`. Agent marks items as verified without `fab exists` evidence.

### Phase 4 — Document (`@fabric-documenter`)

| Step | Tool | What it produces |
|------|------|-----------------|
| Template | `_shared/adr-template.md` | ADR structure |
| Template | `_shared/documentation-templates.md` | Wiki structure |
| LLM adds | Synthesize all handoffs into readable documentation | All content |

**Signs of drift:** Agent invents ADR format instead of using `_shared/adr-template.md`. Agent skips reading prior handoffs.

## Quick Reference: Which Script for Which Phase

```
Phase 0a  →  signal-mapper.py
Phase 1a  →  decision-resolver.py + handoff-scaffolder.py
Phase 1b  →  review-prescan.py
Phase 2a  →  test-plan-prefill.py
Phase 2c  →  deploy-script-gen.py
Phase 3   →  validate-items.ps1 / validate-items.sh
Post      →  taskflow-gen.py
ALL       →  run-pipeline.py (orchestrates everything above)
```

## When the LLM Should Override Tool Output

Tools produce a **starting point**. The LLM is expected to **augment**, not replace:

- ✅ Add review findings the prescan missed (judgment calls)
- ✅ Add edge cases the test plan prefill didn't cover
- ✅ Adjust signal confidence after user conversation
- ✅ Refine item names from generic to project-specific
- ❌ Rewrite the YAML structure the tool produced
- ❌ Replace tool output with free-form prose
- ❌ Skip the tool and write everything from scratch

## Item Type Registry Rules

All Fabric item type metadata lives in `_shared/item-type-registry.json`. This is the **single source of truth**.

### MUST

1. **MUST** use `_shared/item-type-registry.json` as the canonical source for all item type metadata
2. **MUST** import from `scripts/registry_loader.py` — not maintain separate dicts per script
3. **MUST** run `python scripts/sync-item-types.py --check` to detect drift from the Fabric CLI
4. **MUST** run `python scripts/sync-item-types.py --update` when upgrading `ms-fabric-cli`
5. **MUST** fill in `phase` and `task_type` for any auto-added stubs before merging

### MUST NOT

1. **MUST NOT** add item type dicts to individual scripts — all metadata comes from the registry
2. **MUST NOT** hard-code item type names in scripts — use registry aliases for fuzzy matching
3. **MUST NOT** assume CLI support without checking the registry's `cli_supported` and `mkdir_supported` fields
4. **MUST NOT** use the name "Activator" in new code — the CLI canonical name is "Reflex" (display name remains "Activator")

### Adding a New Item Type

1. Add the entry to `_shared/item-type-registry.json` with all required fields
2. Run `python scripts/sync-item-types.py --diff` to verify alignment
3. All scripts automatically pick up the new type via `registry_loader.py` — no other changes needed
