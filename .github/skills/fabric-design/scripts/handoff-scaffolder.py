#!/usr/bin/env python3
"""
Scaffolds an architecture handoff document from registry data.

Loads deployment order from ``_shared/registry/deployment-order.json`` via
``deployment_loader.get_deployment_items()``, maps items to Fabric types from the
item-type registry, and generates a template-aligned architecture handoff document
with YAML frontmatter, items, waves, and acceptance criteria.

Usage:
    python .github/skills/fabric-design/scripts/handoff-scaffolder.py --task-flow medallion --project "My Project"
    python .github/skills/fabric-design/scripts/handoff-scaffolder.py --task-flow lambda --project "My Project" --decisions decisions.json
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
from registry_loader import build_fab_type_map, load_registry, build_alternatives_map, build_display_names
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


PURPOSE_TEMPLATES: dict[str, str] = {
    "Lakehouse": "Delta Lake storage for {rf}",
    "Warehouse": "Relational analytics store for {rf}",
    "Eventhouse": "Time-series/streaming store for {rf}",
    "SQL Database": "Transactional database for {rf}",
    "KQL Database": "KQL analytics database for {rf}",
    "Cosmos DB": "Document/NoSQL store for {rf}",
    "Pipeline": "Orchestrated data movement for {rf}",
    "Dataflow Gen2": "Visual ETL transforms for {rf}",
    "Eventstream": "Real-time streaming ingestion for {rf}",
    "Copy Job": "Bulk data copy for {rf}",
    "Notebook": "Interactive Spark processing for {rf}",
    "KQL Queryset": "KQL-based data exploration for {rf}",
    "Spark Job Definition": "Scheduled Spark job for {rf}",
    "Stored Procedure": "T-SQL server-side logic for {rf}",
    "Semantic Model": "Semantic layer for {rf}",
    "Report": "Interactive report for {rf}",
    "Paginated Report": "Pixel-perfect printable report for {rf}",
    "Real-Time Dashboard": "Live streaming dashboard for {rf}",
    "Dashboard": "Dashboard for {rf}",
    "Metrics Scorecard": "KPI tracking scorecard for {rf}",
    "Environment": "Spark compute environment for {rf}",
    "Experiment": "ML experiment tracking for {rf}",
    "ML Model": "Trained ML model for {rf}",
    "Activator": "Event-driven alerting for {rf}",
    "GraphQL API": "Flexible read API for {rf}",
    "User Data Functions": "Custom business logic API for {rf}",
    "Variable Library": "Workspace-scoped configuration for {rf}",
}


def _purpose_from(item_type: str, required_for: str) -> str:
    """Generate a concise purpose string using templates."""
    required = required_for.strip()
    rf = required if required and required.lower() not in {"(optional)", ""} else "data workloads"
    # Try exact match first, then base type (strip modifiers like "Bronze", "Silver", "Gold")
    template = PURPOSE_TEMPLATES.get(item_type)
    if not template:
        base_type = item_type.strip().split()[0]
        template = PURPOSE_TEMPLATES.get(base_type)
    if template:
        return template.format(rf=rf)
    return rf if rf != "data workloads" else f"{item_type} deployment"


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

def _load_decisions_file(path: str) -> dict:
    """Load decision-resolver output (JSON preferred, legacy YAML fallback)."""
    import json as _json_mod
    with open(path, encoding="utf-8") as f:
        content = f.read().strip()
    if content.startswith("{"):
        return _json_mod.loads(content)
    # Legacy YAML fallback — hand-rolled parser for flat key: value files
    return _load_decisions_yaml_legacy(content)


def _load_decisions_yaml_legacy(content: str) -> dict:
    """Minimal YAML parser for legacy decision-resolver output (no PyYAML dep)."""
    result: dict = {}
    current_section: str | None = None
    current_key: str | None = None

    for line in content.splitlines():
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
    """Prune alternative items based on resolved decisions.

    When the decision resolver has made a high-confidence choice for a
    decision category (ingestion, storage, processing), remove the
    unchosen alternatives from the same alternativeGroup. If the decision
    is ambiguous, skipped, or unresolved, keep all alternatives (preserving
    the ◄OR► in the diagram so the user can see the options).
    """
    if not decisions or "decisions" not in decisions:
        return items

    decs = decisions["decisions"]

    # Map item types to their governing decision key.
    # Item types that appear as alternatives in deployment-order.json:
    _ITEM_TYPE_TO_DECISION: dict[str, str] = {
        # ingestion alternatives
        "copy job":        "ingestion",
        "pipeline":        "ingestion",
        "dataflow gen2":   "ingestion",
        "eventstream":     "ingestion",
        # storage alternatives
        "lakehouse":       "storage",
        "warehouse":       "storage",
        "sql database":    "storage",
        "cosmos db":       "storage",
        "lakehouse gold":  "storage",
        "warehouse gold":  "storage",
        # processing alternatives
        "notebook":        "processing",
        "spark job definition": "processing",
    }

    # Collect choices with high confidence
    resolved: dict[str, str] = {}  # decision_key → choice string (lowered)
    for dec_key in ("ingestion", "storage", "processing"):
        dec = decs.get(dec_key, {})
        choice = dec.get("choice")
        confidence = dec.get("confidence", "")
        if (choice
                and confidence not in ("ambiguous", "na")
                and "not yet determined" not in (choice or "").lower()):
            resolved[dec_key] = choice.lower()

    if not resolved:
        return items

    filtered: list[DiagramItem] = []
    for item in items:
        if not item.is_alternative:
            filtered.append(item)
            continue

        dec_key = _ITEM_TYPE_TO_DECISION.get(item.item_type.lower())
        if dec_key is None or dec_key not in resolved:
            # No decision governs this alternative — keep it
            filtered.append(item)
            continue

        # Check if this item's type appears in the chosen value
        choice = resolved[dec_key]
        item_lower = item.item_type.lower()
        if item_lower in choice or _to_kebab(item.item_type).lower() in choice.replace(" ", "-"):
            filtered.append(item)
        # else: pruned — this alternative was not selected

    # Clean up: if an alternative survived filtering but ALL its counterparts
    # were pruned, it's no longer an alternative — clear the flag.
    filtered_types = {it.item_type for it in filtered}
    for item in filtered:
        if item.is_alternative and item.alternative_group:
            # Count how many OTHER items share this alternative relationship
            has_counterpart = any(
                other is not item
                and other.is_alternative
                and (other.alternative_group == item.item_type
                     or other.item_type == item.alternative_group)
                for other in filtered
            )
            if not has_counterpart:
                item.is_alternative = False
                item.alternative_group = None

    return filtered


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
            rationale = entry.get("rationale", "") or entry.get("rule_matched", "")
            choice = entry.get("choice", "") or "Not yet determined"
            note = entry.get("note", "")
            if choice == "Not yet determined" and note:
                rationale = note
                # If rationale indicates N/A, show N/A as the choice
                if "n/a" in note.lower():
                    choice = "N/A"
            rows.append(f"| {label} | {choice} | {rationale} |")

    if not any("Semantic Model" in r for r in rows):
        # Semantic Model Query Mode is only relevant for task flows with a Semantic Model
        # For Eventhouse-based flows (event-medallion, event-analytics), it's N/A
        rows.append("| Semantic Model Query Mode | N/A | Not applicable for this task flow |")

    return rows if rows else ["| Storage | Not yet determined | |"]


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
        "skillset": "Skillset",
        "api": "API",
    }

    # Known alternatives per decision for high-confidence decisions
    _KNOWN_ALTERNATIVES: dict[str, list[str]] = {
        "storage": ["Lakehouse", "Warehouse", "Eventhouse", "SQL Database"],
        "ingestion": ["Eventstream", "Pipeline", "Copy Job", "Dataflow Gen2"],
        "processing": ["Notebook", "KQL Queryset", "Spark Job Definition", "Dataflow Gen2"],
        "visualization": ["Power BI Report", "KQL Dashboard", "Direct Lake"],
    }

    for key, label in decision_labels.items():
        entry = d.get(key, {})
        if not isinstance(entry, dict):
            continue
        candidates = entry.get("candidates", [])
        choice = entry.get("choice", "")
        rationale = entry.get("rationale", "")
        confidence = entry.get("confidence", "")

        # For high-confidence decisions without candidates, use known alternatives
        if not candidates and choice and confidence == "high" and key in _KNOWN_ALTERNATIVES:
            candidates = [alt for alt in _KNOWN_ALTERNATIVES[key] if alt != choice]

        if isinstance(candidates, list):
            for cand in candidates:
                if cand != choice:
                    if confidence == "ambiguous":
                        reason = "Viable alternative — decision was ambiguous"
                    elif rationale:
                        reason = f"Not selected — {rationale}"
                    else:
                        reason = "Not selected by decision rules"
                    rows.append(f"| {counter} | {label} | {cand} | {reason} |")
                    counter += 1

    return rows if rows else ["| 1 | | | |"]


def _build_tradeoffs_table(deploy_items: list[DeployItem]) -> list[str]:
    """Build Trade-offs table from registry alternatives.

    For each item in the deployment, check the registry for its alternatives.
    If any alternative is NOT in the deployment (i.e., it was rejected),
    document it as a trade-off: "Chose X over Y".
    """
    alternatives_map = build_alternatives_map()
    display_names = build_display_names()
    rows: list[str] = []
    deployed_fab_types = {di.fab_type for di in deploy_items}
    seen: set[tuple[str, str]] = set()
    counter = 1

    for di in deploy_items:
        alts = alternatives_map.get(di.fab_type, [])
        for alt_canonical in alts:
            pair_key = tuple(sorted([di.fab_type, alt_canonical]))
            if pair_key in seen:
                continue
            if alt_canonical not in deployed_fab_types:
                seen.add(pair_key)
                item_display = display_names.get(di.fab_type.lower(), di.item_type)
                alt_display = display_names.get(alt_canonical.lower(), alt_canonical)
                rows.append(
                    f"| {counter} | {item_display} chosen over {alt_display}"
                    f" | Selected by decision resolver based on project signals"
                    f" | {alt_display} remains available if requirements change"
                    f" | Switch via sign-off revision |"
                )
                counter += 1

    return rows if rows else ["| 1 | (no trade-offs identified) | | | |"]


def _build_deployment_strategy(decisions: dict | None, task_flow: str) -> list[str]:
    """Build Deployment Strategy table from decisions."""
    rows: list[str] = []

    if decisions and "decisions" in decisions:
        d = decisions["decisions"]

        # Workspace Approach
        param = d.get("parameterization", {})
        env_note = param.get("note", "")
        if "single" in env_note.lower() or (param.get("choice") and "Environment Variables" in str(param.get("choice"))):
            rows.append("| Workspace Approach | Single workspace | Simpler setup for single-environment deployments |")
        else:
            rows.append("| Workspace Approach | Dev/Test/Prod workspaces | Environment isolation for safe promotion |")

        # Environments
        param_choice = param.get("choice", "")
        if param_choice:
            rows.append(f"| Environments | {param_choice} | {param.get('rationale', 'Based on environment configuration needs')} |")
        else:
            rows.append("| Environments | Dev + Prod (minimum) | Standard two-environment promotion pattern |")

        # CI/CD Tool
        rows.append("| CI/CD Tool | fabric-cicd Python package | Standard deployment tool for Fabric items |")

        # Parameterization
        if param_choice:
            rows.append(f"| Parameterization | {param_choice} | {param.get('rationale', '')} |")
        else:
            rows.append("| Parameterization | Environment Variables | Default single-environment configuration |")

        # Branching Model
        rows.append("| Branching Model | Git-based with dev/test/prod branches | Standard branch-per-environment promotion |")
    else:
        rows.append("| Workspace Approach | Dev/Test/Prod workspaces | Environment isolation for safe promotion |")
        rows.append("| Environments | Dev + Prod (minimum) | Standard two-environment promotion pattern |")
        rows.append("| CI/CD Tool | fabric-cicd Python package | Standard deployment tool for Fabric items |")
        rows.append("| Parameterization | Environment Variables | Default configuration approach |")
        rows.append("| Branching Model | Git-based with dev/test/prod branches | Standard branch-per-environment promotion |")

    return rows

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

    # Build tradeoffs from unfiltered items (before alternatives are pruned)
    unfiltered_deploy = _build_deploy_items(diagram_items)
    tradeoffs_table = _build_tradeoffs_table(unfiltered_deploy)

    if decisions:
        diagram_items = _filter_by_decisions(diagram_items, decisions)

    deploy_items = _build_deploy_items(diagram_items)
    waves = _build_waves(deploy_items)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    manual_steps = sum(1 for di in deploy_items if di.portal_only)

    decisions_table = _build_decisions_table(decisions)
    alternatives_table = _build_alternatives_table(decisions)
    deployment_strategy = _build_deployment_strategy(decisions, task_flow)

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
        "> See: docs/discovery-brief.md",
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
    ])

    parts.extend(tradeoffs_table)

    parts.extend([
        "",
        "## Deployment Strategy",
        "",
        "| Decision | Choice | Rationale |",
        "|----------|--------|-----------|",
    ])

    parts.extend(deployment_strategy)

    parts.extend([
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
        description="Pre-fill architecture handoff from deployment registry"
    )
    parser.add_argument("--task-flow", required=True,
                        help="Task flow ID (e.g. medallion, lambda, event-analytics)")
    parser.add_argument("--project", required=True,
                        help="Project name")
    parser.add_argument("--decisions", default=None,
                        help="Path to decision-resolver output (JSON or legacy YAML)")
    parser.add_argument("--output", default=None,
                        help="Output file path (default: stdout)")
    args = parser.parse_args()

    decisions: dict | None = None
    if args.decisions:
        try:
            decisions = _load_decisions_file(args.decisions)
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
