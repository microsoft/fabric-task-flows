#!/usr/bin/env python3
"""
Scaffolds an architecture handoff document from registry data.

Loads deployment order from ``_shared/registry/deployment-order.json`` via
``deployment_loader.get_deployment_items()``, maps items to Fabric types from the
item-type registry, and generates a template-aligned architecture handoff document
with YAML frontmatter, items, waves, and acceptance criteria.

Usage:
    python .github/skills/fabric-design/scripts/handoff-scaffolder.py --task-flow medallion --project "My Project"
    python .github/skills/fabric-design/scripts/handoff-scaffolder.py --task-flow lambda --project "My Project" --decisions decisions.yaml
    python .github/skills/fabric-design/scripts/handoff-scaffolder.py --task-flow medallion --project "My Project" --output handoff.md

Importable:
    from handoff_scaffolder import scaffold
    md = scaffold("medallion", "My Project")
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# ── Item-type → fab type mapping (for AC verification stubs) ──────────────

# Item type mappings — loaded from _shared/registry/item-type-registry.json
# Do NOT maintain these dicts manually. See CONTRIBUTING.md.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / "_shared" / "lib"))
from paths import REPO_ROOT
from registry_loader import build_fab_type_map, load_registry
from deployment_loader import get_deployment_items

FAB_TYPE_MAP: dict[str, str] = build_fab_type_map()
PORTAL_ONLY_TYPES: set[str] = {
    data["display_name"] for data in load_registry().values()
    if not data.get("rest_api", {}).get("creatable", False)
}

# ── Data classes ──────────────────────────────────────────────────────────

@dataclass
class DiagramItem:
    order: str
    item_type: str
    skillset: str
    depends_on: str
    required_for: str
    is_alternative: bool = False
    alternative_group: str | None = None


@dataclass
class DeployItem:
    item_name: str
    item_type: str
    fab_type: str
    wave: int
    dependencies: list[str] = field(default_factory=list)
    purpose: str = ""
    is_alternative: bool = False
    alternative_note: str | None = None
    portal_only: bool = False


# ── Naming helpers ────────────────────────────────────────────────────────

def _to_kebab(item_type: str) -> str:
    """Convert diagram Item Type to kebab-case item_name.

    Handles modifier-first patterns like 'Lakehouse Bronze' → 'bronze-lakehouse'
    and direct names like 'Copy Job' → 'copy-job'.
    """
    layered_prefixes = {"Lakehouse", "Warehouse", "Eventhouse"}
    parts = item_type.strip().split()
    if len(parts) >= 2 and parts[0] in layered_prefixes:
        base = parts[0].lower()
        modifier = "-".join(p.lower() for p in parts[1:])
        return f"{modifier}-{base}"
    return "-".join(p.lower() for p in parts)


def _fab_type_for(item_type: str) -> str:
    """Resolve the fab CLI type string for an item type."""
    if item_type in FAB_TYPE_MAP:
        return FAB_TYPE_MAP[item_type]
    base = item_type.strip().split()[0]
    if base in FAB_TYPE_MAP:
        return FAB_TYPE_MAP[base]
    return item_type.replace(" ", "")


def _wave_number(order: str) -> int:
    """Extract the numeric wave prefix from an Order cell like '1a', '2', '3b'."""
    m = re.match(r"(\d+)", order.strip())
    return int(m.group(1)) if m else 0


def _purpose_from(item_type: str, required_for: str) -> str:
    """Generate a concise purpose string."""
    required = required_for.strip()
    if required and required.lower() not in {"(optional)", ""}:
        return required
    return f"{item_type} deployment"


# ── Diagram parser — loads from JSON registry ─────────────────────────────


def parse_diagram(task_flow: str) -> list[DiagramItem]:
    """Parse deployment order from the JSON registry for a task flow.
    
    Primary source: _shared/registry/deployment-order.json
    """
    json_items = get_deployment_items(task_flow)
    
    if not json_items:
        raise ValueError(
            f"No deployment order found for task flow '{task_flow}' in registry. "
            f"The 'general' task flow uses a visual-only diagram."
        )

    items: list[DiagramItem] = []

    for ji in json_items:
        is_alt = "alternativeGroup" in ji
        alt_group = ji.get("alternativeGroup")
        
        # Resolve the alternative group reference to the first item in that group
        if is_alt and alt_group:
            # Find the first item with this alternative group
            for prev in json_items:
                if prev.get("alternativeGroup") == alt_group and prev["itemType"] != ji["itemType"]:
                    alt_group = prev["itemType"]
                    break
        
        items.append(DiagramItem(
            order=ji["order"],
            item_type=ji["itemType"],
            skillset=ji.get("skillset", "[LC]"),
            depends_on=", ".join(ji.get("dependsOn", [])),
            required_for=", ".join(ji.get("requiredFor", [])),
            is_alternative=is_alt,
            alternative_group=alt_group,
        ))
    return items


# ── Decision filtering ────────────────────────────────────────────────────

def _load_decisions_yaml(path: str) -> dict:
    """Minimal YAML loader for decision-resolver output (no PyYAML dep)."""
    result: dict = {}
    current_section: str | None = None
    current_key: str | None = None

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.rstrip()
            if not stripped or stripped.startswith("#"):
                continue
            indent = len(line) - len(line.lstrip())

            if indent == 0 and ":" in stripped:
                key, _, val = stripped.partition(":")
                current_section = key.strip()
                val = val.strip()
                if val and val != "":
                    result[current_section] = val.strip('"').strip("'")
                else:
                    result[current_section] = {}
                current_key = None
            elif indent == 2 and current_section == "decisions" and ":" in stripped:
                key = stripped.strip().rstrip(":")
                if ":" in key:
                    k, _, v = key.partition(":")
                    key = k.strip()
                current_key = key.strip().rstrip(":")
                if isinstance(result.get("decisions"), dict):
                    result["decisions"][current_key] = {}
            elif indent == 4 and current_key and isinstance(result.get("decisions"), dict):
                k, _, v = stripped.strip().partition(":")
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if v.lower() == "null":
                    v = None
                result["decisions"][current_key][k] = v

    return result


def _filter_by_decisions(items: list[DiagramItem], decisions: dict) -> list[DiagramItem]:
    """Optionally prune diagram items based on resolved decisions.

    Currently informational — includes all items but marks alternatives
    based on gold_layer_storage or similar decision choices.
    """
    if not decisions or "decisions" not in decisions:
        return items
    return items


# ── Core scaffold logic ──────────────────────────────────────────────────

def _build_deploy_items(diagram_items: list[DiagramItem]) -> list[DeployItem]:
    """Convert parsed diagram rows into deployment items."""
    deploy_items: list[DeployItem] = []
    for di in diagram_items:
        name = _to_kebab(di.item_type)
        fab_type = _fab_type_for(di.item_type)
        wave = _wave_number(di.order)

        deps: list[str] = []
        dep_text = di.depends_on.strip()
        if dep_text and not re.match(r"\(none[\s\-—]", dep_text, re.IGNORECASE) and dep_text.lower() != "(optional)":
            deps = [d.strip() for d in re.split(r"[,/]|\bOR\b|\band\b", dep_text, flags=re.IGNORECASE) if d.strip()]

        portal_only = di.item_type in PORTAL_ONLY_TYPES

        alt_note: str | None = None
        if di.is_alternative:
            alt_note = f"Alternative to {_to_kebab(di.alternative_group)}" if di.alternative_group else "Alternative option"

        deploy_items.append(DeployItem(
            item_name=name,
            item_type=fab_type,
            fab_type=fab_type,
            wave=wave,
            dependencies=deps,
            purpose=_purpose_from(di.item_type, di.required_for),
            is_alternative=di.is_alternative,
            alternative_note=alt_note,
            portal_only=portal_only,
        ))
    return deploy_items


@dataclass
class Wave:
    wave_number: int
    items: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    parallel_capable: bool = False


def _build_waves(deploy_items: list[DeployItem]) -> list[Wave]:
    """Group deploy items into numbered waves."""
    wave_map: dict[int, list[DeployItem]] = {}
    for di in deploy_items:
        wave_map.setdefault(di.wave, []).append(di)

    waves: list[Wave] = []
    for wn in sorted(wave_map):
        items_in_wave = wave_map[wn]
        item_names = [it.item_name for it in items_in_wave]
        # Dependencies: collect all raw deps from items in this wave
        all_deps: list[str] = []
        for it in items_in_wave:
            all_deps.extend(it.dependencies)
        unique_deps = list(dict.fromkeys(d for d in all_deps if d))

        waves.append(Wave(
            wave_number=wn,
            items=item_names,
            dependencies=unique_deps,
            parallel_capable=len(items_in_wave) > 1,
        ))
    return waves


# ── YAML emitters ─────────────────────────────────────────────────────────

def _yaml_list(items: list[str]) -> str:
    if not items:
        return "[]"
    return "[" + ", ".join(items) + "]"


def _emit_items_yaml(deploy_items: list[DeployItem]) -> str:
    lines = ["items:"]
    for i, di in enumerate(deploy_items, start=1):
        lines.append(f"  - id: {i}")
        lines.append(f"    name: \"{di.item_name}\"")
        lines.append(f"    type: \"{di.item_type}\"")
        lines.append(f"    skillset: \"{di.fab_type}\"")
        lines.append(f"    depends_on: {_yaml_list(di.dependencies)}")
        lines.append(f"    purpose: \"{di.purpose}\"")
        if di.is_alternative and di.alternative_note:
            lines.append(f"    note: \"{di.alternative_note}\"")
        if di.portal_only:
            lines.append("    note: \"portal-only — verify manually\"")
    return "\n".join(lines)


def _emit_waves_yaml(waves: list[Wave]) -> str:
    lines = ["waves:"]
    for w in waves:
        wave_name = f"Wave {w.wave_number}"
        blocked_by = [w.wave_number - 1] if w.wave_number > 1 else []
        lines.append(f"  - id: {w.wave_number}")
        lines.append(f"    name: \"{wave_name}\"")
        lines.append(f"    items: {_yaml_list(w.items)}")
        if blocked_by:
            lines.append(f"    blocked_by: {_yaml_list([str(b) for b in blocked_by])}")
        lines.append(f"    parallel: {'true' if w.parallel_capable else 'false'}")
    return "\n".join(lines)


def _emit_ac_yaml(deploy_items: list[DeployItem], task_flow: str) -> str:
    lines = ["acceptance_criteria:"]
    for i, di in enumerate(deploy_items, start=1):
        ac_id = f"AC-{i}"
        portal_suffix = " (portal-only — verify manually)" if di.portal_only else ""
        lines.append(f"  - id: {ac_id}")
        lines.append(f"    type: structural")
        lines.append(f"    criterion: \"{di.item_name} exists and is accessible{portal_suffix}\"")
        lines.append(f"    verify: \"REST API GET /workspaces/{{id}}/items?type={di.fab_type} | verify {di.item_name}\"")
        lines.append(f"    target: \"{di.item_name}\"")
    return "\n".join(lines)


# ── Decision table helpers ────────────────────────────────────────────────

def _build_decisions_table(decisions: dict | None) -> list[str]:
    """Build Decisions table rows from decision-resolver output."""
    if not decisions or "decisions" not in decisions:
        return [
            "| Storage | | |",
            "| Ingestion | | |",
            "| Processing | | |",
            "| Visualization | | |",
            "| Semantic Model Query Mode | | |",
        ]

    d = decisions["decisions"]
    rows: list[str] = []
    decision_labels = {
        "storage": "Storage",
        "ingestion": "Ingestion",
        "processing": "Processing",
        "visualization": "Visualization",
        "parameterization": "Parameterization",
        "skillset": "Skillset",
        "api": "API",
    }

    for key, label in decision_labels.items():
        entry = d.get(key, {})
        if isinstance(entry, dict):
            choice = entry.get("choice", "")
            rule = entry.get("rule_matched", "")
            if choice and choice != "None":
                rows.append(f"| {label} | {choice} | {rule or ''} |")

    if not any("Semantic Model" in r for r in rows):
        rows.append("| Semantic Model Query Mode | | |")

    return rows if rows else ["| Storage | | |"]


def _build_alternatives_table(decisions: dict | None) -> list[str]:
    """Build Alternatives table rows from decision-resolver output."""
    if not decisions or "decisions" not in decisions:
        return ["| 1 | | | |"]

    rows: list[str] = []
    counter = 1
    d = decisions["decisions"]
    decision_labels = {
        "storage": "Storage",
        "ingestion": "Ingestion",
        "processing": "Processing",
        "visualization": "Visualization",
        "parameterization": "Parameterization",
    }

    for key, label in decision_labels.items():
        entry = d.get(key, {})
        if isinstance(entry, dict):
            candidates = entry.get("candidates", [])
            choice = entry.get("choice", "")
            if isinstance(candidates, list):
                for cand in candidates:
                    if cand != choice:
                        rows.append(f"| {counter} | {label} | {cand} | Not selected by decision rules |")
                        counter += 1

    return rows if rows else ["| 1 | | | |"]


# ── Public API ────────────────────────────────────────────────────────────

def scaffold(task_flow: str, project: str, decisions: dict | None = None) -> str:
    """Generate a scaffolded architecture handoff markdown string.

    Args:
        task_flow: Task flow ID (e.g. 'medallion', 'lambda').
        project: Human-readable project name.
        decisions: Optional dict from decision-resolver output.

    Returns:
        Markdown string with pre-filled YAML blocks.
    """
    diagram_items = parse_diagram(task_flow)

    if decisions:
        diagram_items = _filter_by_decisions(diagram_items, decisions)

    deploy_items = _build_deploy_items(diagram_items)
    waves = _build_waves(deploy_items)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    manual_steps = sum(1 for di in deploy_items if di.portal_only)

    decisions_table = _build_decisions_table(decisions)
    alternatives_table = _build_alternatives_table(decisions)

    items_yaml = _emit_items_yaml(deploy_items)
    waves_yaml = _emit_waves_yaml(waves)
    ac_yaml = _emit_ac_yaml(deploy_items, task_flow)

    parts: list[str] = [
        "---",
        f"project: {project}",
        f"task_flow: {task_flow}",
        "phase: draft",
        "status: draft",
        f"created: {today}",
        f"last_updated: {today}",
        "design_review:",
        "  engineer: pending",
        "  tester: pending",
        f"items: {len(deploy_items)}",
        f"acceptance_criteria: {len(deploy_items)}",
        f"manual_steps: {manual_steps}",
        f"deployment_waves: {len(waves)}",
        "blockers:",
        "  critical: []",
        "  medium: []",
        "next_phase: design-review",
        "---",
        "",
        f"# Architecture Handoff — {project}",
        "",
        f"**Project:** {project}",
        f"**Task flow:** {task_flow}",
        f"**Date:** {today}",
        "**Status:** DRAFT — Awaiting design review by /fabric-deploy and /fabric-test.",
        "",
        "---",
        "",
        "### Problem Reference",
        "> See: prd/discovery-brief.md",
        "> Summary: <!-- /fabric-design: ≤20 word summary -->",
        "",
        "---",
        "",
        "## Architecture Diagram",
        "",
        "```",
        "<!-- Replace this block with your ASCII diagram -->",
        "```",
        "",
        "---",
        "",
        "## Decisions",
        "",
        "| Decision | Choice | Rationale |",
        "|----------|--------|-----------|",
    ]

    parts.extend(decisions_table)

    parts.extend([
        "",
        "### Items to Deploy",
        "",
        "```yaml",
        items_yaml,
        "```",
        "",
        "### Deployment Order",
        "",
        "```yaml",
        waves_yaml,
        "```",
        "",
        "### Acceptance Criteria",
        "",
        "```yaml",
        ac_yaml,
        "```",
        "",
        "## Alternatives Considered",
        "",
        "| # | Decision | Option Rejected | Why Rejected |",
        "|---|----------|-----------------|--------------|",
    ])

    parts.extend(alternatives_table)

    parts.extend([
        "",
        "## Trade-offs",
        "",
        "| # | Trade-off | Benefit | Cost | Mitigation |",
        "|---|-----------|---------|------|------------|",
        "| 1 | | | | |",
        "",
        "## Deployment Strategy",
        "",
        "| Decision | Choice | Rationale |",
        "|----------|--------|-----------|",
        "| Workspace Approach | | |",
        "| Environments | | |",
        "| CI/CD Tool | | |",
        "| Parameterization | | |",
        "| Branching Model | | |",
        "",
        "## References",
        "",
        f"- Project folder: projects/{project}/",
        f"- Diagram: diagrams/{task_flow}.md",
        "- Validation: _shared/registry/validation-checklists.json",
        "",
        "## Design Review",
        "",
        "| Reviewer | Feedback Summary | Incorporated? | What Changed |",
        "|----------|-----------------|---------------|--------------|",
        "| /fabric-deploy | <!-- pending --> | | |",
        "| /fabric-test | <!-- pending --> | | |",
    ])

    return "\n".join(parts)


# ── CLI ───────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pre-fill architecture handoff YAML from deployment diagrams"
    )
    parser.add_argument("--task-flow", required=True,
                        help="Task flow ID (e.g. medallion, lambda, event-analytics)")
    parser.add_argument("--project", required=True,
                        help="Project name")
    parser.add_argument("--decisions", default=None,
                        help="Path to decision-resolver output YAML")
    parser.add_argument("--output", default=None,
                        help="Output file path (default: stdout)")
    args = parser.parse_args()

    decisions: dict | None = None
    if args.decisions:
        try:
            decisions = _load_decisions_yaml(args.decisions)
        except FileNotFoundError:
            print(f"Error: decisions file not found: {args.decisions}", file=sys.stderr)
            sys.exit(2)
        except Exception as e:
            print(f"Error reading decisions file: {e}", file=sys.stderr)
            sys.exit(2)

    try:
        result = scaffold(args.task_flow, args.project, decisions)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        print(f"Wrote scaffolded handoff to {args.output}", file=sys.stderr)
    else:
        sys.stdout.buffer.write(result.encode("utf-8"))
        sys.stdout.buffer.write(b"\n")


if __name__ == "__main__":
    main()
