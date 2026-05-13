#!/usr/bin/env python3
"""
Generate Fabric workspace task flow JSON files for import into Microsoft Fabric.

Three modes:
  scaffold  — From a task-flow ID, reads deployment order metadata and generates
               a generic task flow JSON with consolidated tasks + edges.
  finalize  — From an architecture-handoff.md, reads actual items and generates
               a richer JSON with descriptive task names.
  template  — From an architecture-handoff.md, generates an item-level task flow
               JSON template for Fabric workspace import.

Usage:
    python .github/skills/fabric-deploy/scripts/taskflow-gen.py scaffold --task-flow medallion --project "My Project"
    python .github/skills/fabric-deploy/scripts/taskflow-gen.py finalize --handoff projects/x/docs/architecture-handoff.md --project "My Project"
    python .github/skills/fabric-deploy/scripts/taskflow-gen.py template --handoff projects/x/docs/architecture-handoff.md --project "My Project"

Importable:
    from taskflow_gen import generate_scaffold, generate_finalize, generate_taskflow_json, parse_handoff
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_SKILL_DIR = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "_shared" / "lib"))

from registry_loader import build_task_type_map, build_display_names, get_deployment_items
from yaml_utils import (
    extract_task_flow as _shared_extract_task_flow,
    extract_yaml_blocks,
    parse_inline_mapping as _shared_parse_inline_mapping,
    parse_yaml_value,
)

ITEM_TO_TASK_TYPE: dict[str, str] = build_task_type_map()
_DISPLAY_NAMES: dict[str, str] = build_display_names()


def _display_name(item_type: str) -> str:
    """Resolve a registry key or role-qualified name to its display name."""
    return _DISPLAY_NAMES.get(item_type.lower(), item_type)
TASK_TYPE_MAP: dict[str, str] = ITEM_TO_TASK_TYPE

SCAFFOLD_TASK_NAMES: dict[str, str] = {
    "get data": "Ingest data",
    "mirror data": "Mirror data",
    "store data": "Store data",
    "prepare data": "Transform & prepare",
    "analyze and train data": "Train & analyze",
    "visualize": "Visualize & report",
    "track data": "Monitor & track",
    "distribute data": "Distribute & serve",
    "develop data": "Configure environment",
    "general": "General",
}

TASK_TYPE_ORDER: dict[str, int] = {
    "develop data": 0,
    "get data": 1,
    "mirror data": 2,
    "store data": 3,
    "prepare data": 4,
    "analyze and train data": 5,
    "track data": 6,
    "visualize": 7,
    "distribute data": 8,
    "general": 9,
}


@dataclass
class DiagramItem:
    order: str
    item_type: str
    depends_on: str
    is_alternative: bool = False


@dataclass(init=False)
class Item:
    id: int = 0
    name: str = ""
    item_type: str = ""
    dependencies: list[Any] = field(default_factory=list)
    purpose: str = ""

    def __init__(
        self,
        id: int = 0,
        name: str = "",
        type: str = "",
        item_type: str = "",
        depends_on: list[Any] | None = None,
        dependencies: list[Any] | None = None,
        purpose: str = "",
    ) -> None:
        self.id = _coerce_item_id(id)
        self.name = str(name)
        self.item_type = str(item_type or type)
        self.dependencies = list(dependencies if dependencies is not None else (depends_on or []))
        self.purpose = str(purpose)

    @property
    def type(self) -> str:
        return self.item_type

    @type.setter
    def type(self, value: str) -> None:
        self.item_type = str(value)

    @property
    def depends_on(self) -> list[Any]:
        return self.dependencies

    @depends_on.setter
    def depends_on(self, value: list[Any] | None) -> None:
        self.dependencies = list(value or [])


HandoffItem = Item


@dataclass
class HandoffData:
    task_flow: str
    items: list[Item]
    project: str = ""


@dataclass
class TaskInfo:
    task_type: str
    task_id: str
    name: str
    source_items: list[str] = field(default_factory=list)


def _coerce_item_id(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return 0


def _extract_task_flow(markdown: str) -> str:
    return _shared_extract_task_flow(markdown) or "unknown"


def _extract_project_name(markdown: str) -> str:
    match = re.search(r"^project:\s*(.+)$", markdown, re.MULTILINE)
    if not match:
        return ""
    return match.group(1).strip().strip('"').strip("'")


def _parse_inline_mapping(s: str) -> dict[str, Any]:
    return _shared_parse_inline_mapping(s)


def _parse_deps_value(raw: Any) -> list[Any]:
    if raw in (None, ""):
        return []
    if isinstance(raw, list):
        return [item for item in raw if item not in (None, "")]
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return [int(raw) if isinstance(raw, float) and raw.is_integer() else raw]

    text = str(raw).strip()
    if not text:
        return []

    parsed = parse_yaml_value(text)
    if isinstance(parsed, list):
        return [item for item in parsed if item not in (None, "")]
    if parsed in (None, ""):
        return []
    return [item.strip() for item in text.split(",") if item.strip()]


def _dict_to_handoff_item(d: dict[str, Any]) -> HandoffItem:
    return HandoffItem(
        id=_coerce_item_id(d.get("id", 0)),
        name=d.get("name", d.get("item_name", "")),
        item_type=d.get("type", d.get("item_type", "")),
        dependencies=_parse_deps_value(d.get("dependencies", d.get("depends_on", []))),
        purpose=d.get("purpose", ""),
    )


def _dict_to_item(d: dict[str, Any]) -> Item:
    return Item(
        id=_coerce_item_id(d.get("id", 0)),
        name=d.get("name", d.get("item_name", "")),
        item_type=d.get("type", d.get("item_type", "")),
        dependencies=_parse_deps_value(d.get("depends_on", d.get("dependencies", []))),
        purpose=d.get("purpose", ""),
    )


def _extract_items_section(yaml_text: str) -> str:
    lines = yaml_text.splitlines()
    header_index: int | None = None
    header_indent = 0

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("items_to_deploy:") or stripped.startswith("items:"):
            header_index = idx
            header_indent = len(line) - len(line.lstrip())
            break

    if header_index is None:
        return yaml_text

    collected: list[str] = []
    for line in lines[header_index + 1:]:
        stripped = line.strip()
        if not stripped:
            collected.append(line)
            continue
        if stripped.startswith("#"):
            collected.append(line)
            continue
        indent = len(line) - len(line.lstrip())
        if indent <= header_indent and re.match(r"^[\w-]+\s*:", stripped):
            break
        collected.append(line)
    return "\n".join(collected)


def _parse_item_entries(yaml_text: str) -> list[dict[str, Any]]:
    section = _extract_items_section(yaml_text)
    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for line in section.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            if current:
                entries.append(current)
            rest = stripped[2:].strip()
            if rest.startswith("{") and rest.endswith("}"):
                current = _parse_inline_mapping(rest)
                continue
            current = {}
            match = re.match(r"([\w_-]+)\s*:\s*(.*)", rest)
            if match:
                key, value = match.groups()
                current[key] = parse_yaml_value(value)
            continue
        if current is not None and ":" in stripped:
            match = re.match(r"([\w_-]+)\s*:\s*(.*)", stripped)
            if match:
                key, value = match.groups()
                current[key] = parse_yaml_value(value)

    if current:
        entries.append(current)
    return entries


def _parse_items_yaml(yaml_text: str) -> list[HandoffItem]:
    return [_dict_to_handoff_item(entry) for entry in _parse_item_entries(yaml_text)]


def _parse_items_block(yaml_text: str) -> list[Item]:
    return [_dict_to_item(entry) for entry in _parse_item_entries(yaml_text)]


def parse_handoff(path: str) -> HandoffData:
    handoff_path = Path(path)
    if not handoff_path.is_absolute():
        handoff_path = _SKILL_DIR / handoff_path

    content = handoff_path.read_text(encoding="utf-8")
    task_flow = _extract_task_flow(content)
    project = _extract_project_name(content)

    items: list[Item] = []
    for block in extract_yaml_blocks(content):
        parsed = _parse_items_block(block)
        if parsed:
            items = parsed
            break

    return HandoffData(task_flow=task_flow, items=items, project=project)


def _parse_diagram(task_flow: str) -> list[DiagramItem]:
    json_items = get_deployment_items(task_flow)
    if not json_items:
        return []

    items: list[DiagramItem] = []
    for ji in json_items:
        items.append(DiagramItem(
            order=ji["order"],
            item_type=_display_name(ji["itemType"]),
            depends_on=", ".join(_display_name(d) for d in ji.get("dependsOn", [])),
            is_alternative="alternativeGroup" in ji,
        ))
    return items


def _parse_handoff_items(handoff_path: str) -> list[HandoffItem]:
    return [HandoffItem(
        id=item.id,
        name=item.name,
        item_type=item.item_type,
        dependencies=list(item.dependencies),
        purpose=item.purpose,
    ) for item in parse_handoff(handoff_path).items]


def _resolve_task_type_core(item_type: str, fallback: str | None = None) -> str | None:
    if not item_type or not str(item_type).strip():
        return fallback

    candidate = str(item_type).strip()
    if candidate in ITEM_TO_TASK_TYPE:
        return ITEM_TO_TASK_TYPE[candidate]

    base = candidate.split()[0]
    if base in ITEM_TO_TASK_TYPE:
        return ITEM_TO_TASK_TYPE[base]

    normalized = re.sub(r"[\s_-]+", "", candidate).lower()
    for key, value in ITEM_TO_TASK_TYPE.items():
        if re.sub(r"[\s_-]+", "", key).lower() == normalized:
            return value
    return fallback


def _resolve_task_type(item_type: str) -> str | None:
    fallback = "general" if __name__ == "taskflow_template_gen" else None
    return _resolve_task_type_core(item_type, fallback=fallback)


def _scaffold_task_name(task_type: str, item_types: list[str]) -> str:
    storage_types = {item_type for item_type in item_types if _resolve_task_type_core(item_type) == "store data"}
    if task_type == "store data" and storage_types:
        bases = {storage_type.split()[0] if " " in storage_type else storage_type for storage_type in storage_types}
        if len(bases) == 1:
            return f"Store in {next(iter(bases))}"
        return "Store — " + " & ".join(sorted(bases))
    return SCAFFOLD_TASK_NAMES.get(task_type, task_type.title())


_FINALIZE_VERB: dict[str, str] = {
    "get data": "Ingest",
    "mirror data": "Mirror",
    "store data": "Store",
    "prepare data": "Transform",
    "analyze and train data": "Train",
    "visualize": "Visualize",
    "track data": "Monitor",
    "distribute data": "Serve",
    "develop data": "Configure",
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


def _deterministic_uuid(task_flow: str, task_type: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{task_flow}.{task_type}"))


def _random_uuid() -> str:
    return str(uuid.uuid4())


def _generate_task_id() -> str:
    return _random_uuid()


def _fuzzy_resolve_task_type(ref: str, known_item_types: list[str]) -> str | None:
    direct = _resolve_task_type_core(ref)
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
        return _resolve_task_type_core(best_match)
    return None


def _orient_edge(source: str, target: str) -> tuple[str, str] | None:
    if source == "store data" and target == "get data":
        return ("get data", "store data")
    if target == "develop data":
        return None
    return (source, target)


def _pairs_to_edges(
    pairs: set[tuple[str, str]],
    task_map: dict[str, TaskInfo],
) -> list[dict[str, str]]:
    edges: list[dict[str, str]] = []
    for source_type, target_type in sorted(
        pairs,
        key=lambda pair: (TASK_TYPE_ORDER.get(pair[0], 99), TASK_TYPE_ORDER.get(pair[1], 99)),
    ):
        edges.append({
            "source": task_map[source_type].task_id,
            "target": task_map[target_type].task_id,
        })
    return edges


def _build_edges_from_diagram(
    diagram_items: list[DiagramItem],
    task_map: dict[str, TaskInfo],
) -> list[dict[str, str]]:
    known_item_types = list({di.item_type for di in diagram_items})
    edge_pairs: set[tuple[str, str]] = set()

    for di in diagram_items:
        if di.is_alternative:
            continue
        target_task_type = _resolve_task_type_core(di.item_type)
        if not target_task_type or target_task_type not in task_map:
            continue

        dep_text = di.depends_on.strip()
        if not dep_text or re.match(r"\(none[\s\-—]", dep_text, re.IGNORECASE) or dep_text.lower() == "(optional)":
            continue

        dep_refs = [dep.strip() for dep in re.split(r"[,/]|\bOR\b|\band\b", dep_text, flags=re.IGNORECASE) if dep.strip()]
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
    name_to_type: dict[str, str] = {}
    id_to_type: dict[int, str] = {}
    all_item_types: list[str] = []

    for hi in handoff_items:
        task_type = _resolve_task_type_core(hi.item_type)
        if not task_type:
            continue
        if hi.id:
            id_to_type[hi.id] = task_type
        name_to_type[hi.name.lower()] = task_type
        for word in re.findall(r"[a-z]+", hi.name.lower()):
            if len(word) > 3:
                name_to_type.setdefault(word, task_type)
        all_item_types.append(hi.item_type)

    edge_pairs: set[tuple[str, str]] = set()

    for hi in handoff_items:
        target_task_type = _resolve_task_type_core(hi.item_type)
        if not target_task_type or target_task_type not in task_map:
            continue

        for dep_name in hi.dependencies:
            source_task_type: str | None = None
            if isinstance(dep_name, int):
                source_task_type = id_to_type.get(dep_name)
            else:
                dep_lower = str(dep_name).lower().strip()
                source_task_type = name_to_type.get(dep_lower)
                if not source_task_type:
                    source_task_type = _fuzzy_resolve_task_type(str(dep_name), all_item_types)
                if not source_task_type:
                    for known_name, known_type in name_to_type.items():
                        if dep_lower.startswith(known_name) or known_name.startswith(dep_lower):
                            source_task_type = known_type
                            break

            if source_task_type and source_task_type != target_task_type and source_task_type in task_map:
                pair = _orient_edge(source_task_type, target_task_type)
                if pair:
                    edge_pairs.add(pair)

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
            ("develop data", "prepare data"),
            ("develop data", "analyze and train data"),
        ]
        for source, target in standard_flow:
            if source in present_types and target in present_types:
                edge_pairs.add((source, target))

    return _pairs_to_edges(edge_pairs, task_map)


def _minimal_task_flow(project: str, task_flow: str) -> dict:
    tasks_info = [
        TaskInfo("get data", _deterministic_uuid(task_flow, "get data"), "Ingest data"),
        TaskInfo("store data", _deterministic_uuid(task_flow, "store data"), "Store data"),
        TaskInfo("visualize", _deterministic_uuid(task_flow, "visualize"), "Visualize & report"),
    ]
    return {
        "tasks": [{"type": task.task_type, "id": task.task_id, "name": task.name} for task in tasks_info],
        "edges": [
            {"source": tasks_info[0].task_id, "target": tasks_info[1].task_id},
            {"source": tasks_info[1].task_id, "target": tasks_info[2].task_id},
        ],
        "name": project,
        "description": f"Task flow for {project} ({task_flow})",
    }


def generate_scaffold(task_flow: str, project: str) -> dict:
    diagram_items = _parse_diagram(task_flow)
    if not diagram_items:
        return _minimal_task_flow(project, task_flow)

    type_to_items: dict[str, list[str]] = {}
    for di in diagram_items:
        if di.is_alternative:
            continue
        task_type = _resolve_task_type_core(di.item_type)
        if task_type:
            type_to_items.setdefault(task_type, []).append(di.item_type)

    if not type_to_items:
        return _minimal_task_flow(project, task_flow)

    task_map: dict[str, TaskInfo] = {}
    for task_type in sorted(type_to_items, key=lambda value: TASK_TYPE_ORDER.get(value, 99)):
        item_types = type_to_items[task_type]
        task_map[task_type] = TaskInfo(
            task_type=task_type,
            task_id=_deterministic_uuid(task_flow, task_type),
            name=_scaffold_task_name(task_type, item_types),
            source_items=item_types,
        )

    tasks = [
        {"type": task.task_type, "id": task.task_id, "name": task.name}
        for task in sorted(task_map.values(), key=lambda value: TASK_TYPE_ORDER.get(value.task_type, 99))
    ]

    return {
        "tasks": tasks,
        "edges": _build_edges_from_diagram(diagram_items, task_map),
        "name": project,
        "description": f"Task flow for {project} ({task_flow})",
    }


def generate_finalize(handoff_path: str, project: str) -> dict:
    handoff_items = _parse_handoff_items(handoff_path)
    if not handoff_items:
        print(f"⚠ No items found in {handoff_path}, generating minimal task flow", file=sys.stderr)
        return _minimal_task_flow(project, "unknown")

    type_to_names: dict[str, list[str]] = {}
    for hi in handoff_items:
        task_type = _resolve_task_type_core(hi.item_type)
        if task_type:
            type_to_names.setdefault(task_type, []).append(hi.name)

    if not type_to_names:
        return _minimal_task_flow(project, "unknown")

    task_map: dict[str, TaskInfo] = {}
    for task_type in sorted(type_to_names, key=lambda value: TASK_TYPE_ORDER.get(value, 99)):
        item_names = type_to_names[task_type]
        task_map[task_type] = TaskInfo(
            task_type=task_type,
            task_id=_random_uuid(),
            name=_finalize_task_name(task_type, item_names),
            source_items=item_names,
        )

    tasks = [
        {"type": task.task_type, "id": task.task_id, "name": task.name}
        for task in sorted(task_map.values(), key=lambda value: TASK_TYPE_ORDER.get(value.task_type, 99))
    ]

    return {
        "tasks": tasks,
        "edges": _build_edges_from_handoff(handoff_items, task_map),
        "name": project,
        "description": f"Task flow for {project}",
    }


def _normalize_lookup_key(value: str) -> str:
    return value.lower().replace("-", "").replace("_", "").replace(" ", "")


def generate_taskflow_json(data: HandoffData, project_name: str = "") -> dict:
    tasks: list[dict[str, str]] = []
    item_id_to_task_id: dict[int, str] = {}

    for item in data.items:
        task_id = _generate_task_id()
        item_id_to_task_id[item.id] = task_id
        task_type = _resolve_task_type_core(item.type, fallback="general")
        description = item.purpose or f"{item.type} for {project_name or data.task_flow}"
        tasks.append({
            "type": task_type,
            "id": task_id,
            "name": item.name,
            "description": description,
        })

    edges: list[dict[str, str]] = []
    name_to_id: dict[str, int] = {}
    for item in data.items:
        name_to_id[_normalize_lookup_key(item.type)] = item.id
        name_to_id[_normalize_lookup_key(f"{item.type} {item.name}")] = item.id
        name_to_id[_normalize_lookup_key(item.name)] = item.id
        for part in item.name.replace("-", " ").replace("_", " ").split():
            name_to_id[_normalize_lookup_key(f"{item.type} {part}")] = item.id

    for item in data.items:
        target_task_id = item_id_to_task_id.get(item.id)
        if not target_task_id:
            continue
        for dep in item.depends_on:
            source_item_id: int | None = None
            if isinstance(dep, int):
                source_item_id = dep
            else:
                try:
                    source_item_id = int(str(dep))
                except ValueError:
                    source_item_id = name_to_id.get(_normalize_lookup_key(str(dep)))
            source_task_id = item_id_to_task_id.get(source_item_id)
            if source_task_id:
                edges.append({"source": source_task_id, "target": target_task_id})

    flow_name = project_name or data.task_flow.replace("-", " ").title()
    flow_description = (
        f"Task flow for {flow_name} — {data.task_flow} architecture pattern. "
        f"{len(tasks)} items with dependency-ordered connections."
    )

    return {
        "tasks": tasks,
        "edges": edges,
        "name": flow_name,
        "description": flow_description,
    }


def _default_template_output(handoff: str, project_name: str) -> Path:
    handoff_dir = Path(handoff).parent.parent / "deploy"
    slug = project_name.lower().replace(" ", "-")
    return handoff_dir / f"taskflow-{slug}.json"


def _write_taskflow_output(
    data: dict,
    output: str | None,
    *,
    indent: int,
    trailing_newline: bool,
    message: str | None = None,
    message_stream: Any | None = None,
) -> None:
    text = json.dumps(data, indent=indent, ensure_ascii=False)
    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        suffix = "\n" if trailing_newline else ""
        out_path.write_text(text + suffix, encoding="utf-8", newline="\n")
        if message:
            print(message.format(path=output), file=message_stream or sys.stdout)
        return
    print(text)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Fabric workspace task flow JSON files")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scaffold_parser = subparsers.add_parser("scaffold", help="Generate from deployment diagram")
    scaffold_parser.add_argument("--task-flow", required=True, help="Task flow ID (e.g. medallion, lambda, event-analytics)")
    scaffold_parser.add_argument("--project", required=True, help="Project name (used as task flow name)")
    scaffold_parser.add_argument("--output", default=None, help="Output file path (default: stdout)")

    finalize_parser = subparsers.add_parser("finalize", help="Generate from architecture handoff")
    finalize_parser.add_argument("--handoff", required=True, help="Path to architecture-handoff.md")
    finalize_parser.add_argument("--project", required=True, help="Project name (used as task flow name)")
    finalize_parser.add_argument("--output", default=None, help="Output file path (default: stdout)")

    template_parser = subparsers.add_parser("template", help="Generate item-level task flow JSON from architecture handoff")
    template_parser.add_argument("--handoff", required=True, help="Path to architecture-handoff.md")
    template_parser.add_argument("--project", default="", help="Project display name")
    template_parser.add_argument("--output", default="", help="Output JSON path (default: alongside handoff)")

    return parser


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    argv = list(sys.argv[1:] if argv is None else argv)
    commands = {"scaffold", "finalize", "template"}
    if argv and argv[0] not in commands:
        legacy_parser = argparse.ArgumentParser(description="Generate Fabric Task Flow JSON from architecture handoff")
        legacy_parser.add_argument("--handoff", required=True, help="Path to architecture-handoff.md")
        legacy_parser.add_argument("--project", default="", help="Project display name")
        legacy_parser.add_argument("--output", default="", help="Output JSON path (default: alongside handoff)")
        args = legacy_parser.parse_args(argv)
        args.command = "template"
        return args
    return _build_parser().parse_args(argv)


def main() -> None:
    args = _parse_args()

    try:
        if args.command == "scaffold":
            result = generate_scaffold(args.task_flow, args.project)
            _write_taskflow_output(
                result,
                args.output,
                indent=4,
                trailing_newline=True,
                message="Wrote task flow JSON to {path}",
                message_stream=sys.stderr,
            )
        elif args.command == "finalize":
            result = generate_finalize(args.handoff, args.project)
            _write_taskflow_output(
                result,
                args.output,
                indent=4,
                trailing_newline=True,
                message="Wrote task flow JSON to {path}",
                message_stream=sys.stderr,
            )
        else:
            data = parse_handoff(args.handoff)
            if not data.items:
                print("❌ No items found in handoff", file=sys.stderr)
                sys.exit(1)
            project_name = args.project or data.project or data.task_flow.replace("-", " ").title()
            output_path = args.output or str(_default_template_output(args.handoff, project_name))
            result = generate_taskflow_json(data, project_name)
            _write_taskflow_output(
                result,
                output_path,
                indent=2,
                trailing_newline=False,
                message="✅ {path}",
            )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
