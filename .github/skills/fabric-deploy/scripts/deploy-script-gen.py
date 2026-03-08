#!/usr/bin/env python3
"""
Generate deployment shell scripts from architecture handoffs.

Reads an architecture-handoff.md (with items_to_deploy and deployment_waves
YAML blocks) and generates filled .sh and .ps1 deploy scripts from the
templates in _shared/.

Usage:
    python scripts/deploy-script-gen.py --handoff projects/my-project/prd/architecture-handoff.md --project "My Project"
    python scripts/deploy-script-gen.py --handoff projects/my-project/prd/architecture-handoff.md --project "My Project" --output-dir projects/my-project/deployments/
    python scripts/deploy-script-gen.py --handoff projects/my-project/prd/architecture-handoff.md --project "My Project" --shell bash

Importable:
    from deploy_script_gen import generate
    bash_script, ps1_script = generate("projects/x/prd/architecture-handoff.md", "My Project")
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
ASSETS_DIR = SKILL_DIR / "assets"

# ─────────────────────────────────────────────────────────────────────────────
# Item type → fab command mapping
# ─────────────────────────────────────────────────────────────────────────────

# Item type mappings — loaded from _shared/item-type-registry.json
# Do NOT maintain these dicts manually. See CONTRIBUTING.md.
_SHARED_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "_shared"
sys.path.insert(0, str(_SHARED_DIR))
from registry_loader import build_fab_commands, build_display_names

FAB_COMMANDS: dict[str, tuple[str, list[str]] | None] = build_fab_commands()
DISPLAY_NAMES: dict[str, str] = build_display_names()
REGISTRY: dict = json.loads((_SHARED_DIR / "item-type-registry.json").read_text(encoding="utf-8"))

# Task-flow-specific prompts
TASK_FLOW_PROMPTS: dict[str, list[tuple[str, str, str, str, bool]]] = {
    # (env_var, prompt_text, default, description, optional)
    "event-analytics": [
        ("EVENT_HUB_NAMESPACE", "Event Hub namespace (Azure Event Hubs that streams events into Fabric)", "", "Azure Event Hub namespace for streaming", True),
        ("EVENT_HUB_CONSUMER_GROUP", "Event Hub consumer group (isolates this pipeline's read position — use $Default if unsure)", "$Default", "Consumer group controls which reader offset Eventstream uses", False),
    ],
    "event-medallion": [
        ("EVENT_HUB_NAMESPACE", "Event Hub namespace (Azure Event Hubs that streams events into Fabric)", "", "Azure Event Hub namespace for streaming", True),
        ("EVENT_HUB_CONSUMER_GROUP", "Event Hub consumer group (isolates this pipeline's read position — use $Default if unsure)", "$Default", "Consumer group controls which reader offset Eventstream uses", False),
    ],
    "medallion": [
        ("SOURCE_CONNECTION_STRING", "Source database connection string (e.g., SQL Server, PostgreSQL — used by Copy Job)", "", "Connection to source database", True),
    ],
    "lambda": [
        ("SOURCE_CONNECTION_STRING", "Source database connection string (e.g., SQL Server, PostgreSQL — used by Copy Job)", "", "Connection to source database", True),
        ("EVENT_HUB_NAMESPACE", "Event Hub namespace (Azure Event Hubs that streams events into Fabric)", "", "Azure Event Hub namespace for streaming", True),
        ("EVENT_HUB_CONSUMER_GROUP", "Event Hub consumer group (isolates this pipeline's read position — use $Default if unsure)", "$Default", "Consumer group controls which reader offset Eventstream uses", False),
    ],
    "app-backend": [
        ("API_FRONTEND_URL", "API frontend URL (the app that will call the GraphQL/REST endpoints)", "", "URL of the application frontend", True),
    ],
    "sensitive-data-insights": [
        ("KEY_VAULT_URL", "Key Vault URL (Azure Key Vault storing encryption keys for PII masking)", "", "Azure Key Vault for encryption keys", True),
        ("ENCRYPTION_KEY_NAME", "Encryption key name (key used by masking notebooks)", "", "Name of the encryption key", True),
    ],
}


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
# YAML extraction (regex-based, same approach as other scripts)
# ─────────────────────────────────────────────────────────────────────────────

def _extract_yaml_blocks(markdown: str) -> list[str]:
    """Extract all ```yaml ... ``` fenced code blocks."""
    return re.findall(r"```yaml\s*\n(.*?)```", markdown, re.DOTALL)


def _extract_task_flow(markdown: str) -> str:
    """Extract task_flow from YAML frontmatter."""
    fm = re.match(r"^---\s*\n(.*?)\n---", markdown, re.DOTALL)
    if fm:
        m = re.search(r"^task_flow:\s*(.+)$", fm.group(1), re.MULTILINE)
        if m:
            return m.group(1).strip()
    # Fallback: look in body
    m = re.search(r"\*\*Task [Ff]low:\*\*\s*(.+)", markdown)
    if m:
        val = m.group(1).strip()
        # Take first word/phrase (might have extra description after)
        val = re.split(r"\s*[\(\[]", val)[0].strip()
        return val
    return "unknown"


def _parse_yaml_value(raw: str) -> str | int | float | bool | list | None:
    """Minimal YAML scalar/inline-list parser."""
    raw = raw.strip()
    if raw in ("", "~", "null"):
        return None
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [_parse_yaml_value(v) for v in _split_list(inner)]
    if raw.lower() in ("true", "yes"):
        return True
    if raw.lower() in ("false", "no"):
        return False
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    # Strip quotes
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]
    return raw


def _split_list(s: str) -> list[str]:
    """Split comma-separated values, respecting quotes."""
    parts: list[str] = []
    current: list[str] = []
    in_quotes = False
    quote_char = ""
    for ch in s:
        if ch in ('"', "'") and not in_quotes:
            in_quotes = True
            quote_char = ch
            current.append(ch)
        elif ch == quote_char and in_quotes:
            in_quotes = False
            current.append(ch)
        elif ch == "," and not in_quotes:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current).strip())
    return parts


def _parse_inline_mapping(line: str) -> dict[str, str | int | float | bool | list | None]:
    """Parse a YAML inline mapping like {id: 1, name: foo, depends_on: [1,2]}."""
    line = line.strip()
    if line.startswith("{") and line.endswith("}"):
        line = line[1:-1]

    result: dict[str, str | int | float | bool | list | None] = {}
    # Split on comma but respect brackets and quotes
    depth = 0
    in_quotes = False
    quote_char = ""
    parts: list[str] = []
    current: list[str] = []

    for ch in line:
        if ch in ('"', "'") and not in_quotes:
            in_quotes = True
            quote_char = ch
            current.append(ch)
        elif ch == quote_char and in_quotes:
            in_quotes = False
            current.append(ch)
        elif ch == "[":
            depth += 1
            current.append(ch)
        elif ch == "]":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0 and not in_quotes:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current))

    for part in parts:
        part = part.strip()
        colon_idx = part.find(":")
        if colon_idx == -1:
            continue
        key = part[:colon_idx].strip()
        val = part[colon_idx + 1:].strip()
        result[key] = _parse_yaml_value(val)

    return result


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
    """Convert a parsed dict to an Item dataclass."""
    name = d.get("name", d.get("item_name", ""))
    item_type = d.get("type", d.get("item_type", ""))
    deps_raw = d.get("dependencies", d.get("depends_on", "[]"))
    if isinstance(deps_raw, list):
        deps = [int(x) for x in deps_raw]
    elif isinstance(deps_raw, str) and deps_raw.startswith("["):
        inner = deps_raw[1:-1].strip()
        deps = [int(x.strip().strip('"').strip("'")) for x in inner.split(",") if x.strip()] if inner else []
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
    """Parse an architecture-handoff.md and extract structured data."""
    content = Path(path).read_text(encoding="utf-8")
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

    if not items:
        print(f"⚠ No items found in {path}", file=sys.stderr)
    if not waves:
        print(f"⚠ No waves found in {path}", file=sys.stderr)

    return HandoffData(task_flow=task_flow, items=items, waves=waves, summary=summary)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _slugify(name: str) -> str:
    """Convert project name to kebab-case."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s]+", "-", s)
    return s.strip("-")


def _type_key(item_type: str) -> str:
    """Normalize item type for FAB_COMMANDS lookup."""
    return item_type.lower().replace("_", "").replace(" ", "").replace("-", "")


def _is_portal_only(item_type: str) -> bool:
    key = _type_key(item_type)
    return FAB_COMMANDS.get(key) is None and FAB_COMMANDS.get(item_type.lower()) is None


def _cli_safe_name(name: str) -> str:
    """Convert item name to CLI-safe format (underscores instead of hyphens).

    Fabric CLI rejects hyphens in item names for multiple item types
    (Lakehouse, Eventstream, MLExperiment, MLModel, and potentially others).
    Rather than maintain an incomplete allowlist, we universally convert
    hyphens to underscores for all item types.
    """
    return name.replace("-", "_")


def _get_fab_command(item: Item) -> tuple[str, list[str]] | None:
    """Return (path_template, extra_args) for an item, or None if portal-only.
    Items are created at workspace root — folders are for Portal organization."""
    key = _type_key(item.type)
    entry = FAB_COMMANDS.get(key)
    if entry is None:
        entry = FAB_COMMANDS.get(item.type.lower())
    if entry is not None:
        path_tpl, extra_args = entry
        safe_name = _cli_safe_name(item.name)
        path = path_tpl.replace("{name}", safe_name)
        return (path, extra_args)
    return None


def _get_display_type(item_type: str) -> str:
    key = _type_key(item_type)
    return DISPLAY_NAMES.get(key, DISPLAY_NAMES.get(item_type.lower(), item_type))


def _resolve_fab_type(item_type: str) -> str:
    """Resolve item type to its Fabric CLI type name (e.g., 'Pipeline' → 'DataPipeline')."""
    key = _type_key(item_type)
    entry = FAB_COMMANDS.get(key) or FAB_COMMANDS.get(item_type.lower())
    if entry is not None:
        path_tpl = entry[0]
        # Extract type from path template: "{ws}.Workspace/{name}.TypeName" → "TypeName"
        return path_tpl.split(".")[-1]
    return item_type


def _has_or_alternatives(data: HandoffData) -> list[tuple[Item, Item]]:
    """Detect items that are ──OR── alternatives."""
    alternatives: list[tuple[Item, Item]] = []
    items_by_name = {item.name: item for item in data.items}
    # Check for items with "Alternative to" note from scaffolder
    for item in data.items:
        if hasattr(item, "purpose") and "alternative" in str(getattr(item, "purpose", "")).lower():
            continue
    # Fallback: group by same non-zero id
    if not alternatives:
        seen_ids: dict[int, list[Item]] = {}
        for item in data.items:
            if item.id != 0:
                seen_ids.setdefault(item.id, []).append(item)
        alternatives = [(g[0], g[1]) for g in seen_ids.values() if len(g) >= 2]
    return alternatives


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
}


def _get_item_phase(item_type: str) -> str:
    """Get the deployment phase for an item type from the registry."""
    key = _type_key(item_type)
    for type_name, type_info in REGISTRY.get("types", {}).items():
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


def _gen_folder_creation_ps1(data: "HandoffData", ws_var: str) -> str:
    """Generate PowerShell folder creation calls before wave deployment."""
    folders = _collect_folders(data)
    if not folders:
        return ""
    lines = [
        "",
        "  # ─────────────────────────────────────────────────────────────────",
        "  # Workspace Folders",
        "  # ─────────────────────────────────────────────────────────────────",
        '  Write-Host ""',
        '  Write-Host "  Workspace Folders"',
    ]
    for idx, folder in enumerate(folders):
        connector = "└──" if idx == len(folders) - 1 else "├──"
        lines.append(f'  New-FabFolder -WorkspacePath $wsPath -FolderName "{folder}" -TreeChar "{connector}"')
    lines.append("")
    return "\n".join(lines)


def _gen_folder_creation_bash(data: "HandoffData", ws_var: str) -> str:
    """Generate bash folder creation calls before wave deployment."""
    folders = _collect_folders(data)
    if not folders:
        return ""
    lines = [
        "",
        "  # ─────────────────────────────────────────────────────────────────",
        "  # Workspace Folders",
        "  # ─────────────────────────────────────────────────────────────────",
        '  echo ""',
        '  echo "  Workspace Folders"',
    ]
    for idx, folder in enumerate(folders):
        connector = "└──" if idx == len(folders) - 1 else "├──"
        lines.append(f'  fab_create_folder "{ws_var}.Workspace" "{folder}" "{connector}"')
    lines.append("")
    return "\n".join(lines)


def _build_item_lookup(data: HandoffData) -> dict[str, Item]:
    lookup: dict[str, Item] = {}
    for item in data.items:
        lookup[item.name] = item
        lookup[str(item.id)] = item
    return lookup


def _tree_connector(idx: int, total: int) -> str:
    return "└──" if idx == total - 1 else "├──"


# ─────────────────────────────────────────────────────────────────────────────
# Code generation: Python deploy script
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# fabric-cicd directory structure generation
# ─────────────────────────────────────────────────────────────────────────────

import uuid as _uuid

# fabric-cicd supported item types and our type name mappings
_FABRIC_CICD_TYPES = {
    "ApacheAirflowJob", "CopyJob", "DataAgent", "DataPipeline", "Dataflow",
    "Environment", "Eventhouse", "Eventstream", "GraphQLApi", "KQLDashboard",
    "KQLDatabase", "KQLQueryset", "Lakehouse", "MLExperiment", "MirroredDatabase",
    "MountedDataFactory", "Notebook", "Reflex", "Report", "SQLDatabase",
    "SemanticModel", "SparkJobDefinition", "UserDataFunction", "VariableLibrary", "Warehouse",
}
_TYPE_REMAP = {
    "Activator": "Reflex",
    "Real-Time Dashboard": "KQLDashboard",
    "KQL Dashboard": "KQLDashboard",
    "ML Experiment": "MLExperiment",
    "ML Model": "MLExperiment",  # MLModel not supported; shell only via MLExperiment
}


def _cicd_type(item_type: str) -> str:
    """Resolve item type to fabric-cicd compatible name. Returns empty string if unsupported."""
    fab_type = _resolve_fab_type(item_type)
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
    raw_types = set()
    for item in data.items:
        if not item.name:
            continue
        ct = _cicd_type(item.type)
        if ct:
            raw_types.add(ct)
    item_types = sorted(raw_types)

    # Collect unique folder names
    folders = _collect_folders(data)

    lines = [
        f"# fabric-cicd configuration for {project}",
        f"# Task flow: {data.task_flow}",
        f"# Generated by deploy-script-gen.py",
        "",
        "core:",
        f"  # Set workspace name or ID per environment",
        f"  workspace: {slug}-dev",
        f"  repository_directory: ./workspace",
        f"  item_types_in_scope:",
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

    return "\n".join(lines) + "\n"


def _gen_deploy_script(project: str, data: HandoffData) -> str:
    """Generate a thin deploy.py that uses fabric-cicd."""
    slug = _slugify(project)
    ws_desc_line = f"{project} — {data.task_flow} architecture"
    if data.summary:
        ws_desc_line += f". {data.summary}"

    return f"""#!/usr/bin/env python3
\"""
Fabric Task Flows - Deploy Script
Project:   {project}
Task Flow: {data.task_flow}

Uses fabric-cicd (pip install fabric-cicd) for deployment.
\"""

import argparse
import os
import sys
import yaml

BASE_URL = "https://api.fabric.microsoft.com/v1"


def get_auth_headers():
    try:
        from azure.identity import DefaultAzureCredential
        import requests
        token = DefaultAzureCredential().get_token("https://api.fabric.microsoft.com/.default").token
        return {{"Authorization": f"Bearer {{token}}", "Content-Type": "application/json"}}
    except ImportError:
        print("  -- azure-identity not installed. Run: pip install azure-identity")
        sys.exit(1)


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


def deploy_to_workspace(config_path, ws_id, environment=None):
    from fabric_cicd import deploy_with_config
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    config["core"]["workspace_id"] = ws_id
    config["core"].pop("workspace", None)
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    kwargs = {{"config_file_path": config_path}}
    if environment:
        kwargs["environment"] = environment

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
    from datetime import datetime
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
    variables.append({{"name": "Project_Name", "type": "String", "value": "{project}", "note": "Project name"}})
    variables.append({{"name": "Environment_Name", "type": "String", "value": "dev", "note": "Current deployment stage"}})
    variables.append({{"name": "Deploy_Timestamp", "type": "String", "value": datetime.utcnow().isoformat() + "Z", "note": "Deployment timestamp"}})

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
        with open(fallback, "w", encoding="utf-8") as f:
            _json.dump(body, f, indent=2)
        print(f"  ── Definition saved to: {{fallback}}")


def main():
    parser = argparse.ArgumentParser(description="Deploy {project}")
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

    print()
    print("  Project:   {project}")
    print("  Task Flow: {data.task_flow}")
    print()

    if not args.mode:
        print("    1)  Single workspace (demo / simple deploy)")
        print("    2)  Multi-environment (dev / ppe / prod)")
        print()
        choice = ""
        while choice not in ("1", "2"):
            choice = input("  ? Select mode (1 or 2): ").strip()
        args.mode = "single" if choice == "1" else "multi"

    headers = get_auth_headers()

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
            deploy_to_workspace(args.config, ws_id)
            populate_variable_library(ws_id, headers)
            print()
            print("  Deployment complete!")
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
                deploy_to_workspace(args.config, ws_ids[env], environment=env)
                populate_variable_library(ws_ids[env], headers)
                print(f"  {{env.upper()}} complete!")
            except Exception as e:
                print(f"  {{env.upper()}} failed: {{e}}")
                sys.exit(1)
        print()
        print("  All environments deployed!")


if __name__ == "__main__":
    main()
"""


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def generate(handoff_path: str, project: str) -> None:
    """Generate fabric-cicd deployment artifacts from a handoff file.

    Creates:
        - workspace/ directory with item subdirectories and .platform files
        - config.yml for fabric-cicd
        - deploy-{slug}.py thin deploy script
        - descriptions-{slug}.json (central definitions)
        - taskflow-{slug}.json (importable task flow)
    """
    pass  # Called from main() which handles output


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

    # 1. Generate workspace directory with item folders and .platform files
    ws_dir = out / "workspace"
    ws_dir.mkdir(exist_ok=True)

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
        (item_dir / ".platform").write_text(platform_content, encoding="utf-8")

        # Generate required definition files per item type
        if cicd_type == "Environment":
            setting_dir = item_dir / "Setting"
            setting_dir.mkdir(exist_ok=True)
            sparkcompute = {
                "instancePool": "",
                "targetPlatform": "spark",
                "runtimeVersion": "1.3",
                "automaticLog": {"enabled": True},
            }
            (setting_dir / "Sparkcompute.yml").write_text(
                "instancePool: \"\"\ntargetPlatform: spark\nruntimeVersion: \"1.3\"\nautomaticLog:\n  enabled: true\n",
                encoding="utf-8"
            )

        elif cicd_type == "VariableLibrary":
            variables = {
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/variableLibrary/definition/variables/1.0.0/schema.json",
                "variables": [
                    {"name": "workspace_id", "type": "String", "value": "", "note": "Workspace ID — set at deploy time"},
                ]
            }
            (item_dir / "variables.json").write_text(json.dumps(variables, indent=2), encoding="utf-8")
            settings = {
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/variableLibrary/definition/settings/1.0.0/schema.json",
                "valueSetsOrder": []
            }
            (item_dir / "settings.json").write_text(json.dumps(settings, indent=2), encoding="utf-8")

        elif cicd_type == "Notebook":
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
            (item_dir / "notebook-content.py").write_text(nb_content, encoding="utf-8")

        elif cicd_type == "SemanticModel":
            # definition.pbism + definition/model.tmdl required
            (item_dir / "definition.pbism").write_text(
                json.dumps({"version": "4.0", "settings": {}}, indent=2),
                encoding="utf-8"
            )
            def_dir = item_dir / "definition"
            def_dir.mkdir(exist_ok=True)
            (def_dir / "model.tmdl").write_text(
                "model Model\n"
                "\tculture: en-US\n"
                "\tdefaultPowerBIDataSourceVersion: powerBI_V3\n"
                "\tsourceQueryCulture: en-US\n",
                encoding="utf-8"
            )

        elif cicd_type == "Report":
            # definition.pbir + report.json required
            # Find the SemanticModel dependency for byPath reference
            items_by_id = {i.id: i for i in data.items}
            sm_path = None
            for dep_id in (item.depends_on or []):
                dep = items_by_id.get(dep_id)
                if dep and _cicd_type(dep.type) == "SemanticModel":
                    dep_safe = _cli_safe_name(dep.name)
                    dep_folder = _get_folder_for_item(dep.type) or ""
                    # Build relative path from Report dir to SemanticModel dir
                    if folder and dep_folder:
                        sm_path = f"../../{dep_folder}/{dep_safe}.SemanticModel"
                    elif dep_folder:
                        sm_path = f"../{dep_folder}/{dep_safe}.SemanticModel"
                    else:
                        sm_path = f"../{dep_safe}.SemanticModel"
                    break

            pbir = {"version": "4.0", "datasetReference": {}}
            if sm_path:
                pbir["datasetReference"]["byPath"] = {"path": sm_path}
            else:
                pbir["datasetReference"]["byPath"] = {"path": ""}
            (item_dir / "definition.pbir").write_text(json.dumps(pbir, indent=2), encoding="utf-8")
            report_json = {
                "config": json.dumps({
                    "version": "5.59",
                    "themeCollection": {"baseTheme": {"name": "CY24SU10", "version": "5.61", "type": 2}},
                    "activeSectionIndex": 0,
                    "settings": {"useNewFilterPaneExperience": True, "allowChangeFilterTypes": True}
                }),
                "layoutOptimization": 0,
                "sections": [{
                    "config": "{}",
                    "displayName": "Page 1",
                    "displayOption": 1,
                    "filters": "[]",
                    "height": 720.0,
                    "name": "ReportSection",
                    "visualContainers": [],
                    "width": 1280.0
                }]
            }
            (item_dir / "report.json").write_text(json.dumps(report_json, indent=2), encoding="utf-8")

        elif cicd_type == "DataPipeline":
            pipeline_content = {"properties": {"activities": []}}
            (item_dir / "pipeline-content.json").write_text(json.dumps(pipeline_content, indent=2), encoding="utf-8")

        elif cicd_type == "CopyJob":
            # From sample: Hello Copy Job.CopyJob
            copyjob = {"properties": {"jobMode": "Batch", "source": {"type": "LakehouseTable"}, "destination": {"type": "LakehouseTable"}, "policy": {"timeout": "0.12:00:00"}}, "activities": []}
            (item_dir / "copyjob-content.json").write_text(json.dumps(copyjob, indent=2), encoding="utf-8")

        elif cicd_type == "Eventstream":
            # VERIFIED from sample: SampleEventstream.Eventstream
            (item_dir / "eventstream.json").write_text(json.dumps({"compatibilityLevel": "1.0", "sources": [], "destinations": []}, indent=2), encoding="utf-8")
            (item_dir / "eventstreamProperties.json").write_text(json.dumps({"retentionTimeInDays": 1, "eventThroughputLevel": "Low"}, indent=2), encoding="utf-8")

        elif cicd_type == "KQLQueryset":
            # VERIFIED from sample: SampleKQLQueryset.KQLQueryset
            queryset = {"queryset": {"version": "1.0.0", "dataSources": [], "tabs": []}}
            (item_dir / "RealTimeQueryset.json").write_text(json.dumps(queryset, indent=2), encoding="utf-8")

        elif cicd_type == "Eventhouse":
            # VERIFIED from sample: SampleEventhouse.Eventhouse — just empty object
            (item_dir / "EventhouseProperties.json").write_text("{}", encoding="utf-8")

        elif cicd_type == "KQLDashboard":
            # KQLDashboard: create without definition supported — no content file needed
            # Content file causes 'NoneType' errors; shell creation is sufficient
            pass

        elif cicd_type == "Reflex":
            # VERIFIED from sample: SampleDataActivator.Reflex — empty array
            (item_dir / "ReflexEntities.json").write_text("[]", encoding="utf-8")

        elif cicd_type == "Dataflow":
            (item_dir / "mashup.pq").write_text('section Section1;\n\nshared Table = let\n    Source = ""\nin\n    Source;\n', encoding="utf-8")

        elif cicd_type == "GraphQLApi":
            # From sample: Sample.GraphQLApi
            (item_dir / "graphql-definition.json").write_text(json.dumps({"datasources": []}, indent=2), encoding="utf-8")

        elif cicd_type == "SparkJobDefinition":
            (item_dir / "SparkJobDefinitionV1.json").write_text(json.dumps({
                "executableFile": None, "defaultLakehouseArtifactId": "", "mainClass": ""
            }, indent=2), encoding="utf-8")

        elif cicd_type == "SQLDatabase":
            # From sample: Hello db.SQLDatabase
            sqlproj = (
                '<?xml version="1.0" encoding="utf-8"?>\n'
                '<Project DefaultTargets="Build">\n'
                '  <Sdk Name="Microsoft.Build.Sql" Version="1.0.0-rc1" />\n'
                '  <PropertyGroup>\n'
                f'    <Name>{safe_name}</Name>\n'
                '    <ProjectGuid>{00000000-0000-0000-0000-000000000000}</ProjectGuid>\n'
                '    <DSP>Microsoft.Data.Tools.Schema.Sql.SqlDbFabricDatabaseSchemaProvider</DSP>\n'
                '    <ModelCollation>1033, CI</ModelCollation>\n'
                '  </PropertyGroup>\n'
                '  <Target Name="BeforeBuild">\n'
                '    <Delete Files="$(BaseIntermediateOutputPath)\\project.assets.json" />\n'
                '  </Target>\n'
                '</Project>\n'
            )
            (item_dir / f"{safe_name}.sqlproj").write_text(sqlproj, encoding="utf-8")

        elif cicd_type == "UserDataFunction":
            (item_dir / "function_app.py").write_text(
                'from fabric_user_data_functions import udf\n\n@udf.function()\ndef hello():\n    return "Hello"\n',
                encoding="utf-8"
            )
            (item_dir / "definition.json").write_text(json.dumps({"connections": [], "libraries": []}, indent=2), encoding="utf-8")
            res_dir = item_dir / ".resources"
            res_dir.mkdir(exist_ok=True)
            (res_dir / "functions.json").write_text(json.dumps({"functions": []}, indent=2), encoding="utf-8")

        elif cicd_type == "MirroredDatabase":
            # From sample: MirroredDatabase_1.MirroredDatabase
            mirroring = {"properties": {"source": {"type": "GenericMirror", "typeProperties": None}, "target": {"type": "MountedRelationalDatabase", "typeProperties": {"format": "Delta", "defaultSchema": "dbo"}}}}
            (item_dir / "mirroring.json").write_text(json.dumps(mirroring, indent=2), encoding="utf-8")

        elif cicd_type == "ApacheAirflowJob":
            # From sample: sample apache airflow job.ApacheAirflowJob
            airflow = {"properties": {"type": "Airflow", "typeProperties": {"airflowProperties": {"airflowVersion": "2.10.5", "pythonVersion": "3.12", "airflowEnvironment": "FabricAirflowJob-1.0.0", "airflowRequirements": [], "enableAADIntegration": True, "enableTriggerers": False, "airflowConfigurationOverrides": {}, "environmentVariables": {}, "packageProviderPath": "plugins"}, "computeProperties": {"computePool": "StarterPool", "computeSize": "Small", "enableAutoscale": False, "enableAvailabilityZones": False, "extraNodes": 0}}}}
            (item_dir / "apacheairflowjob-content.json").write_text(json.dumps(airflow, indent=2), encoding="utf-8")
            dags_dir = item_dir / "dags"
            dags_dir.mkdir(exist_ok=True)
            dag_content = 'from datetime import datetime\nfrom airflow import DAG\nfrom airflow.operators.bash import BashOperator\n\ndefault_args = {"owner": "airflow", "depends_on_past": False, "start_date": datetime(2023, 5, 1)}\n\nwith DAG("dag1", default_args=default_args, schedule_interval=None, catchup=False) as dag:\n    hello = BashOperator(task_id="hello", bash_command=\'echo "Hello"\')\n    hello\n'
            (dags_dir / "dag1.py").write_text(dag_content, encoding="utf-8")

    print(f"✅ {ws_dir}/ ({len([i for i in data.items if i.name])} items)")

    # Generate parameter.yml inside workspace directory with actual item references
    param_lines = [
        f"# Parameter file for {args.project}",
        f"# Task flow: {data.task_flow}",
        f"# Ref: https://microsoft.github.io/fabric-cicd/latest/how_to/parameterization/",
        "",
        "find_replace:",
    ]

    # Generate find_replace entries for cross-item references
    # Uses $items.Type.Name.id for dynamic resolution per environment
    for item in data.items:
        if not item.name:
            continue
        safe_name = _cli_safe_name(item.name)
        cicd_type = _cicd_type(item.type)
        if not cicd_type:
            continue

        # Workspace ID replacement — Notebooks reference lakehouse/environment workspace IDs
        if cicd_type in ("Notebook",):
            param_lines += [
                f"  # {safe_name} — default lakehouse workspace ID",
                f'  - find_value: "00000000-0000-0000-0000-000000000000"',
                f"    replace_value:",
                f'      dev: "$workspace.id"',
                f'      ppe: "$workspace.id"',
                f'      prod: "$workspace.id"',
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

        # Find dependencies and create replacement rules
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
                f"    replace_value:",
                f'      dev: "$items.{dep_cicd}.{dep_safe}.id"',
                f'      ppe: "$items.{dep_cicd}.{dep_safe}.id"',
                f'      prod: "$items.{dep_cicd}.{dep_safe}.id"',
                f'    item_name: "{safe_name}"',
                "",
            ]

    param_content = "\n".join(param_lines) + "\n"
    param_path = ws_dir / "parameter.yml"
    param_path.write_text(param_content, encoding="utf-8")

    # 2. Generate config.yml
    ws_desc = f"{args.project} — {data.task_flow} architecture"
    if data.summary:
        ws_desc += f". {data.summary}"

    config_content = _gen_config_yml(data, args.project, ws_desc)
    config_path = out / "config.yml"
    config_path.write_text(config_content, encoding="utf-8")
    print(f"✅ {config_path}")

    # 3. Generate thin deploy script
    deploy_content = _gen_deploy_script(args.project, data)
    deploy_path = out / f"deploy-{slug}.py"
    deploy_path.write_text(deploy_content, encoding="utf-8")
    print(f"✅ {deploy_path}")

    # 4. Generate descriptions JSON
    desc_data = {
        "project": args.project,
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
            "description": item.purpose or f"{item.type} for {args.project}",
            "folder": _get_folder_for_item(item.type) or "root",
        }
    desc_path = out / f"descriptions-{slug}.json"
    desc_path.write_text(json.dumps(desc_data, indent=2, ensure_ascii=False), encoding="utf-8")
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


if __name__ == "__main__":
    main()
