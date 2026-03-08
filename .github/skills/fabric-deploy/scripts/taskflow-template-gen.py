#!/usr/bin/env python3
"""
Generate a Fabric Task Flow JSON template from an architecture handoff.

Produces a JSON file importable into Microsoft Fabric workspaces via
Settings → Task flow → Import. The template defines tasks (nodes) and
edges (connections) that visualize item dependencies in the workspace.

Usage:
    python taskflow-template-gen.py --handoff projects/my-project/prd/architecture-handoff.md --project "My Project"
    python taskflow-template-gen.py --handoff projects/my-project/prd/architecture-handoff.md --project "My Project" --output projects/my-project/deployments/taskflow.json

Reference: https://learn.microsoft.com/en-us/fabric/fundamentals/task-flow-overview
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent

# Load task_type mappings from item registry
sys.path.insert(0, str(REPO_ROOT / "_shared"))
REGISTRY = json.loads((REPO_ROOT / "_shared" / "item-type-registry.json").read_text(encoding="utf-8"))

TASK_TYPE_MAP: dict[str, str] = {}
for type_name, type_info in REGISTRY["types"].items():
    tt = type_info.get("task_type", "general")
    key = type_name.lower().replace(" ", "").replace("-", "").replace("_", "")
    TASK_TYPE_MAP[key] = tt
    for alias in type_info.get("aliases", []):
        TASK_TYPE_MAP[alias.lower().replace(" ", "").replace("-", "").replace("_", "")] = tt


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class Item:
    id: int
    name: str
    type: str
    depends_on: list = field(default_factory=list)
    purpose: str = ""


@dataclass
class HandoffData:
    task_flow: str
    items: list[Item]
    project: str = ""


# ---------------------------------------------------------------------------
# YAML extraction (regex-based, same as deploy-script-gen.py)
# ---------------------------------------------------------------------------

def _extract_yaml_blocks(markdown: str) -> list[str]:
    return re.findall(r"```yaml\s*\n(.*?)```", markdown, re.DOTALL)


def _extract_task_flow(markdown: str) -> str:
    fm = re.match(r"^---\s*\n(.*?)\n---", markdown, re.DOTALL)
    if fm:
        m = re.search(r"^task_flow:\s*(.+)$", fm.group(1), re.MULTILINE)
        if m:
            return m.group(1).strip()
    m = re.search(r"\*\*Task [Ff]low:\*\*\s*(.+)", markdown)
    if m:
        return re.split(r"\s*[\(\[]", m.group(1).strip())[0].strip()
    return "unknown"


def _parse_yaml_value(raw: str):
    raw = raw.strip()
    if raw in ("", "~", "null"):
        return None
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [_parse_yaml_value(v.strip()) for v in inner.split(",")]
    if raw.lower() in ("true", "yes"):
        return True
    if raw.lower() in ("false", "no"):
        return False
    try:
        return int(raw)
    except ValueError:
        pass
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]
    return raw


def _parse_items_block(yaml_text: str) -> list[Item]:
    """Parse the items YAML block into Item objects."""
    items: list[Item] = []
    current: dict = {}

    for line in yaml_text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # New item starts with "- id:" or "  - id:"
        if re.match(r"-\s+id:", stripped):
            if current:
                items.append(Item(
                    id=current.get("id", 0),
                    name=str(current.get("name", "")),
                    type=str(current.get("type", "")),
                    depends_on=current.get("depends_on", []),
                    purpose=str(current.get("purpose", "")),
                ))
            current = {}
            key, val = stripped.lstrip("- ").split(":", 1)
            current[key.strip()] = _parse_yaml_value(val)
        elif ":" in stripped and current is not None:
            key, val = stripped.split(":", 1)
            current[key.strip()] = _parse_yaml_value(val)

    if current:
        items.append(Item(
            id=current.get("id", 0),
            name=str(current.get("name", "")),
            type=str(current.get("type", "")),
            depends_on=current.get("depends_on", []),
            purpose=str(current.get("purpose", "")),
        ))

    return items


def parse_handoff(path: str) -> HandoffData:
    """Parse architecture handoff markdown into structured data."""
    content = Path(path).read_text(encoding="utf-8")
    task_flow = _extract_task_flow(content)
    yaml_blocks = _extract_yaml_blocks(content)

    items: list[Item] = []
    for block in yaml_blocks:
        if "items:" in block and ("name:" in block and "type:" in block):
            # Extract just the items section
            in_items = False
            items_text = []
            for line in block.split("\n"):
                if line.strip().startswith("items:"):
                    in_items = True
                    continue
                if in_items:
                    if re.match(r"\S", line) and not line.strip().startswith("-"):
                        break
                    items_text.append(line)
            if items_text:
                items = _parse_items_block("\n".join(items_text))
                if items:
                    break

    return HandoffData(task_flow=task_flow, items=items)


# ---------------------------------------------------------------------------
# Task flow JSON generation
# ---------------------------------------------------------------------------

def _resolve_task_type(item_type: str) -> str:
    """Map a Fabric item type to a task flow task type."""
    key = item_type.lower().replace(" ", "").replace("-", "").replace("_", "")
    return TASK_TYPE_MAP.get(key, "general")


def _generate_task_id() -> str:
    """Generate a task ID in the Fabric format: task-{uuid4}."""
    return f"task-{uuid.uuid4()}"


def generate_taskflow_json(data: HandoffData, project_name: str = "") -> dict:
    """Generate a Fabric Task Flow JSON from parsed handoff data."""
    # Build task nodes
    tasks = []
    # Map item id → task UUID for edge generation
    item_id_to_task_id: dict[int, str] = {}

    for item in data.items:
        task_id = _generate_task_id()
        item_id_to_task_id[item.id] = task_id

        task_type = _resolve_task_type(item.type)
        description = item.purpose if item.purpose else f"{item.type} for {project_name or data.task_flow}"

        tasks.append({
            "type": task_type,
            "id": task_id,
            "name": item.name,
            "description": description,
        })

    # Build edges from depends_on relationships
    edges = []
    for item in data.items:
        target_task_id = item_id_to_task_id.get(item.id)
        if not target_task_id:
            continue
        deps = item.depends_on or []
        for dep_id in deps:
            if isinstance(dep_id, str):
                try:
                    dep_id = int(dep_id)
                except ValueError:
                    continue
            source_task_id = item_id_to_task_id.get(dep_id)
            if source_task_id:
                edges.append({
                    "source": source_task_id,
                    "target": target_task_id,
                })

    # Build the task flow document
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate Fabric Task Flow JSON from architecture handoff")
    parser.add_argument("--handoff", required=True, help="Path to architecture-handoff.md")
    parser.add_argument("--project", default="", help="Project display name")
    parser.add_argument("--output", default="", help="Output JSON path (default: alongside handoff)")
    args = parser.parse_args()

    data = parse_handoff(args.handoff)
    if not data.items:
        print("❌ No items found in handoff", file=sys.stderr)
        sys.exit(1)

    project_name = args.project or data.task_flow.replace("-", " ").title()
    taskflow = generate_taskflow_json(data, project_name)

    if args.output:
        out_path = Path(args.output)
    else:
        handoff_dir = Path(args.handoff).parent.parent / "deployments"
        slug = project_name.lower().replace(" ", "-")
        out_path = handoff_dir / f"taskflow-{slug}.json"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(taskflow, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ {out_path}")


if __name__ == "__main__":
    main()
