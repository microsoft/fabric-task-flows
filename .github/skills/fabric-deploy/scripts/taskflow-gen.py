#!/usr/bin/env python3
"""
Generate Fabric workspace task flow JSON files for import into Microsoft Fabric.

Two modes:
  scaffold  — From a task-flow ID, reads diagrams/{task-flow}.md and generates
               a generic task flow JSON with consolidated tasks + edges.
  finalize  — From an architecture-handoff.md, reads actual items and generates
               a richer JSON with descriptive task names.

Usage:
    python .github/skills/fabric-deploy/scripts/taskflow-gen.py scaffold --task-flow medallion --project "My Project"
    python .github/skills/fabric-deploy/scripts/taskflow-gen.py scaffold --task-flow medallion --project "My Project" --output task-flow.json

    python .github/skills/fabric-deploy/scripts/taskflow-gen.py finalize --handoff projects/x/prd/architecture-handoff.md --project "My Project"
    python .github/skills/fabric-deploy/scripts/taskflow-gen.py finalize --handoff projects/x/prd/architecture-handoff.md --project "My Project" --output task-flow.json

Importable:
    from taskflow_gen import generate_scaffold, generate_finalize
    data = generate_scaffold("medallion", "My Project")
    data = generate_finalize("path/to/handoff.md", "My Project")
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

_SHARED_DIR = REPO_ROOT.parent.parent.parent / "_shared" / "lib"
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

# ── Item type → Fabric task type mapping ──────────────────────────────────────

# Task type mapping — loaded from _shared/registry/item-type-registry.json
# Do NOT maintain this dict manually. See CONTRIBUTING.md.
from registry_loader import build_task_type_map
from yaml_utils import extract_yaml_blocks
from diagram_parser import get_deployment_items

ITEM_TO_TASK_TYPE: dict[str, str] = build_task_type_map()

# Valid Fabric task types — derived from registry values (not hardcoded).
VALID_TASK_TYPES: set[str] = set(ITEM_TO_TASK_TYPE.values()) | {"general"}

# ── Scaffold-mode generic task names ──────────────────────────────────────

SCAFFOLD_TASK_NAMES: dict[str, str] = {
    "get data": "Ingest data",
    "mirror data": "Mirror data",
    "store data": "Store data",
    "prepare data": "Transform & prepare",
    "analyze and train data": "Train & analyze",
    "visualize": "Visualize & report",
    "track data": "Monitor & track",
    "distribute data": "Distribute & serve",
    "develop": "Configure environment",
    "govern data": "Govern & catalog",
    "general": "General",
}

# ── Canonical task-type ordering (for deterministic edge generation) ──────

TASK_TYPE_ORDER: dict[str, int] = {
    "develop": 0,
    "govern data": 1,
    "get data": 2,
    "mirror data": 3,
    "store data": 4,
    "prepare data": 5,
    "analyze and train data": 6,
    "track data": 7,
    "visualize": 8,
    "distribute data": 9,
    "general": 10,
}

# ── Data classes ──────────────────────────────────────────────────────────

@dataclass
class DiagramItem:
    order: str
    item_type: str
    depends_on: str
    is_alternative: bool = False


@dataclass
class HandoffItem:
    name: str
    item_type: str
    dependencies: list[str] = field(default_factory=list)


@dataclass
class TaskInfo:
    task_type: str
    task_id: str
    name: str
    source_items: list[str] = field(default_factory=list)


# ── Diagram parser — loads from JSON registry ─────────────────────────────


def _parse_diagram(task_flow: str) -> list[DiagramItem]:
    """Parse deployment order from the JSON registry for a task flow.
    
    Primary source: _shared/registry/deployment-order.json
    """
    json_items = get_deployment_items(task_flow)
    
    if not json_items:
        return []

    items: list[DiagramItem] = []
    
    for ji in json_items:
        is_alt = "alternativeGroup" in ji
        
        items.append(DiagramItem(
            order=ji["order"],
            item_type=ji["itemType"],
            depends_on=", ".join(ji.get("dependsOn", [])),
            is_alternative=is_alt,
        ))

    return items


# ── Handoff parser ────────────────────────────────────────────────────────

def _extract_yaml_blocks(markdown: str) -> list[str]:
    return extract_yaml_blocks(markdown)


def _parse_handoff_items(handoff_path: str) -> list[HandoffItem]:
    path = Path(handoff_path)
    if not path.is_absolute():
        path = REPO_ROOT / path
    text = path.read_text(encoding="utf-8")
    blocks = _extract_yaml_blocks(text)

    items: list[HandoffItem] = []
    for block in blocks:
        if "items_to_deploy:" not in block and "items:" not in block:
            continue
        items = _parse_items_yaml(block)
        if items:
            break
    return items


def _parse_items_yaml(yaml_text: str) -> list[HandoffItem]:
    items: list[HandoffItem] = []

    # Try inline format: - { name: ..., type: ... }
    for line in yaml_text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("- {"):
            mapping = _parse_inline_mapping(stripped[stripped.index("{"):])
            name = mapping.get("name", mapping.get("item_name", ""))
            item_type = mapping.get("type", mapping.get("item_type", ""))
            deps_raw = mapping.get("dependencies", mapping.get("depends_on", ""))
            deps = _parse_deps_value(deps_raw)
            if name and item_type:
                items.append(HandoffItem(name=name, item_type=item_type, dependencies=deps))

    if items:
        return items

    # Multi-line format
    current: dict[str, str] = {}
    for line in yaml_text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        if stripped.startswith("items_to_deploy:") or stripped.startswith("items:"):
            continue
        if stripped.startswith("- "):
            if current:
                items.append(_dict_to_handoff_item(current))
            current = {}
            rest = stripped[2:].strip()
            m = re.match(r"([\w_-]+)\s*:\s*(.*)", rest)
            if m:
                current[m.group(1)] = m.group(2).strip().strip('"').strip("'")
        elif ":" in stripped and current is not None:
            m = re.match(r"([\w_-]+)\s*:\s*(.*)", stripped)
            if m:
                current[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    if current:
        items.append(_dict_to_handoff_item(current))

    return items


def _parse_inline_mapping(s: str) -> dict[str, str]:
    s = s.strip().strip("{}")
    result: dict[str, str] = {}
    for part in re.split(r",\s*(?=\w+\s*:)", s):
        m = re.match(r"([\w_-]+)\s*:\s*(.*)", part.strip())
        if m:
            result[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return result


def _parse_deps_value(raw: str) -> list[str]:
    if not raw:
        return []
    raw = raw.strip()
    if raw.startswith("["):
        inner = raw[1:-1].strip()
        return [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()] if inner else []
    return [x.strip() for x in raw.split(",") if x.strip()]


def _dict_to_handoff_item(d: dict[str, str]) -> HandoffItem:
    name = d.get("name", d.get("item_name", ""))
    item_type = d.get("type", d.get("item_type", ""))
    deps = _parse_deps_value(d.get("dependencies", d.get("depends_on", "")))
    return HandoffItem(name=name, item_type=item_type, dependencies=deps)


# ── Task type resolution ─────────────────────────────────────────────────

def _resolve_task_type(item_type: str) -> str | None:
    if not item_type or not item_type.strip():
        return None
    if item_type in ITEM_TO_TASK_TYPE:
        return ITEM_TO_TASK_TYPE[item_type]
    parts = item_type.strip().split()
    if parts:
        base = parts[0]
        if base in ITEM_TO_TASK_TYPE:
            return ITEM_TO_TASK_TYPE[base]
    normalized = item_type.replace(" ", "").replace("-", "").replace("_", "")
    for key, val in ITEM_TO_TASK_TYPE.items():
        if key.replace(" ", "").replace("-", "").replace("_", "").lower() == normalized.lower():
            return val
    return None


# ── Scaffold mode name refinement ─────────────────────────────────────────

def _scaffold_task_name(task_type: str, item_types: list[str]) -> str:
    storage_types = {t for t in item_types if _resolve_task_type(t) == "store data"}
    if task_type == "store data" and storage_types:
        bases = set()
        for st in storage_types:
            base = st.split()[0] if " " in st else st
            bases.add(base)
        if len(bases) == 1:
            return f"Store in {next(iter(bases))}"
        return "Store — " + " & ".join(sorted(bases))
    return SCAFFOLD_TASK_NAMES.get(task_type, task_type.title())


# ── Finalize mode descriptive names ───────────────────────────────────────

_FINALIZE_VERB: dict[str, str] = {
    "get data": "Ingest",
    "mirror data": "Mirror",
    "store data": "Store",
    "prepare data": "Transform",
    "analyze and train data": "Train",
    "visualize": "Visualize",
    "track data": "Monitor",
    "distribute data": "Serve",
    "develop": "Configure",
    "govern data": "Govern",
    "general": "Process",
}


def _finalize_task_name(task_type: str, item_names: list[str]) -> str:
    verb = _FINALIZE_VERB.get(task_type, task_type.title())
    if not item_names:
        return SCAFFOLD_TASK_NAMES.get(task_type, verb)
    summary = " & ".join(item_names[:4])
    if len(item_names) > 4:
        summary += f" +{len(item_names) - 4} more"
    return f"{verb} — {summary}"


# ── UUID generation ───────────────────────────────────────────────────────

def _deterministic_uuid(task_flow: str, task_type: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{task_flow}.{task_type}"))


def _random_uuid() -> str:
    return str(uuid.uuid4())


# ── Edge generation ───────────────────────────────────────────────────────

def _fuzzy_resolve_task_type(ref: str, known_item_types: list[str]) -> str | None:
    """Resolve a dependency reference to a task type using fuzzy word matching."""
    direct = _resolve_task_type(ref)
    if direct:
        return direct

    ref_words = set(re.findall(r"[a-z]+", ref.lower()))
    best_match: str | None = None
    best_overlap = 0
    for known in known_item_types:
        known_words = set(re.findall(r"[a-z]+", known.lower()))
        overlap = len(ref_words & known_words)
        if overlap > best_overlap:
            best_overlap = overlap
            best_match = known
    if best_match and best_overlap >= 1:
        return _resolve_task_type(best_match)
    return None


def _orient_edge(source: str, target: str) -> tuple[str, str] | None:
    """Ensure data-flow direction. Returns None to drop non-data-flow edges."""
    if source == "store data" and target == "get data":
        return ("get data", "store data")
    if target == "develop":
        return None
    return (source, target)


def _build_edges_from_diagram(
    diagram_items: list[DiagramItem],
    task_map: dict[str, TaskInfo],
) -> list[dict[str, str]]:
    """Build edges from item-level dependencies, lifting to task-type level."""
    known_item_types = list({di.item_type for di in diagram_items})

    edge_pairs: set[tuple[str, str]] = set()

    for di in diagram_items:
        if di.is_alternative:
            continue
        target_task_type = _resolve_task_type(di.item_type)
        if not target_task_type or target_task_type not in task_map:
            continue

        dep_text = di.depends_on.strip()
        if not dep_text or re.match(r"\(none[\s\-—]", dep_text, re.IGNORECASE) or dep_text.lower() == "(optional)":
            continue

        dep_refs = [d.strip() for d in re.split(r"[,/]|\bOR\b|\band\b", dep_text, flags=re.IGNORECASE) if d.strip()]
        for dep_ref in dep_refs:
            clean_ref = re.sub(r"\(.*?\)", "", dep_ref).strip()
            clean_ref = re.sub(r"Sem(?:antic)?\s*Model", "Semantic Model", clean_ref)
            clean_ref = re.sub(r"Evthouse", "Eventhouse", clean_ref)
            clean_ref = re.sub(r"Environmt|Env\b", "Environment", clean_ref)
            clean_ref = re.sub(r"Report\(s\)", "Report", clean_ref)
            clean_ref = re.sub(r"Reports?$", "Report", clean_ref)

            source_task_type = _fuzzy_resolve_task_type(clean_ref, known_item_types)

            if source_task_type and source_task_type != target_task_type and source_task_type in task_map:
                pair = _orient_edge(source_task_type, target_task_type)
                if pair:
                    edge_pairs.add(pair)

    return _pairs_to_edges(edge_pairs, task_map)


def _build_edges_from_handoff(
    handoff_items: list[HandoffItem],
    task_map: dict[str, TaskInfo],
) -> list[dict[str, str]]:
    """Build edges from handoff item dependencies, lifting to task-type level."""
    name_to_type: dict[str, str] = {}
    all_item_types: list[str] = []
    for hi in handoff_items:
        task_type = _resolve_task_type(hi.item_type)
        if task_type:
            name_to_type[hi.name.lower()] = task_type
            # Also index by words for fuzzy matching
            for word in re.findall(r"[a-z]+", hi.name.lower()):
                if len(word) > 3:
                    name_to_type.setdefault(word, task_type)
            all_item_types.append(hi.item_type)

    edge_pairs: set[tuple[str, str]] = set()

    for hi in handoff_items:
        target_task_type = _resolve_task_type(hi.item_type)
        if not target_task_type or target_task_type not in task_map:
            continue
        for dep_name in hi.dependencies:
            dep_lower = dep_name.lower().strip()
            source_task_type = name_to_type.get(dep_lower)
            if not source_task_type:
                # Try fuzzy: match individual words against known items
                source_task_type = _fuzzy_resolve_task_type(dep_name, all_item_types)
            if not source_task_type:
                # Try partial word match: "Lakehouses" → "lakehouse"
                for known_name, known_type in name_to_type.items():
                    if dep_lower.startswith(known_name) or known_name.startswith(dep_lower):
                        source_task_type = known_type
                        break
            if source_task_type and source_task_type != target_task_type and source_task_type in task_map:
                pair = _orient_edge(source_task_type, target_task_type)
                if pair:
                    edge_pairs.add(pair)

    # Fallback: if we found few edges, add standard data flow edges
    # for task types that exist in this flow
    present_types = set(task_map.keys())
    if len(edge_pairs) < 2:
        standard_flow = [
            ("get data", "store data"),
            ("store data", "prepare data"),
            ("store data", "visualize"),
            ("store data", "analyze and train data"),
            ("store data", "track data"),
            ("prepare data", "visualize"),
            ("prepare data", "analyze and train data"),
            ("develop", "prepare data"),
            ("develop", "analyze and train data"),
        ]
        for src, tgt in standard_flow:
            if src in present_types and tgt in present_types:
                edge_pairs.add((src, tgt))

    return _pairs_to_edges(edge_pairs, task_map)


def _pairs_to_edges(
    pairs: set[tuple[str, str]],
    task_map: dict[str, TaskInfo],
) -> list[dict[str, str]]:
    edges: list[dict[str, str]] = []
    for source_type, target_type in sorted(pairs, key=lambda p: (TASK_TYPE_ORDER.get(p[0], 99), TASK_TYPE_ORDER.get(p[1], 99))):
        edges.append({
            "source": task_map[source_type].task_id,
            "target": task_map[target_type].task_id,
        })
    return edges


# ── Fallback minimal task flow ────────────────────────────────────────────

def _minimal_task_flow(project: str, task_flow: str) -> dict:
    tasks_info = [
        TaskInfo("get data", _deterministic_uuid(task_flow, "get data"), "Ingest data"),
        TaskInfo("store data", _deterministic_uuid(task_flow, "store data"), "Store data"),
        TaskInfo("visualize", _deterministic_uuid(task_flow, "visualize"), "Visualize & report"),
    ]
    return {
        "tasks": [{"type": t.task_type, "id": t.task_id, "name": t.name} for t in tasks_info],
        "edges": [
            {"source": tasks_info[0].task_id, "target": tasks_info[1].task_id},
            {"source": tasks_info[1].task_id, "target": tasks_info[2].task_id},
        ],
        "name": project,
        "description": f"Task flow for {project} ({task_flow})",
    }


# ── Public API: scaffold ──────────────────────────────────────────────────

def generate_scaffold(task_flow: str, project: str) -> dict:
    """Generate a task flow JSON dict from a deployment diagram.

    Args:
        task_flow: Task flow ID (e.g. 'medallion', 'lambda').
        project: Human-readable project name.

    Returns:
        Dict matching the Fabric task flow JSON schema.
    """
    diagram_items = _parse_diagram(task_flow)
    if not diagram_items:
        return _minimal_task_flow(project, task_flow)

    # Group non-alternative items by task type
    type_to_items: dict[str, list[str]] = {}
    for di in diagram_items:
        if di.is_alternative:
            continue
        task_type = _resolve_task_type(di.item_type)
        if task_type:
            type_to_items.setdefault(task_type, []).append(di.item_type)

    if not type_to_items:
        return _minimal_task_flow(project, task_flow)

    # Build consolidated tasks
    task_map: dict[str, TaskInfo] = {}
    for task_type in sorted(type_to_items, key=lambda t: TASK_TYPE_ORDER.get(t, 99)):
        item_types = type_to_items[task_type]
        task_id = _deterministic_uuid(task_flow, task_type)
        name = _scaffold_task_name(task_type, item_types)
        task_map[task_type] = TaskInfo(
            task_type=task_type,
            task_id=task_id,
            name=name,
            source_items=item_types,
        )

    edges = _build_edges_from_diagram(diagram_items, task_map)

    tasks = [
        {"type": t.task_type, "id": t.task_id, "name": t.name}
        for t in sorted(task_map.values(), key=lambda t: TASK_TYPE_ORDER.get(t.task_type, 99))
    ]

    return {
        "tasks": tasks,
        "edges": edges,
        "name": project,
        "description": f"Task flow for {project} ({task_flow})",
    }


# ── Public API: finalize ──────────────────────────────────────────────────

def generate_finalize(handoff_path: str, project: str) -> dict:
    """Generate a task flow JSON dict from an architecture handoff.

    Args:
        handoff_path: Path to architecture-handoff.md.
        project: Human-readable project name.

    Returns:
        Dict matching the Fabric task flow JSON schema.
    """
    handoff_items = _parse_handoff_items(handoff_path)
    if not handoff_items:
        print(f"⚠ No items found in {handoff_path}, generating minimal task flow", file=sys.stderr)
        return _minimal_task_flow(project, "unknown")

    # Group items by task type
    type_to_names: dict[str, list[str]] = {}
    for hi in handoff_items:
        task_type = _resolve_task_type(hi.item_type)
        if task_type:
            type_to_names.setdefault(task_type, []).append(hi.name)

    if not type_to_names:
        return _minimal_task_flow(project, "unknown")

    task_map: dict[str, TaskInfo] = {}
    for task_type in sorted(type_to_names, key=lambda t: TASK_TYPE_ORDER.get(t, 99)):
        item_names = type_to_names[task_type]
        task_id = _random_uuid()
        name = _finalize_task_name(task_type, item_names)
        task_map[task_type] = TaskInfo(
            task_type=task_type,
            task_id=task_id,
            name=name,
            source_items=item_names,
        )

    edges = _build_edges_from_handoff(handoff_items, task_map)

    tasks = [
        {"type": t.task_type, "id": t.task_id, "name": t.name}
        for t in sorted(task_map.values(), key=lambda t: TASK_TYPE_ORDER.get(t.task_type, 99))
    ]

    return {
        "tasks": tasks,
        "edges": edges,
        "name": project,
        "description": f"Task flow for {project}",
    }


# ── CLI ───────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Fabric workspace task flow JSON files"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    sp_scaffold = subparsers.add_parser("scaffold",
        help="Generate from deployment diagram")
    sp_scaffold.add_argument("--task-flow", required=True,
        help="Task flow ID (e.g. medallion, lambda, event-analytics)")
    sp_scaffold.add_argument("--project", required=True,
        help="Project name (used as task flow name)")
    sp_scaffold.add_argument("--output", default=None,
        help="Output file path (default: stdout)")

    sp_finalize = subparsers.add_parser("finalize",
        help="Generate from architecture handoff")
    sp_finalize.add_argument("--handoff", required=True,
        help="Path to architecture-handoff.md")
    sp_finalize.add_argument("--project", required=True,
        help="Project name (used as task flow name)")
    sp_finalize.add_argument("--output", default=None,
        help="Output file path (default: stdout)")

    args = parser.parse_args()

    try:
        if args.command == "scaffold":
            result = generate_scaffold(args.task_flow, args.project)
        else:
            result = generate_finalize(args.handoff, args.project)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    output_json = json.dumps(result, indent=4, ensure_ascii=False)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output_json + "\n", encoding="utf-8")
        print(f"Wrote task flow JSON to {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
