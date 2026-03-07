"""
Fabric Task Flows — Dynamic Task Flow Generator

Builds a task-flow JSON file matching the Fabric task flow schema:
  { name, description, tasks: [{type, id, name, description}], edges: [{source, target}] }

Called by the engineer agent at deploy time (Phase 2c) when the architecture
is finalized and we know the exact items, their types, and their dependencies.

Usage:
  python scripts/build_task_flow.py --project <project-slug>

  Reads:  projects/<slug>/prd/architecture-handoff.md  (YAML frontmatter)
  Writes: projects/<slug>/deployments/task-flow.json
"""

import argparse
import json
import os
import re
import sys
import uuid

# ---------------------------------------------------------------------------
# Fabric item type → task flow task type mapping
#
# These are the 10 canonical task types from the Fabric task flow schema.
# Every Fabric item maps to exactly one task type.
# ---------------------------------------------------------------------------
ITEM_TYPE_TO_TASK_TYPE = {
    # get data — ingestion items
    "Eventstream": "get data",
    "DataPipeline": "get data",
    "CopyJob": "get data",

    # store data — storage items
    "Lakehouse": "store data",
    "Warehouse": "store data",
    "Eventhouse": "store data",
    "KQLDatabase": "store data",
    "SQLDatabase": "store data",

    # prepare data — processing / transformation items
    "Notebook": "prepare data",
    "KQLQueryset": "prepare data",
    "SparkJobDefinition": "prepare data",

    # develop — compute environment items
    "Environment": "develop",

    # analyze and train data — ML items
    "MLExperiment": "analyze and train data",
    "MLModel": "analyze and train data",

    # visualize — presentation items
    "SemanticModel": "visualize",
    "Report": "visualize",
    "KQLDashboard": "visualize",

    # track data — monitoring / alerting items
    "Activator": "track data",

    # mirror data — mirroring items
    "MirroredDatabase": "mirror data",

    # distribute data — sharing / API items
    "GraphQLAPI": "distribute data",

    # govern data — governance items
    "Ontology": "govern data",
    "VariableLibrary": "govern data",
}


def generate_task_id():
    """Generate a unique task ID in the Fabric task flow format."""
    return f"task-{uuid.uuid4()}"


def parse_items_from_handoff(handoff_path):
    """
    Parse the architecture handoff to extract items and their dependencies.

    Supports two source files:
    1. architecture-handoff.md — has items with id/name/type/depends_on in ```yaml blocks
    2. deployment-handoff.md — has items with name/type/wave in ```yaml blocks

    Returns a list of dicts: [{name, type, wave, depends_on, description}]
    and project metadata: {project, task_flow}
    """
    with open(handoff_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract YAML frontmatter if present (--- delimited)
    fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    frontmatter = fm_match.group(1) if fm_match else ""

    # Extract project name and task flow from frontmatter or body
    project_match = re.search(r"^project:\s*(.+)$", frontmatter or content, re.MULTILINE)
    project = project_match.group(1).strip() if project_match else "unknown"

    tf_match = re.search(r"^task_flow:\s*(.+)$", frontmatter or content, re.MULTILINE)
    task_flow = tf_match.group(1).strip() if tf_match else "unknown"

    # Extract all ```yaml blocks from the document
    yaml_blocks = re.findall(r"```yaml\s*\n(.*?)```", content, re.DOTALL)
    all_yaml = "\n".join(yaml_blocks)

    # Also include frontmatter content
    if frontmatter:
        all_yaml = frontmatter + "\n" + all_yaml

    items = _parse_yaml_items(all_yaml)

    # Filter out non-item entries (e.g., waves parsed as items)
    items = [i for i in items if "type" in i]

    return items, {"project": project, "task_flow": task_flow}


def _parse_yaml_items(yaml_text):
    """
    Parse items from YAML content. Handles both architecture-handoff format
    (id/name/type/depends_on/purpose) and deployment-handoff format
    (name/type/wave/status/command).
    """
    items = []
    current = {}
    in_items = False

    for line in yaml_text.split("\n"):
        stripped = line.strip()

        if stripped == "items:":
            in_items = True
            continue

        if in_items:
            # New item
            if stripped.startswith("- "):
                if current and "name" in current:
                    items.append(current)
                current = {}
                # Handle inline field: "- name: foo" or "- id: 1"
                rest = stripped[2:]
                if ":" in rest:
                    key, val = rest.split(":", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key == "id":
                        current["item_id"] = int(val) if val.isdigit() else val
                    elif key == "name":
                        current["name"] = val
                    elif key == "type":
                        current["type"] = val
                continue

            # Continuation fields
            if ":" in stripped and not stripped.startswith("#"):
                key, val = stripped.split(":", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")

                if key == "name":
                    current["name"] = val
                elif key == "type":
                    current["type"] = val
                elif key == "id" and "item_id" not in current:
                    current["item_id"] = int(val) if val.isdigit() else val
                elif key == "wave":
                    current["wave"] = int(val) if val.isdigit() else 1
                elif key == "depends_on":
                    current["depends_on"] = _parse_depends_on(val)
                elif key == "purpose":
                    current["description"] = val
                elif key == "description":
                    current["description"] = val
            # End of items section
            elif stripped.startswith("waves:") or stripped.startswith("manual_steps:") \
                    or stripped.startswith("acceptance_criteria:"):
                if current and "name" in current:
                    items.append(current)
                    current = {}
                in_items = False

    # Don't forget the last item
    if current and "name" in current:
        items.append(current)

    return items


def _parse_depends_on(val):
    """Parse depends_on value: [1, 4] or [] or 1."""
    val = val.strip().strip("[]")
    if not val:
        return []
    parts = [p.strip() for p in val.split(",")]
    result = []
    for p in parts:
        if p.isdigit():
            result.append(int(p))
        elif p:
            result.append(p)
    return result


def normalize_item_type(raw_type):
    """
    Normalize item type strings from handoff to canonical Fabric types.

    Handles variations like 'Pipeline', 'Data Pipeline', 'Lakehouse',
    'KQL Queryset', 'Semantic Model', 'Real-Time Dashboard', etc.
    """
    normalized = {
        "pipeline": "DataPipeline",
        "data pipeline": "DataPipeline",
        "datapipeline": "DataPipeline",
        "eventstream": "Eventstream",
        "copy job": "CopyJob",
        "copyjob": "CopyJob",
        "lakehouse": "Lakehouse",
        "warehouse": "Warehouse",
        "eventhouse": "Eventhouse",
        "kql database": "KQLDatabase",
        "kqldatabase": "KQLDatabase",
        "sql database": "SQLDatabase",
        "sqldatabase": "SQLDatabase",
        "notebook": "Notebook",
        "kql queryset": "KQLQueryset",
        "kqlqueryset": "KQLQueryset",
        "spark job definition": "SparkJobDefinition",
        "sparkjobdefinition": "SparkJobDefinition",
        "environment": "Environment",
        "ml experiment": "MLExperiment",
        "mlexperiment": "MLExperiment",
        "experiment": "MLExperiment",
        "ml model": "MLModel",
        "mlmodel": "MLModel",
        "semantic model": "SemanticModel",
        "semanticmodel": "SemanticModel",
        "report": "Report",
        "real-time dashboard": "KQLDashboard",
        "rt dashboard": "KQLDashboard",
        "kql dashboard": "KQLDashboard",
        "kqldashboard": "KQLDashboard",
        "activator": "Activator",
        "reflex": "Activator",
        "mirrored database": "MirroredDatabase",
        "mirroreddatabase": "MirroredDatabase",
        "graphql api": "GraphQLAPI",
        "graphqlapi": "GraphQLAPI",
        "ontology": "Ontology",
        "variable library": "VariableLibrary",
        "variablelibrary": "VariableLibrary",
    }
    return normalized.get(raw_type.lower().strip(), raw_type)


def build_task_flow(items, metadata):
    """
    Build a task flow JSON structure from a list of architecture items.

    Edges are derived from:
    1. Explicit `depends_on` references (preferred — from architecture handoff)
    2. Wave ordering fallback (from deployment handoff)
    3. Intra-wave known patterns (e.g., Eventhouse → KQLDatabase)
    """
    # Build task nodes with unique IDs
    tasks = []
    id_map = {}       # item_name → task_id
    num_id_map = {}   # numeric item_id → item_name (for depends_on resolution)

    for item in items:
        canonical_type = normalize_item_type(item["type"])
        task_type = ITEM_TYPE_TO_TASK_TYPE.get(canonical_type, "prepare data")
        task_id = generate_task_id()
        id_map[item["name"]] = task_id

        if "item_id" in item:
            num_id_map[item["item_id"]] = item["name"]

        tasks.append({
            "type": task_type,
            "id": task_id,
            "name": item["name"],
            "description": item.get("description", f"{item['type']}: {item['name']}"),
        })

    # Build edges
    edges = []
    has_depends_on = any("depends_on" in item for item in items)

    if has_depends_on:
        # Use explicit depends_on references
        for item in items:
            deps = item.get("depends_on", [])
            for dep in deps:
                # Resolve numeric ID to item name
                dep_name = num_id_map.get(dep, dep) if isinstance(dep, int) else dep
                if dep_name in id_map and item["name"] in id_map:
                    edges.append({
                        "source": id_map[dep_name],
                        "target": id_map[item["name"]],
                    })
    else:
        # Fallback: derive edges from wave ordering
        waves = {}
        for item in items:
            w = item.get("wave", 1)
            waves.setdefault(w, [])
            waves[w].append(item)

        sorted_waves = sorted(waves.keys())
        for i, wave_num in enumerate(sorted_waves):
            if i + 1 >= len(sorted_waves):
                break
            current_wave = waves[wave_num]
            next_wave = waves[sorted_waves[i + 1]]
            for src in current_wave:
                src_type = normalize_item_type(src["type"])
                src_task_type = ITEM_TYPE_TO_TASK_TYPE.get(src_type, "prepare data")
                for tgt in next_wave:
                    tgt_type = normalize_item_type(tgt["type"])
                    tgt_task_type = ITEM_TYPE_TO_TASK_TYPE.get(tgt_type, "prepare data")
                    if _should_connect(src_task_type, tgt_task_type):
                        edges.append({
                            "source": id_map[src["name"]],
                            "target": id_map[tgt["name"]],
                        })

    # Add intra-wave edges for known patterns
    waves = {}
    for item in items:
        w = item.get("wave", 1)
        waves.setdefault(w, [])
        waves[w].append(item)

    for wave_items in waves.values():
        for i, a in enumerate(wave_items):
            for b in wave_items[i + 1:]:
                a_type = normalize_item_type(a["type"])
                b_type = normalize_item_type(b["type"])
                if (a_type, b_type) in _INTRA_WAVE_PAIRS:
                    edges.append({
                        "source": id_map[a["name"]],
                        "target": id_map[b["name"]],
                    })
                elif (b_type, a_type) in _INTRA_WAVE_PAIRS:
                    edges.append({
                        "source": id_map[b["name"]],
                        "target": id_map[a["name"]],
                    })

    # Deduplicate edges
    seen = set()
    unique_edges = []
    for e in edges:
        key = (e["source"], e["target"])
        if key not in seen:
            seen.add(key)
            unique_edges.append(e)

    return {
        "name": metadata["project"],
        "description": (
            f"Task flow for {metadata['project']} "
            f"({metadata['task_flow']} architecture)"
        ),
        "tasks": tasks,
        "edges": unique_edges,
    }


# Cross-wave connection rules: src_task_type → allowed tgt_task_types
_FLOW_RULES = {
    "get data": {"store data", "track data"},
    "store data": {"prepare data", "analyze and train data", "visualize", "track data"},
    "develop": {"prepare data", "analyze and train data"},
    "prepare data": {"store data", "visualize", "track data"},
    "analyze and train data": {"visualize", "prepare data", "store data"},
    "visualize": {"track data", "distribute data"},
    "mirror data": {"store data"},
    "track data": {"distribute data"},
    "govern data": set(),
    "distribute data": set(),
}

# Item type pairs that should be connected within the same wave
_INTRA_WAVE_PAIRS = {
    ("Eventhouse", "KQLDatabase"),
    ("SemanticModel", "Report"),
}


def _should_connect(src_type, tgt_type):
    """Determine if two task types should have an edge between waves."""
    allowed = _FLOW_RULES.get(src_type, set())
    return tgt_type in allowed


def main():
    parser = argparse.ArgumentParser(
        description="Generate a Fabric task flow JSON from architecture handoff"
    )
    parser.add_argument(
        "--project", required=True,
        help="Project slug (e.g., agent-assist-telco)"
    )
    parser.add_argument(
        "--repo-root", default=None,
        help="Repository root (default: auto-detect from script location)"
    )
    args = parser.parse_args()

    # Find repo root
    if args.repo_root:
        repo_root = args.repo_root
    else:
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    handoff_path = os.path.join(
        repo_root, "projects", args.project, "prd", "architecture-handoff.md"
    )
    if not os.path.exists(handoff_path):
        print(f"  ❌ Architecture handoff not found: {handoff_path}")
        sys.exit(1)

    output_dir = os.path.join(repo_root, "projects", args.project, "deployments")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{args.project}-task-flow.json")

    # Parse and build
    items, metadata = parse_items_from_handoff(handoff_path)
    if not items:
        print(f"  ❌ No items found in {handoff_path}")
        print("     Ensure the handoff has a table with | Item | Type | Wave | columns")
        print("     or a YAML items list with name/type/wave fields.")
        sys.exit(1)

    task_flow = build_task_flow(items, metadata)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(task_flow, f, indent=2)

    print(f"  ✅ Task flow generated: {output_path}")
    print(f"     {len(task_flow['tasks'])} tasks, {len(task_flow['edges'])} edges")


if __name__ == "__main__":
    main()
