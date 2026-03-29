#!/usr/bin/env python3
"""
Generate deployment shell scripts from architecture handoffs.

Reads an architecture-handoff.md (with items_to_deploy and deployment_waves
YAML blocks) and generates filled .sh and .ps1 deploy scripts from the
templates in _shared/.

Usage:
    python .github/skills/fabric-deploy/scripts/deploy-script-gen.py --handoff projects/my-project/docs/architecture-handoff.md --project "My Project"
    python .github/skills/fabric-deploy/scripts/deploy-script-gen.py --handoff projects/my-project/docs/architecture-handoff.md --project "My Project" --output-dir projects/my-project/deploy/
    python .github/skills/fabric-deploy/scripts/deploy-script-gen.py --handoff projects/my-project/docs/architecture-handoff.md --project "My Project" --shell bash
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

SHARED_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "_shared"
SKILL_DIR = Path(__file__).resolve().parent.parent  # .github/skills/fabric-deploy/

# ─────────────────────────────────────────────────────────────────────────────
# Item type → fab command mapping
# ─────────────────────────────────────────────────────────────────────────────

# Item type mappings — loaded from _shared/registry/item-type-registry.json
# Do NOT maintain these dicts manually. See CONTRIBUTING.md.
_SHARED_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "_shared" / "lib"

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "_shared" / "lib"))
import bootstrap  # noqa: F401
from registry_loader import load_registry
from banner import BANNER_ART
from yaml_utils import extract_yaml_blocks, extract_task_flow, parse_yaml_value, split_list, parse_inline_mapping
from text_utils import slugify, escape_for_python_string

# REST API creation support map loaded from registry
REGISTRY_TYPES: dict = load_registry()

# Static item content templates — loaded from _shared/templates/ (single source of truth)
# Each subdirectory contains the exact empty-state definition files that fabric-cicd
# will base64-encode and POST to the Fabric Items API.
_TEMPLATES_DIR = SHARED_DIR / "templates"


def _load_template_files(cicd_type: str) -> dict[str, str] | None:
    """Load definition files from _shared/templates/{cicd_type}/.

    Returns {relative_path: content} or None if no template directory exists.
    Files are read as-is — no JSON parsing or transformation.
    """
    tpl_dir = _TEMPLATES_DIR / cicd_type
    if not tpl_dir.is_dir():
        return None
    result: dict[str, str] = {}
    for fpath in sorted(tpl_dir.rglob("*")):
        if fpath.is_file() and fpath.name != "README.md":
            rel = fpath.relative_to(tpl_dir).as_posix()
            result[rel] = fpath.read_text(encoding="utf-8")
    return result or None


# ─────────────────────────────────────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Item:
    id: int
    name: str
    type: str
    skillset: str = ""
    depends_on: list = field(default_factory=list)
    purpose: str = ""


@dataclass
class Wave:
    id: int
    items: list = field(default_factory=list)
    blocked_by: list = field(default_factory=list)
    note: str = ""


@dataclass
class HandoffData:
    task_flow: str
    items: list[Item]
    waves: list[Wave]
    summary: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# YAML extraction — delegated to _shared/yaml_utils.py
# Aliases kept for internal call-site compatibility.
# ─────────────────────────────────────────────────────────────────────────────

_extract_yaml_blocks = extract_yaml_blocks


def _extract_task_flow(markdown: str) -> str:
    """Extract task_flow from YAML frontmatter or body content."""
    return extract_task_flow(markdown) or "unknown"


_parse_yaml_value = parse_yaml_value
_split_list = split_list
_parse_inline_mapping = parse_inline_mapping


def _parse_items_block(yaml_text: str) -> list[Item]:
    """Parse items from a YAML block (handles both inline and multi-line)."""
    items: list[Item] = []

    # Try inline format first: - { name: ..., type: ... }
    for line in yaml_text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("- {"):
            brace_start = stripped.index("{")
            mapping = _parse_inline_mapping(stripped[brace_start:])
            items.append(Item(
                id=int(mapping.get("id", 0)),
                name=str(mapping.get("name", mapping.get("item_name", ""))),
                type=str(mapping.get("type", mapping.get("item_type", ""))),
                skillset=str(mapping.get("skillset", "")),
                depends_on=[],
                purpose=str(mapping.get("purpose", "")),
            ))

    if items:
        return items

    # Multi-line format: - item_name: ... \n    item_type: ...
    current: dict[str, str] = {}
    for line in yaml_text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        if stripped.startswith("- "):
            if current:
                items.append(_dict_to_item(current))
            current = {}
            rest = stripped[2:].strip()
            m = re.match(r"([\w_-]+)\s*:\s*(.*)", rest)
            if m:
                current[m.group(1)] = m.group(2).strip().strip('"').strip("'")
        elif ":" in stripped and current is not None:
            m = re.match(r"([\w_-]+)\s*:\s*(.*)", stripped)
            if m:
                val = m.group(2).strip().strip('"').strip("'")
                if val.startswith("[") and val.endswith("]"):
                    current[m.group(1)] = val
                else:
                    current[m.group(1)] = val
    if current:
        items.append(_dict_to_item(current))

    return items


def _dict_to_item(d: dict[str, str]) -> Item:
    """Convert a parsed dict to an Item dataclass.

    Handles depends_on as integer IDs, string names, or a mix of both.
    String names are kept as-is and resolved later by _resolve_string_deps().
    """
    name = d.get("name", d.get("item_name", ""))
    item_type = d.get("type", d.get("item_type", ""))
    deps_raw = d.get("dependencies", d.get("depends_on", "[]"))
    if isinstance(deps_raw, list):
        deps = []
        for x in deps_raw:
            try:
                deps.append(int(x))
            except (ValueError, TypeError):
                deps.append(str(x))
    elif isinstance(deps_raw, str) and deps_raw.startswith("["):
        inner = deps_raw[1:-1].strip()
        deps = []
        if inner:
            for x in inner.split(","):
                val = x.strip().strip('"').strip("'")
                if not val:
                    continue
                try:
                    deps.append(int(val))
                except ValueError:
                    deps.append(val)
    else:
        deps = []
    return Item(
        id=int(d.get("id", 0)),
        name=name,
        type=item_type,
        skillset=d.get("skillset", ""),
        depends_on=deps,
        purpose=d.get("purpose", ""),
    )


def _resolve_string_deps(items: list[Item]) -> None:
    """Resolve string dependency names to integer IDs in-place.

    After all items are parsed, any depends_on entries that are strings
    (e.g. "Lakehouse Bronze") are matched against item names/types and
    replaced with the corresponding item ID.
    """
    def _norm(s: str) -> str:
        return s.lower().replace("-", "").replace("_", "").replace(" ", "")

    name_to_id: dict[str, int] = {}
    for item in items:
        name_to_id[item.name.lower()] = item.id
        name_to_id[item.type.lower()] = item.id
        # Support "Type Name" patterns like "Lakehouse Bronze"
        composite = f"{item.type} {item.name}".lower()
        name_to_id[composite] = item.id
        # Normalized variants (collapse dashes, underscores, spaces)
        name_to_id[_norm(item.name)] = item.id
        name_to_id[_norm(item.type)] = item.id
        name_to_id[_norm(f"{item.type} {item.name}")] = item.id
    for item in items:
        resolved = []
        for dep in item.depends_on:
            if isinstance(dep, int):
                resolved.append(dep)
            elif isinstance(dep, str):
                key = dep.lower().strip()
                if key in name_to_id:
                    resolved.append(name_to_id[key])
                elif _norm(dep) in name_to_id:
                    resolved.append(name_to_id[_norm(dep)])
                else:
                    resolved.append(dep)
        item.depends_on = resolved


def _parse_waves_block(yaml_text: str) -> list[Wave]:
    """Parse waves from a YAML block (handles both inline and multi-line)."""
    waves: list[Wave] = []

    # Try inline format first
    for line in yaml_text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("- {"):
            brace_start = stripped.index("{")
            mapping = _parse_inline_mapping(stripped[brace_start:])
            waves.append(Wave(
                id=int(mapping.get("id", mapping.get("wave_number", 0))),
                items=[str(x) for x in (mapping.get("items") or [])],
                blocked_by=[str(x) for x in (mapping.get("blocked_by", mapping.get("dependencies")) or [])],
                note=str(mapping.get("note", "")),
            ))

    if waves:
        return waves

    # Multi-line format
    current: dict[str, str] = {}
    for line in yaml_text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        if stripped.startswith("- "):
            if current:
                waves.append(_dict_to_wave(current))
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
        waves.append(_dict_to_wave(current))

    return waves


def _dict_to_wave(d: dict[str, str]) -> Wave:
    """Convert a parsed dict to a Wave dataclass."""
    wave_id = int(d.get("id", d.get("wave_number", 0)))
    items_raw = d.get("items", "[]")
    if isinstance(items_raw, str) and items_raw.startswith("["):
        inner = items_raw[1:-1].strip()
        items = [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()] if inner else []
    else:
        items = []
    deps_raw = d.get("blocked_by", d.get("dependencies", "[]"))
    if isinstance(deps_raw, str) and deps_raw.startswith("["):
        inner = deps_raw[1:-1].strip()
        deps = [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()] if inner else []
    else:
        deps = []
    return Wave(id=wave_id, items=items, blocked_by=deps, note=d.get("name", d.get("note", "")))


def parse_handoff(path: str) -> HandoffData:
    """Parse an architecture-handoff.md or architecture-summary.json and extract structured data."""
    p = Path(path)
    content = p.read_text(encoding="utf-8")

    # JSON format (architecture-summary.json)
    if p.suffix == ".json":
        return _parse_json_handoff(content, path)

    # Markdown format (architecture-handoff.md)
    task_flow = _extract_task_flow(content)

    # Extract problem summary from handoff
    summary = ""
    m = re.search(r">\s*Summary:\s*(.+)", content)
    if m:
        summary = m.group(1).strip()

    yaml_blocks = _extract_yaml_blocks(content)

    items: list[Item] = []
    waves: list[Wave] = []

    for block in yaml_blocks:
        stripped = block.strip()
        if stripped.startswith("items:") or stripped.startswith("items_to_deploy:"):
            items = _parse_items_block(stripped)
        elif stripped.startswith("waves:") or stripped.startswith("deployment_waves:"):
            waves = _parse_waves_block(stripped)

    if items:
        _resolve_string_deps(items)

    if not items:
        print(f"⚠ No items found in {path}", file=sys.stderr)
    if not waves:
        print(f"⚠ No waves found in {path}", file=sys.stderr)

    return HandoffData(task_flow=task_flow, items=items, waves=waves, summary=summary)


def _parse_json_handoff(content: str, path: str) -> HandoffData:
    """Parse architecture-summary.json format into HandoffData."""
    data = json.loads(content)
    task_flow = data.get("task_flow", "unknown")

    items: list[Item] = []
    for item_data in data.get("items", []):
        deps_raw = item_data.get("depends_on", [])
        deps = []
        for d in deps_raw:
            try:
                deps.append(int(d))
            except (ValueError, TypeError):
                deps.append(str(d))
        items.append(Item(
            id=int(item_data.get("id", 0)),
            name=str(item_data.get("name", "")),
            type=str(item_data.get("type", "")),
            skillset=str(item_data.get("skillset", "")),
            depends_on=deps,
            purpose=str(item_data.get("purpose", "")),
        ))

    waves: list[Wave] = []
    for wave_data in data.get("waves", []):
        waves.append(Wave(
            id=int(wave_data.get("id", 0)),
            items=wave_data.get("items", []),
            blocked_by=wave_data.get("blocked_by", []),
        ))

    if items:
        _resolve_string_deps(items)

    if not items:
        print(f"⚠ No items found in {path}", file=sys.stderr)
    if not waves:
        print(f"⚠ No waves found in {path}", file=sys.stderr)

    return HandoffData(task_flow=task_flow, items=items, waves=waves)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _slugify(name: str) -> str:
    """Convert project name to kebab-case."""
    return slugify(name)


def _type_key(item_type: str) -> str:
    """Normalize item type for registry lookup."""
    return item_type.lower().replace("_", "").replace(" ", "").replace("-", "")


def _cli_safe_name(name: str) -> str:
    """Convert item name to CLI-safe format (underscores instead of hyphens).

    Fabric CLI rejects hyphens in item names for multiple item types
    (Lakehouse, Eventstream, MLExperiment, MLModel, and potentially others).
    Rather than maintain an incomplete allowlist, we universally convert
    hyphens to underscores for all item types.
    """
    return name.replace("-", "_")


def _resolve_fab_type(item_type: str) -> str:
    """Resolve item type to its Fabric type name (e.g., 'Pipeline' → 'DataPipeline')."""
    from registry_loader import build_fab_type_map
    fab_map = build_fab_type_map()
    return fab_map.get(item_type, fab_map.get(item_type.title(), item_type))


# ─────────────────────────────────────────────────────────────────────────────
# Code generation: wave deployment commands
# ─────────────────────────────────────────────────────────────────────────────

# Item types that trigger post-wave logic
_ENV_TYPES = {"environment"}
_SEMANTIC_MODEL_TYPES = {"semanticmodel", "semantic model"}
_NOTEBOOK_TYPES = {"notebook"}

# Phase → folder name mapping (used for workspace folder organization)
PHASE_FOLDER_NAMES: dict[str, str] = {
    "Foundation": "Storage",
    "Environment": "Configuration",
    "Ingestion": "Ingestion",
    "Transformation": "Processing",
    "Visualization": "Analytics",
    "ML": "Machine Learning",
    "IQ": "Intelligence",
    "Monitoring": "Monitoring",
}


def _get_item_phase(item_type: str) -> str:
    """Get the deployment phase for an item type from the registry."""
    key = _type_key(item_type)
    for type_name, type_info in REGISTRY_TYPES.items():
        reg_key = _type_key(type_name)
        if reg_key == key:
            return type_info.get("phase", "Other")
        for alias in type_info.get("aliases", []):
            if _type_key(alias) == key:
                return type_info.get("phase", "Other")
    return "Other"


def _get_folder_for_item(item_type: str) -> str:
    """Get the workspace folder name for an item type. Returns empty string for unknown types."""
    phase = _get_item_phase(item_type)
    if phase == "Other":
        return ""
    return PHASE_FOLDER_NAMES.get(phase, "")


def _collect_folders(data: "HandoffData") -> list[str]:
    """Collect unique folder names needed for all items in the handoff."""
    folders: list[str] = []
    seen: set[str] = set()
    for item in data.items:
        folder = _get_folder_for_item(item.type)
        if folder and folder not in seen:
            seen.add(folder)
            folders.append(folder)
    return folders


# ─────────────────────────────────────────────────────────────────────────────
# Code generation: Python deploy script
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# fabric-cicd directory structure generation
# ─────────────────────────────────────────────────────────────────────────────

import uuid as _uuid

from registry_loader import build_cicd_type_set, build_type_remap
_FABRIC_CICD_TYPES: set[str] = build_cicd_type_set()
_TYPE_REMAP: dict[str, str] = build_type_remap()


def _cicd_type(item_type: str) -> str:
    """Resolve item type to fabric-cicd compatible name. Returns empty string if unsupported."""
    fab_type= _resolve_fab_type(item_type)
    fab_type = _TYPE_REMAP.get(fab_type, fab_type)
    return fab_type if fab_type in _FABRIC_CICD_TYPES else ""


def _gen_platform_file(item_type: str, display_name: str, description: str = "") -> str:
    """Generate a .platform file matching fabric-cicd's expected format."""
    cicd_type = _cicd_type(item_type) or _resolve_fab_type(item_type)
    platform = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {
            "type": cicd_type,
            "displayName": display_name,
        },
        "config": {
            "version": "2.0",
            "logicalId": str(_uuid.uuid4()),
        }
    }
    if description:
        platform["metadata"]["description"] = description
    return json.dumps(platform, indent=2, ensure_ascii=False)


def _gen_config_yml(data: HandoffData, project: str, ws_desc: str) -> str:
    """Generate a config.yml for fabric-cicd deploy_with_config."""
    slug = _slugify(project)
    # Collect unique item types, filtering to fabric-cicd supported only
    # Exclude REST-only types — they're created via REST API post-deploy
    raw_types = set()
    for item in data.items:
        if not item.name:
            continue
        ct = _cicd_type(item.type)
        if ct:
            raw_types.add(ct)
    # Hard rule: always include VariableLibrary for CI/CD stage flexibility
    raw_types.add("VariableLibrary")
    item_types = sorted(raw_types)

    # Collect unique folder names
    folders = _collect_folders(data)
    # Hard rule: always include Configuration folder for Variable Library
    if "Configuration" not in folders:
        folders.insert(0, "Configuration")

    lines = [
        f"# fabric-cicd configuration for {project}",
        f"# Task flow: {data.task_flow}",
        "# Generated by deploy-script-gen.py",
        "",
        "core:",
        "  # Set workspace name or ID per environment",
        f"  workspace: {slug}-dev",
        "  repository_directory: ./workspace",
        "  item_types_in_scope:",
    ]
    for t in item_types:
        lines.append(f"    - {t}")

    lines += [
        "",
        "publish:",
        "  # Folder paths to include in deployment",
    ]
    if folders:
        lines.append("  folder_path_to_include:")
        for f in folders:
            lines.append(f"    - /{f}")

    lines += [
        "",
        "feature_flags:",
        "  - enable_workspace_folder_publish",
    ]

    # fabric-cicd v0.3.1+ uses 'features' key instead of 'feature_flags'
    feature_list = ["enable_workspace_folder_publish"]
    if folders:
        feature_list += ["enable_experimental_features", "enable_include_folder"]
    lines += [
        "",
        "features:",
    ]
    for feat in feature_list:
        lines.append(f"  - {feat}")

    return "\n".join(lines) + "\n"


def _build_deploy_banner_func(project: str, task_flow: str) -> str:
    """Generate a self-contained print_banner() function for deploy scripts.

    Embeds the BANNER_ART directly so generated scripts have zero
    dependency on banner.py at runtime.
    """
    art_lines = BANNER_ART.split("\n")
    divider_len = max(len(line) for line in art_lines)

    parts = ['def print_banner():']
    parts.append(f'    divider = "-" * {divider_len}')
    parts.append('    print()')
    for art_line in art_lines:
        escaped = art_line.replace("\\", "\\\\").replace('"', '\\"')
        parts.append(f'    print("{escaped}")')
    parts.append('    print()')
    parts.append('    print(divider)')
    parts.append('    print("  T A S K   F L O W S")')
    if project:
        parts.append(f'    print("  Project:   {escape_for_python_string(project)}")')
    if task_flow:
        parts.append(f'    print("  Task Flow: {escape_for_python_string(task_flow)}")')
    parts.append('    print(divider)')
    parts.append('    print()')

    return "\n".join(parts)


def _gen_deploy_script(project: str, data: HandoffData) -> str:
    """Generate a thin deploy.py that uses fabric-cicd."""
    slug = _slugify(project)
    safe_project = escape_for_python_string(project)
    safe_task_flow = escape_for_python_string(data.task_flow)
    item_count = len(data.items)
    wave_count = len(data.waves)
    ws_desc_line = f"{safe_project} — {safe_task_flow} architecture"
    if data.summary:
        ws_desc_line += f". {data.summary}"

    # Build a self-contained banner function for the deploy script
    banner_func = _build_deploy_banner_func(project, data.task_flow)

    return f"""#!/usr/bin/env python3
\"""
Fabric Task Flows - Deploy Script
Project:   {safe_project}
Task Flow: {safe_task_flow}

Uses fabric-cicd (pip install fabric-cicd) for deployment.
\"""

import argparse
import os
import sys

BASE_URL = "https://api.fabric.microsoft.com/v1"

{banner_func}


def get_credential():
    try:
        from azure.identity import AzureCliCredential, DeviceCodeCredential, InteractiveBrowserCredential
    except ImportError:
        print("  -- azure-identity not installed. Run: pip install azure-identity")
        sys.exit(1)
    scope = "https://api.fabric.microsoft.com/.default"

    # 1. Azure CLI — works if user has run 'az login' (best for terminal/CI)
    try:
        cred = AzureCliCredential()
        cred.get_token(scope)
        print("  -- Authenticated via Azure CLI")
        return cred
    except Exception:
        pass

    # 2. Device code — prints a code to the terminal (works in headless/CLI environments)
    try:
        print("  -- Azure CLI not available. Using device code flow...")
        cred = DeviceCodeCredential()
        cred.get_token(scope)
        return cred
    except Exception:
        pass

    # 3. Browser — last resort (requires visible browser window)
    print("  -- Falling back to browser sign-in...")
    return InteractiveBrowserCredential()


def get_auth_headers(credential=None):
    import requests
    if credential is None:
        credential = get_credential()
    token = credential.get_token("https://api.fabric.microsoft.com/.default").token
    return {{"Authorization": f"Bearer {{token}}", "Content-Type": "application/json"}}


def ensure_workspace(name, headers, description=""):
    import requests
    resp = requests.get(f"{{BASE_URL}}/workspaces", headers=headers)
    if resp.ok:
        for ws in resp.json().get("value", []):
            if ws.get("displayName") == name:
                print(f"  -- Found workspace: {{name}} ({{ws['id'][:8]}}...)")
                return ws["id"]
    print(f"  -- Workspace '{{name}}' not found.")
    response = input("  ? Create it now? [Y/n]: ").strip() or "Y"
    if response.upper() != "Y":
        sys.exit(1)
    create_resp = requests.post(f"{{BASE_URL}}/workspaces", headers=headers,
        json={{"displayName": name, "description": description}})
    if create_resp.ok:
        new_id = create_resp.json()["id"]
        print(f"  -- Created workspace: {{name}} ({{new_id[:8]}}...)")
        return new_id
    else:
        print(f"  -- Failed: {{create_resp.json().get('message', create_resp.text)}}")
        sys.exit(1)


def ensure_capacity(ws_id, headers):
    import requests
    ws_resp = requests.get(f"{{BASE_URL}}/workspaces/{{ws_id}}", headers=headers)
    if ws_resp.ok:
        ws_data = ws_resp.json()
        if ws_data.get("capacityId") and ws_data["capacityId"] != "00000000-0000-0000-0000-000000000000":
            print(f"  -- Capacity already assigned")
            return
    print("  -- No capacity assigned. Fetching available capacities...")
    cap_resp = requests.get(f"{{BASE_URL}}/capacities", headers=headers)
    capacities = cap_resp.json().get("value", []) if cap_resp.ok else []
    if not capacities:
        print("  -- No capacities available.")
        sys.exit(1)
    print()
    for i, cap in enumerate(capacities):
        print(f"  {{i+1:3}})  {{cap.get('displayName', 'Unknown')}} ({{cap.get('sku', '')}})")
    print()
    num = 0
    while num < 1 or num > len(capacities):
        try: num = int(input("  ? Select capacity: ").strip())
        except ValueError: num = 0
    cap_id = capacities[num - 1]["id"]
    assign_resp = requests.post(f"{{BASE_URL}}/workspaces/{{ws_id}}/assignToCapacity",
        headers=headers, json={{"capacityId": cap_id}})
    if assign_resp.ok or assign_resp.status_code == 202:
        print(f"  -- Capacity assigned: {{capacities[num-1].get('displayName', '')}}")
    else:
        print("  -- Failed to assign capacity")
        sys.exit(1)


def deploy_to_workspace(config_path, ws_id, environment=None, credential=None):
    import yaml
    from fabric_cicd import deploy_with_config
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    config["core"]["workspace_id"] = ws_id
    config["core"].pop("workspace", None)
    with open(config_path, "w", encoding="utf-8", newline="\\n") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    kwargs = {{"config_file_path": config_path}}
    if environment:
        kwargs["environment"] = environment
    if credential:
        kwargs["token_credential"] = credential

    # Retry deploy up to 3 times — fabric-cicd skips already-published items on re-run
    import time
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            deploy_with_config(**kwargs)
            return
        except Exception as e:
            err_msg = str(e)
            if "timed out" in err_msg.lower() or "timeout" in err_msg.lower() or "connection" in err_msg.lower():
                if attempt < max_retries:
                    wait = attempt * 30
                    print(f"  -- Timeout on attempt {{attempt}}, retrying in {{wait}}s...")
                    time.sleep(wait)
                    continue
            raise


def populate_variable_library(ws_id, headers):
    # Post-deploy: populate Variable Library with ItemReference variables for all deployed items.
    # Uses ItemReference type (workspaceId + itemId in one variable) — no separate _WSID vars needed.
    import requests, base64
    import json as _json
    from datetime import datetime, timezone
    print()
    print("  -- POPULATING VARIABLE LIBRARY --")

    resp = requests.get(f"{{BASE_URL}}/workspaces/{{ws_id}}/items", headers=headers)
    if not resp.ok:
        print(f"  ── Could not list items: {{resp.text}}")
        return

    items = resp.json().get("value", [])

    vl_item = None
    for item in items:
        if item.get("type") == "VariableLibrary":
            vl_item = item
            break

    if not vl_item:
        print("  ── No Variable Library found — skipping")
        return

    vl_id = vl_item["id"]
    print(f"  ── Found Variable Library: {{vl_item.get('displayName', '')}} ({{vl_id[:8]}}...)")

    # Map item types to role-based names
    ROLE_MAP = {{
        "Lakehouse": "Raw_Lakehouse",
        "Warehouse": "Curated_Warehouse",
        "Eventhouse": "Streaming_Eventhouse",
        "Environment": "Spark_Environment",
        "DataPipeline": "Batch_Pipeline",
        "Eventstream": "Feed_Eventstream",
        "Notebook": "NLP_Notebook",
        "KQLQueryset": "KQL_Queryset",
        "SemanticModel": "Semantic_Model",
        "Report": "Leadership_Report",
        "Reflex": "Alerts_Activator",
        "KQLDashboard": "RT_Dashboard",
        "MLExperiment": "ML_Experiment",
    }}

    variables = []
    role_counter = {{}}
    # Only these types support ItemReference consumers (Notebooks, Shortcuts, UDFs)
    ITEM_REF_TYPES = {{"Lakehouse", "Warehouse", "Eventhouse", "Environment", "SemanticModel"}}

    for item in items:
        item_type = item.get("type", "")
        if item_type == "VariableLibrary":
            continue

        role_name = ROLE_MAP.get(item_type, item["displayName"].replace("-", "_").replace(" ", "_"))

        role_counter[role_name] = role_counter.get(role_name, 0) + 1
        if role_counter[role_name] > 1:
            role_name = f"{{role_name}}_{{role_counter[role_name]}}"

        if item_type in ITEM_REF_TYPES:
            # ItemReference — contains workspaceId + itemId (no separate String needed)
            variables.append({{
                "name": role_name,
                "type": "ItemReference",
                "value": {{"workspaceId": ws_id, "itemId": item["id"]}},
                "note": f"{{item_type}} — {{item.get('displayName', '')}}"
            }})
        else:
            # String — for types that don't support ItemReference
            variables.append({{
                "name": role_name,
                "type": "String",
                "value": item["id"],
                "note": f"{{item_type}} — {{item.get('displayName', '')}}"
            }})

    # Operational metadata (String type — not item references)
    variables.append({{"name": "Workspace_ID", "type": "String", "value": ws_id, "note": "Current workspace GUID"}})
    variables.append({{"name": "Workspace_URL", "type": "String", "value": f"https://app.fabric.microsoft.com/groups/{{ws_id}}", "note": "Fabric Portal URL"}})
    variables.append({{"name": "Project_Name", "type": "String", "value": "{safe_project}", "note": "Project name"}})
    variables.append({{"name": "Environment_Name", "type": "String", "value": "dev", "note": "Current deployment stage"}})
    variables.append({{"name": "Deploy_Timestamp", "type": "String", "value": datetime.now(timezone.utc).isoformat(), "note": "Deployment timestamp"}})

    # Build and push definition
    var_json = _json.dumps({{
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/variableLibrary/definition/variables/1.0.0/schema.json",
        "variables": variables
    }})
    settings_json = _json.dumps({{
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/variableLibrary/definition/settings/1.0.0/schema.json",
        "valueSetsOrder": []
    }})

    body = {{
        "definition": {{
            "format": "VariableLibraryV1",
            "parts": [
                {{"path": "variables.json", "payload": base64.b64encode(var_json.encode()).decode(), "payloadType": "InlineBase64"}},
                {{"path": "settings.json", "payload": base64.b64encode(settings_json.encode()).decode(), "payloadType": "InlineBase64"}}
            ]
        }}
    }}

    update_resp = requests.post(
        f"{{BASE_URL}}/workspaces/{{ws_id}}/VariableLibraries/{{vl_id}}/updateDefinition",
        headers=headers, json=body
    )

    ref_count = sum(1 for v in variables if v["type"] == "ItemReference")
    str_count = sum(1 for v in variables if v["type"] == "String")

    if update_resp.ok or update_resp.status_code == 202:
        print(f"  ── Populated {{len(variables)}} variables ({{ref_count}} ItemReferences + {{str_count}} metadata)")
    else:
        print(f"  ── Could not update Variable Library: {{update_resp.text[:200]}}")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        fallback = os.path.join(script_dir, "variable-library-definition.json")
        with open(fallback, "w", encoding="utf-8", newline="\\n") as f:
            _json.dump(body, f, indent=2)
        print(f"  ── Definition saved to: {{fallback}}")


def main():
    parser = argparse.ArgumentParser(description="Deploy {safe_project}")
    parser.add_argument("--workspace-id", default=os.getenv("FABRIC_WORKSPACE_ID", ""))
    parser.add_argument("--workspace", default=os.getenv("FABRIC_WORKSPACE_NAME", ""))
    parser.add_argument("--mode", choices=["single", "multi"], default=os.getenv("FABRIC_DEPLOY_MODE", ""))
    parser.add_argument("--config", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yml"))
    args = parser.parse_args()

    try:
        import fabric_cicd
    except ImportError:
        print("  fabric-cicd is not installed.")
        response = input("  ? Install it now? [Y/n]: ").strip() or "Y"
        if response.upper() == "Y":
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "fabric-cicd"])
        else:
            sys.exit(1)

    print_banner()

    if not args.mode:
        print("    1)  Single workspace (demo / simple deploy)")
        print("    2)  Multi-environment (dev / ppe / prod)")
        print()
        choice = ""
        while choice not in ("1", "2"):
            choice = input("  ? Select mode (1 or 2): ").strip()
        args.mode = "single" if choice == "1" else "multi"

    credential = get_credential()
    headers = get_auth_headers(credential)

    if args.mode == "single":
        print()
        print("  -- WORKSPACE --")
        if args.workspace_id:
            ws_id = args.workspace_id
        else:
            ws_name = args.workspace or input("  ? Workspace name (Enter = {slug}): ").strip() or "{slug}"
            ws_id = ensure_workspace(ws_name, headers, "{ws_desc_line}")
        print()
        print("  -- CAPACITY --")
        ensure_capacity(ws_id, headers)
        print()
        print("  -- DEPLOYING --")
        try:
            deploy_to_workspace(args.config, ws_id, credential=credential)
            populate_variable_library(ws_id, headers)
            print()
            print("  " + "=" * 56)
            print("  DEPLOYMENT SUMMARY")
            print("  " + "=" * 56)
            print(f"  Project:    {safe_project}")
            print(f"  Task Flow:  {safe_task_flow}")
            print(f"  Items:      {item_count} across {wave_count} waves")
            print(f"  Workspace:  {{ws_name}}")
            print(f"  Portal:     https://app.fabric.microsoft.com/groups/{{ws_id}}")
            print()
            print("  Next Steps:")
            print(f"  - Review items in Fabric portal")
            print(f"  - Run: python run-pipeline.py advance --project {slug}")
            print("  " + "=" * 56)
        except Exception as e:
            print(f"  Deployment failed: {{e}}")
            sys.exit(1)
    else:
        base_name = args.workspace or input("  ? Base workspace name (Enter = {slug}): ").strip() or "{slug}"
        envs = ["dev", "ppe", "prod"]
        print()
        print("  -- WORKSPACES (3 environments) --")
        ws_ids = {{}}
        for env in envs:
            ws_name = f"{{base_name}}-{{env}}"
            print(f"  {{env.upper()}}:")
            ws_ids[env] = ensure_workspace(ws_name, headers, "{ws_desc_line}")
        print()
        print("  -- CAPACITY --")
        for env in envs:
            print(f"  {{env.upper()}}:")
            ensure_capacity(ws_ids[env], headers)
        print()
        print("  -- DEPLOYING (dev -> ppe -> prod) --")
        for env in envs:
            print(f"  Deploying to {{env.upper()}}...")
            try:
                deploy_to_workspace(args.config, ws_ids[env], environment=env, credential=credential)
                populate_variable_library(ws_ids[env], headers)
                print(f"  {{env.upper()}} complete!")
            except Exception as e:
                print(f"  {{env.upper()}} failed: {{e}}")
                sys.exit(1)
        print()
        print("  " + "=" * 56)
        print("  DEPLOYMENT SUMMARY")
        print("  " + "=" * 56)
        print(f"  Project:      {safe_project}")
        print(f"  Task Flow:    {safe_task_flow}")
        print(f"  Items:        {item_count} across {wave_count} waves")
        print(f"  Environments: dev, ppe, prod")
        for env in envs:
            print(f"    {{env.upper()}}: https://app.fabric.microsoft.com/groups/{{ws_ids[env]}}")
        print()
        print("  Next Steps:")
        print(f"  - Review items in Fabric portal")
        print(f"  - Run: python run-pipeline.py advance --project {slug}")
        print("  " + "=" * 56)


if __name__ == "__main__":
    main()
"""


# ─────────────────────────────────────────────────────────────────────────────
# Extracted helpers (called from main)
# ─────────────────────────────────────────────────────────────────────────────

def _gen_item_definitions(
    cicd_type: str, item: Item, data: HandoffData,
    safe_name: str, description: str, folder: str,
) -> dict[str, str]:
    """Return ``{relative_path: content}`` for an item's definition files.

    Templates are loaded from ``_shared/templates/{cicd_type}/`` — the single
    source of truth for empty-state item definitions.  These files are
    byte-for-byte what fabric-cicd will base64-encode and POST to the Fabric
    Items API.

    A small number of *dynamic* types customise the template with runtime
    values (item name, dependency paths, etc.).  All others are copied
    verbatim.
    """
    # ── Dynamic types: need runtime values ──────────────────────────────────

    if cicd_type == "Notebook":
        # Embed item name and description into the notebook cell
        tpl = _load_template_files(cicd_type)
        if tpl and "notebook-content.py" in tpl:
            base = tpl["notebook-content.py"]
            base = base.replace(
                "# Welcome to your new notebook\n# Type here in the cell editor to add code!",
                f"# {safe_name} — {description}\nprint(\"{safe_name} initialized\")",
            )
            return {"notebook-content.py": base}
        # Inline fallback
        nb_content = (
            "# Fabric notebook source\n\n"
            "# METADATA ********************\n\n"
            "# META {\n"
            '# META   "kernel_info": {\n'
            '# META     "name": "synapse_pyspark"\n'
            "# META   }\n"
            "# META }\n\n"
            "# CELL ********************\n\n"
            f"# {safe_name} — {description}\n"
            f'print("{safe_name} initialized")\n\n'
            "# METADATA ********************\n\n"
            "# META {\n"
            '# META   "language": "python",\n'
            '# META   "language_group": "synapse_pyspark"\n'
            "# META }\n"
        )
        return {"notebook-content.py": nb_content}

    if cicd_type == "Report":
        # Resolve semantic model relative path from dependencies
        items_by_id = {i.id: i for i in data.items}
        sm_path = ""
        for dep_id in (item.depends_on or []):
            dep = items_by_id.get(dep_id)
            if dep and _cicd_type(dep.type) == "SemanticModel":
                dep_safe = _cli_safe_name(dep.name)
                dep_folder = _get_folder_for_item(dep.type) or ""
                if folder and dep_folder:
                    sm_path = f"../../{dep_folder}/{dep_safe}.SemanticModel"
                elif dep_folder:
                    sm_path = f"../{dep_folder}/{dep_safe}.SemanticModel"
                else:
                    sm_path = f"../{dep_safe}.SemanticModel"
                break

        # Load report.json from template, customise definition.pbir
        tpl = _load_template_files(cicd_type) or {}
        pbir = json.dumps({
            "version": "4.0",
            "datasetReference": {"byPath": {"path": sm_path}}
        }, indent=2)
        report_json = tpl.get("report.json", json.dumps({
            "config": "{}",
            "layoutOptimization": 0,
            "sections": []
        }, indent=2))
        return {
            "definition.pbir": pbir,
            "report.json": report_json,
        }

    if cicd_type == "SQLDatabase":
        # Embed item name into .sqlproj filename and content
        tpl = _load_template_files(cicd_type)
        if tpl and "template.sqlproj" in tpl:
            content = tpl["template.sqlproj"].replace("{{ITEM_NAME}}", safe_name)
            return {f"{safe_name}.sqlproj": content}
        sqlproj = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<Project DefaultTargets="Build">\n'
            '  <Sdk Name="Microsoft.Build.Sql" Version="1.0.0-rc1" />\n'
            '  <PropertyGroup>\n'
            f'    <Name>{safe_name}</Name>\n'
            '    <ProjectGuid>{{00000000-0000-0000-0000-000000000000}}</ProjectGuid>\n'
            '    <DSP>Microsoft.Data.Tools.Schema.Sql.SqlDbFabricDatabaseSchemaProvider</DSP>\n'
            '    <ModelCollation>1033, CI</ModelCollation>\n'
            '  </PropertyGroup>\n'
            '  <Target Name="BeforeBuild">\n'
            '    <Delete Files="$(BaseIntermediateOutputPath)\\project.assets.json" />\n'
            '  </Target>\n'
            '</Project>\n'
        )
        return {f"{safe_name}.sqlproj": sqlproj}

    # ── All other types: load from _shared/templates/ (source of truth) ─────

    tpl = _load_template_files(cicd_type)
    if tpl:
        return tpl

    # Types with no definition files (e.g. KQLDashboard, Lakehouse platform-only)
    return {}


def _inject_variable_library(slug: str, project: str, ws_dir: Path) -> None:
    """Write an auto-injected Variable Library when the handoff omits one."""
    vl_name = _cli_safe_name(f"{slug}_variable_library")
    vl_dir = ws_dir / "Configuration" / f"{vl_name}.VariableLibrary"
    vl_dir.mkdir(parents=True, exist_ok=True)
    vl_platform = _gen_platform_file(
        "VariableLibrary", vl_name,
        f"Variable Library for {project} — CI/CD stage configuration"
    )
    (vl_dir / ".platform").write_text(vl_platform, encoding="utf-8", newline="\n")
    # Load from templates directory (source of truth)
    tpl = _load_template_files("VariableLibrary")
    if tpl:
        for filename, content in tpl.items():
            filepath = vl_dir / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(content, encoding="utf-8", newline="\n")
    else:
        # Inline fallback
        variables = {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/variableLibrary/definition/variables/1.0.0/schema.json",
            "variables": []
        }
        (vl_dir / "variables.json").write_text(json.dumps(variables, indent=2), encoding="utf-8", newline="\n")
        settings = {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/variableLibrary/definition/settings/1.0.0/schema.json",
            "valueSetsOrder": []
        }
        (vl_dir / "settings.json").write_text(json.dumps(settings, indent=2), encoding="utf-8", newline="\n")


def _gen_parameter_yml(data: HandoffData, project: str) -> str:
    """Generate the full text content of parameter.yml."""
    param_lines = [
        f"# Parameter file for {project}",
        f"# Task flow: {data.task_flow}",
        "# Ref: https://microsoft.github.io/fabric-cicd/latest/how_to/parameterization/",
        "",
        "find_replace:",
    ]

    for item in data.items:
        if not item.name:
            continue
        safe_name = _cli_safe_name(item.name)
        cicd_type = _cicd_type(item.type)
        if not cicd_type:
            continue

        if cicd_type in ("Notebook",):
            param_lines += [
                f"  # {safe_name} — default lakehouse workspace ID",
                '  - find_value: "00000000-0000-0000-0000-000000000000"',
                "    replace_value:",
                '      dev: "$workspace.id"',
                '      ppe: "$workspace.id"',
                '      prod: "$workspace.id"',
                f'    item_name: "{safe_name}"',
                "",
            ]

    # Generateitem-specific replacements for items that reference other items
    for item in data.items:
        if not item.name or not item.depends_on:
            continue
        safe_name = _cli_safe_name(item.name)
        cicd_type = _cicd_type(item.type)
        if not cicd_type:
            continue

        items_by_id = {i.id: i for i in data.items}
        for dep_id in item.depends_on:
            dep = items_by_id.get(dep_id)
            if not dep or not dep.name:
                continue
            dep_safe = _cli_safe_name(dep.name)
            dep_cicd = _cicd_type(dep.type)
            if not dep_cicd:
                continue

            param_lines += [
                f"  # {safe_name} → {dep_safe} reference",
                f'  - find_value: "placeholder-{dep_safe}-id"',
                "    replace_value:",
                f'      dev: "$items.{dep_cicd}.{dep_safe}.id"',
                f'      ppe: "$items.{dep_cicd}.{dep_safe}.id"',
                f'      prod: "$items.{dep_cicd}.{dep_safe}.id"',
                f'    item_name: "{safe_name}"',
                "",
            ]

    return "\n".join(param_lines) + "\n"


def _gen_descriptions_json(data: HandoffData, project: str) -> str:
    """Generate the descriptions JSON content."""
    ws_desc = f"{project} — {data.task_flow} architecture"
    if data.summary:
        ws_desc += f". {data.summary}"
    desc_data = {
        "project": project,
        "task_flow": data.task_flow,
        "workspace_description": ws_desc,
        "items": {}
    }
    for item in data.items:
        if not item.name:
            continue
        safe_name = _cli_safe_name(item.name)
        desc_data["items"][safe_name] = {
            "type": item.type,
            "description": item.purpose or f"{item.type} for {project}",
            "folder": _get_folder_for_item(item.type) or "root",
        }
    return json.dumps(desc_data, indent=2, ensure_ascii=False)


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate fabric-cicd deployment artifacts from architecture handoffs"
    )
    parser.add_argument("--handoff", required=True, help="Path to architecture-handoff.md")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--output-dir", default=None, help="Directory for output artifacts")
    args = parser.parse_args()

    data = parse_handoff(args.handoff)
    slug = _slugify(args.project)

    if not args.output_dir:
        print("Error: --output-dir is required", file=sys.stderr)
        sys.exit(1)

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Check for existing manifest (idempotency warning)
    manifest_path = out / "_deploy_manifest.json"
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        print(f"⚠ Re-generating artifacts (previous run: {old.get('generated_at', 'unknown')})", file=sys.stderr)

    # 1. Generate workspace directory with item folders and .platform files
    ws_dir = out / "workspace"
    ws_dir.mkdir(exist_ok=True)

    has_vl = any(
        _cicd_type(item.type) == "VariableLibrary"
        for item in data.items if item.name
    )

    # REST-only types skip workspace directory creation (created via REST API post-deploy)

    for item in data.items:
        if not item.name:
            continue
        safe_name = _cli_safe_name(item.name)
        cicd_type = _cicd_type(item.type)
        if not cicd_type:
            continue  # Skip unsupported types (Dashboard, MLModel)
        folder = _get_folder_for_item(item.type) or ""
        description = item.purpose or f"{item.type} for {args.project}"

        # Create folder structure: workspace/FolderName/item_name.ItemType/.platform
        if folder:
            item_dir = ws_dir / folder / f"{safe_name}.{cicd_type}"
        else:
            item_dir = ws_dir / f"{safe_name}.{cicd_type}"
        item_dir.mkdir(parents=True, exist_ok=True)

        platform_content = _gen_platform_file(item.type, safe_name, description)
        (item_dir / ".platform").write_text(platform_content, encoding="utf-8", newline="\n")

        # Generate required definition files per item type
        definitions = _gen_item_definitions(cicd_type, item, data, safe_name, description, folder)
        for filename, content in definitions.items():
            filepath = item_dir / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(content, encoding="utf-8", newline="\n")

    # Auto-inject Variable Library if not already present
    if not has_vl:
        _inject_variable_library(slug, args.project, ws_dir)

    item_count = len([i for i in data.items if i.name]) + (0 if has_vl else 1)
    print(f"✅ {ws_dir}/ ({item_count} items)")

    # 2. Generate parameter.yml
    param_content = _gen_parameter_yml(data, args.project)
    param_path = ws_dir / "parameter.yml"
    param_path.write_text(param_content, encoding="utf-8", newline="\n")

    # 3. Generate config.yml
    ws_desc = f"{args.project} — {data.task_flow} architecture"
    if data.summary:
        ws_desc += f". {data.summary}"

    config_content = _gen_config_yml(data, args.project, ws_desc)
    config_path = out / "config.yml"
    config_path.write_text(config_content, encoding="utf-8", newline="\n")
    print(f"✅ {config_path}")

    # 3. Generate thin deploy script
    deploy_content = _gen_deploy_script(args.project, data)
    deploy_path = out / f"deploy-{slug}.py"
    deploy_path.write_text(deploy_content, encoding="utf-8", newline="\n")
    print(f"✅ {deploy_path}")

    # 4. Generate descriptions JSON
    desc_path = out / f"descriptions-{slug}.json"
    desc_path.write_text(_gen_descriptions_json(data, args.project), encoding="utf-8", newline="\n")
    print(f"✅ {desc_path}")

    # 5. Generate task flow JSON template
    try:
        tf_gen_path = Path(__file__).resolve().parent / "taskflow-template-gen.py"
        if tf_gen_path.exists():
            import subprocess as _sp
            tf_path = out / f"taskflow-{slug}.json"
            _sp.run(
                [sys.executable, str(tf_gen_path),
                 "--handoff", args.handoff,
                 "--project", args.project,
                 "--output", str(tf_path)],
                capture_output=True, text=True, timeout=30, encoding="utf-8",
            )
            if tf_path.exists():
                print(f"✅ {tf_path}")
    except Exception as e:
        print(f"⚠️  Task flow template generation skipped: {e}", file=sys.stderr)

    # 6. Write deployment manifest for idempotency tracking
    artifacts = []
    for platform_file in ws_dir.rglob(".platform"):
        artifacts.append({
            "path": str(platform_file.parent.relative_to(out)),
            "type": "platform",
        })
    artifacts.append({"path": str(param_path.relative_to(out)), "type": "config"})
    artifacts.append({"path": str(config_path.relative_to(out)), "type": "config"})
    artifacts.append({"path": str(deploy_path.relative_to(out)), "type": "deploy_script"})
    artifacts.append({"path": str(desc_path.relative_to(out)), "type": "config"})
    tf_path = out / f"taskflow-{slug}.json"
    if tf_path.exists():
        artifacts.append({"path": str(tf_path.relative_to(out)), "type": "config"})
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": args.project,
        "artifacts": artifacts,
    }
    manifest_path = out / "_deploy_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8", newline="\n")
    print(f"✅ {manifest_path}")


if __name__ == "__main__":
    main()
