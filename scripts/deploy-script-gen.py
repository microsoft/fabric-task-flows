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
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

SHARED_DIR = Path(__file__).resolve().parent.parent / "_shared"

# ─────────────────────────────────────────────────────────────────────────────
# Item type → fab command mapping
# ─────────────────────────────────────────────────────────────────────────────

# Item type mappings — loaded from _shared/item-type-registry.json
# Do NOT maintain these dicts manually. See _shared/agent-boundaries.md.
from registry_loader import build_fab_commands, build_display_names

FAB_COMMANDS: dict[str, tuple[str, list[str]] | None] = build_fab_commands()
DISPLAY_NAMES: dict[str, str] = build_display_names()

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

    return HandoffData(task_flow=task_flow, items=items, waves=waves)


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
    # Also check the original with spaces for types like "Real-Time Dashboard"
    return FAB_COMMANDS.get(key) is None and FAB_COMMANDS.get(item_type.lower()) is None


def _get_fab_command(item: Item) -> tuple[str, list[str]] | None:
    """Return (path_template, extra_args) for an item, or None if portal-only."""
    key = _type_key(item.type)
    entry = FAB_COMMANDS.get(key)
    if entry is None:
        entry = FAB_COMMANDS.get(item.type.lower())
    if entry is not None:
        path_tpl, extra_args = entry
        return (path_tpl.replace("{name}", item.name), extra_args)
    return None


def _get_display_type(item_type: str) -> str:
    key = _type_key(item_type)
    return DISPLAY_NAMES.get(key, DISPLAY_NAMES.get(item_type.lower(), item_type))


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


def _build_item_lookup(data: HandoffData) -> dict[str, Item]:
    lookup: dict[str, Item] = {}
    for item in data.items:
        lookup[item.name] = item
        lookup[str(item.id)] = item
    return lookup


def _tree_connector(idx: int, total: int) -> str:
    return "└──" if idx == total - 1 else "├──"


def _find_dependency_items(item: Item, all_items: list[Item], target_types: set[str]) -> list[Item]:
    """Find items in depends_on list matching target types."""
    items_by_id = {i.id: i for i in all_items}
    matches = []
    for dep_id in item.depends_on:
        dep = items_by_id.get(dep_id)
        if dep and _type_key(dep.type) in target_types:
            matches.append(dep)
    return matches


def _gen_post_wave_ps1(wave_items: list[Item], all_items: list[Item], ws_var: str) -> list[str]:
    """Generate post-wave PowerShell code for Environment wait, notebook binding, etc."""
    lines: list[str] = []

    # Environment publish wait
    env_items = [i for i in wave_items if _type_key(i.type) in _ENV_TYPES]
    for env in env_items:
        lines.append("")
        lines.append(f'  Write-Host "  ⏳ Waiting for Environment publish (may take 20+ min)..."')
        lines.append(f'  $maxWait = 1800; $elapsed = 0')
        lines.append(f'  do {{')
        lines.append(f'    Start-Sleep -Seconds 30; $elapsed += 30')
        lines.append(f'    $envStatus = (fab get "{ws_var}.Workspace/{env.name}.Environment" -q properties.publishStatus 2>&1)')
        lines.append(f'    Write-Host "    ⏱  $([math]::Floor($elapsed/60))m elapsed — status: $envStatus"')
        lines.append(f'  }} while ($envStatus -ne "Published" -and $elapsed -lt $maxWait)')
        lines.append(f'  if ($envStatus -ne "Published") {{')
        lines.append(f'    Write-Host "  ⚠️  Environment publish timed out — notebooks may fail until publish completes"')
        lines.append(f'  }} else {{')
        lines.append(f'    Write-Host "  ── ✅ Environment published"')
        lines.append(f'  }}')

    # Notebook binding (fab set for lakehouse + environment)
    nb_items = [i for i in wave_items if _type_key(i.type) in _NOTEBOOK_TYPES]
    for nb in nb_items:
        lakehouses = _find_dependency_items(nb, all_items, {"lakehouse"})
        envs = _find_dependency_items(nb, all_items, _ENV_TYPES)
        if lakehouses or envs:
            lines.append("")
            lines.append(f'  # Bind {nb.name} to dependencies')
        if lakehouses:
            lh = lakehouses[0]
            lines.append(f'  $lhId = (fab get "{ws_var}.Workspace/{lh.name}.Lakehouse" -q id 2>&1).Trim()')
            lines.append(f'  fab set "{ws_var}.Workspace/{nb.name}.Notebook" -q lakehouse -i "$lhId" 2>&1 | Out-Null')
            lines.append(f'  Write-Host "  ── ✅ {nb.name} bound to lakehouse {lh.name}"')
        if envs:
            env = envs[0]
            lines.append(f'  $envId = (fab get "{ws_var}.Workspace/{env.name}.Environment" -q id 2>&1).Trim()')
            lines.append(f'  fab set "{ws_var}.Workspace/{nb.name}.Notebook" -q environment -i "$envId" 2>&1 | Out-Null')
            lines.append(f'  Write-Host "  ── ✅ {nb.name} bound to environment {env.name}"')

    # Semantic Model ID capture (for later Report binding)
    sm_items = [i for i in wave_items if _type_key(i.type) in _SEMANTIC_MODEL_TYPES]
    for sm in sm_items:
        lines.append("")
        lines.append(f'  $SemanticModelId = (fab get "{ws_var}.Workspace/{sm.name}.SemanticModel" -q id 2>&1).Trim()')
        lines.append(f'  Write-Host "  ── ℹ️  Captured SemanticModel ID: $SemanticModelId"')

    # Eventhouse ID capture (for later KQLDatabase binding)
    eh_items = [i for i in wave_items if _type_key(i.type) == "eventhouse"]
    for eh in eh_items:
        lines.append("")
        lines.append(f'  $EventhouseId = (fab get "{ws_var}.Workspace/{eh.name}.Eventhouse" -q id 2>&1).Trim()')
        lines.append(f'  Write-Host "  ── ℹ️  Captured Eventhouse ID: $EventhouseId"')

    return lines


def _gen_post_wave_bash(wave_items: list[Item], all_items: list[Item], ws_var: str) -> list[str]:
    """Generate post-wave bash code for Environment wait, notebook binding, etc."""
    lines: list[str] = []

    # Environment publish wait
    env_items = [i for i in wave_items if _type_key(i.type) in _ENV_TYPES]
    for env in env_items:
        lines.append("")
        lines.append(f'  echo "  ⏳ Waiting for Environment publish (may take 20+ min)..."')
        lines.append(f'  max_wait=1800; elapsed=0')
        lines.append(f'  while [ $elapsed -lt $max_wait ]; do')
        lines.append(f'    sleep 30; elapsed=$((elapsed + 30))')
        lines.append(f'    env_status=$(fab get "{ws_var}.Workspace/{env.name}.Environment" -q properties.publishStatus 2>&1)')
        lines.append(f'    echo "    ⏱  $((elapsed / 60))m elapsed — status: $env_status"')
        lines.append(f'    [ "$env_status" = "Published" ] && break')
        lines.append(f'  done')
        lines.append(f'  if [ "$env_status" != "Published" ]; then')
        lines.append(f'    echo "  ⚠️  Environment publish timed out — notebooks may fail until publish completes"')
        lines.append(f'  else')
        lines.append(f'    echo "  ── ✅ Environment published"')
        lines.append(f'  fi')

    # Notebook binding
    nb_items = [i for i in wave_items if _type_key(i.type) in _NOTEBOOK_TYPES]
    for nb in nb_items:
        lakehouses = _find_dependency_items(nb, all_items, {"lakehouse"})
        envs = _find_dependency_items(nb, all_items, _ENV_TYPES)
        if lakehouses or envs:
            lines.append("")
            lines.append(f'  # Bind {nb.name} to dependencies')
        if lakehouses:
            lh = lakehouses[0]
            lines.append(f'  lh_id=$(fab get "{ws_var}.Workspace/{lh.name}.Lakehouse" -q id 2>&1 | tr -d "[:space:]")')
            lines.append(f'  fab set "{ws_var}.Workspace/{nb.name}.Notebook" -q lakehouse -i "$lh_id" 2>&1 | cat > /dev/null')
            lines.append(f'  echo "  ── ✅ {nb.name} bound to lakehouse {lh.name}"')
        if envs:
            env = envs[0]
            lines.append(f'  env_id=$(fab get "{ws_var}.Workspace/{env.name}.Environment" -q id 2>&1 | tr -d "[:space:]")')
            lines.append(f'  fab set "{ws_var}.Workspace/{nb.name}.Notebook" -q environment -i "$env_id" 2>&1 | cat > /dev/null')
            lines.append(f'  echo "  ── ✅ {nb.name} bound to environment {env.name}"')

    # Semantic Model ID capture
    sm_items = [i for i in wave_items if _type_key(i.type) in _SEMANTIC_MODEL_TYPES]
    for sm in sm_items:
        lines.append("")
        lines.append(f'  SEMANTIC_MODEL_ID=$(fab get "{ws_var}.Workspace/{sm.name}.SemanticModel" -q id 2>&1 | tr -d "[:space:]")')
        lines.append(f'  echo "  ── ℹ️  Captured SemanticModel ID: $SEMANTIC_MODEL_ID"')

    # Eventhouse ID capture (for later KQLDatabase binding)
    eh_items = [i for i in wave_items if _type_key(i.type) == "eventhouse"]
    for eh in eh_items:
        lines.append("")
        lines.append(f'  EVENTHOUSE_ID=$(fab get "{ws_var}.Workspace/{eh.name}.Eventhouse" -q id 2>&1 | tr -d "[:space:]")')
        lines.append(f'  echo "  ── ℹ️  Captured Eventhouse ID: $EVENTHOUSE_ID"')

    return lines


def _gen_wave_deployment_bash(data: HandoffData) -> str:
    lines: list[str] = []
    item_lookup = _build_item_lookup(data)
    sm_captured = False  # Track if SemanticModel ID has been captured

    for wave in data.waves:
        wave_items = [item_lookup[str(iid)] for iid in wave.items if str(iid) in item_lookup]
        if not wave_items:
            continue

        note = wave.note or f"Wave {wave.id}"
        lines.append(f"  # ─────────────────────────────────────────────────────────────────")
        lines.append(f"  # Wave {wave.id} — {note}")
        lines.append(f"  # ─────────────────────────────────────────────────────────────────")
        lines.append(f'  echo ""')
        lines.append(f'  echo "  Wave {wave.id} — {note}"')

        for idx, item in enumerate(wave_items):
            connector = _tree_connector(idx, len(wave_items))
            display_type = _get_display_type(item.type)
            fab_result = _get_fab_command(item)

            if fab_result is not None:
                path_tpl, extra_args = fab_result
                bash_path = path_tpl.replace("{ws}", "$FABRIC_WORKSPACE_NAME")
                # Inject SemanticModel ID for Report items
                if _type_key(item.type) == "report" and sm_captured:
                    extra_args = list(extra_args) + ["-P", "semanticModelId=$SEMANTIC_MODEL_ID"]
                # Inject Eventhouse ID for KQLDatabase items
                if _type_key(item.type) == "kqldatabase":
                    extra_args = list(extra_args) + ["-P", "eventhouseId=$EVENTHOUSE_ID"]
                extra_str = " " + " ".join(f'"{a}"' for a in extra_args) if extra_args else ""
                lines.append(
                    f'  fab_mkdir "{bash_path}" "{display_type}: {item.name}" "{connector}"{extra_str}'
                )
            else:
                lines.append(f'  echo "  {connector} ⏭️  [MANUAL] {display_type}: create via Fabric Portal"')

        # Post-wave logic (environment wait, notebook binding, ID capture)
        post_lines = _gen_post_wave_bash(wave_items, data.items, "$FABRIC_WORKSPACE_NAME")
        if post_lines:
            lines.extend(post_lines)
        # Track if SemanticModel ID was captured in this wave
        if any(_type_key(i.type) in _SEMANTIC_MODEL_TYPES for i in wave_items):
            sm_captured = True

        lines.append("")

    return "\n".join(lines)


def _gen_wave_deployment_ps1(data: HandoffData) -> str:
    lines: list[str] = []
    item_lookup = _build_item_lookup(data)
    sm_captured = False  # Track if SemanticModel ID has been captured

    for wave in data.waves:
        wave_items = [item_lookup[str(iid)] for iid in wave.items if str(iid) in item_lookup]
        if not wave_items:
            continue

        note = wave.note or f"Wave {wave.id}"
        lines.append(f"  # ─────────────────────────────────────────────────────────────────")
        lines.append(f"  # Wave {wave.id} — {note}")
        lines.append(f"  # ─────────────────────────────────────────────────────────────────")
        lines.append(f'  Write-Host ""')
        lines.append(f'  Write-Host "  Wave {wave.id} — {note}"')

        for idx, item in enumerate(wave_items):
            connector = _tree_connector(idx, len(wave_items))
            display_type = _get_display_type(item.type)
            fab_result = _get_fab_command(item)

            if fab_result is not None:
                path_tpl, extra_args = fab_result
                ps_path = path_tpl.replace("{ws}", "$WorkspaceName")
                # Inject SemanticModel ID for Report items
                if _type_key(item.type) == "report" and sm_captured:
                    extra_args = list(extra_args) + ["-P", "semanticModelId=$SemanticModelId"]
                # Inject Eventhouse ID for KQLDatabase items
                if _type_key(item.type) == "kqldatabase":
                    extra_args = list(extra_args) + ["-P", "eventhouseId=$EventhouseId"]
                extra_str = ""
                if extra_args:
                    args_joined = ", ".join(f'"{a}"' for a in extra_args)
                    extra_str = f" -ExtraArgs @({args_joined})"
                lines.append(
                    f'  Fab-Mkdir -Path "{ps_path}" -Label "{display_type}: {item.name}" -TreeChar "{connector}"{extra_str}'
                )
            else:
                lines.append(f'  Write-Host "  {connector} ⏭️  [MANUAL] {display_type}: create via Fabric Portal"')

        # Post-wave logic (environment wait, notebook binding, ID capture)
        post_lines = _gen_post_wave_ps1(wave_items, data.items, "$WorkspaceName")
        if post_lines:
            lines.extend(post_lines)
        # Track if SemanticModel ID was captured in this wave
        if any(_type_key(i.type) in _SEMANTIC_MODEL_TYPES for i in wave_items):
            sm_captured = True

        lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Code generation: deployment plan preview
# ─────────────────────────────────────────────────────────────────────────────

def _gen_plan_preview_bash(data: HandoffData) -> str:
    lines: list[str] = []
    item_lookup = _build_item_lookup(data)

    for wave in data.waves:
        wave_items = [item_lookup[str(iid)] for iid in wave.items if str(iid) in item_lookup]
        if not wave_items:
            continue

        note = wave.note or f"Wave {wave.id}"
        lines.append(f'  echo "  Wave {wave.id} — {note}"')

        for idx, item in enumerate(wave_items):
            connector = _tree_connector(idx, len(wave_items))
            display_type = _get_display_type(item.type)
            if _is_portal_only(item.type):
                lines.append(f'  echo "  {connector} ☐ [MANUAL] {display_type}: {item.name}"')
            else:
                lines.append(f'  echo "  {connector} ☐ {display_type}: {item.name}"')

        lines.append(f'  echo ""')

    return "\n".join(lines)


def _gen_plan_preview_ps1(data: HandoffData) -> str:
    lines: list[str] = []
    item_lookup = _build_item_lookup(data)

    for wave in data.waves:
        wave_items = [item_lookup[str(iid)] for iid in wave.items if str(iid) in item_lookup]
        if not wave_items:
            continue

        note = wave.note or f"Wave {wave.id}"
        lines.append(f'  Write-Host "  Wave {wave.id} — {note}"')

        for idx, item in enumerate(wave_items):
            connector = _tree_connector(idx, len(wave_items))
            display_type = _get_display_type(item.type)
            if _is_portal_only(item.type):
                lines.append(f'  Write-Host "  {connector} ☐ [MANUAL] {display_type}: {item.name}"')
            else:
                lines.append(f'  Write-Host "  {connector} ☐ {display_type}: {item.name}"')

        lines.append(f'  Write-Host ""')

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Code generation: task-flow-specific prompts
# ─────────────────────────────────────────────────────────────────────────────

def _gen_tf_prompts_bash(task_flow: str) -> str:
    prompts = TASK_FLOW_PROMPTS.get(task_flow, [])
    if not prompts:
        return ""

    lines: list[str] = []
    for env_var, prompt_text, default, desc, optional in prompts:
        # Show description as a comment before the prompt
        if desc:
            lines.append(f'  # {desc}')
        if default:
            lines.append(f'  {env_var}=$(prompt_value "{env_var}" "{prompt_text}" "{default}")')
        elif optional:
            lines.append(f'  {env_var}=$(prompt_value "{env_var}" "{prompt_text}" "" "optional")')
        else:
            lines.append(f'  {env_var}=$(prompt_value "{env_var}" "{prompt_text}")')
    return "\n".join(lines)


def _gen_tf_prompts_ps1(task_flow: str) -> str:
    prompts = TASK_FLOW_PROMPTS.get(task_flow, [])
    if not prompts:
        return ""

    lines: list[str] = []
    for env_var, prompt_text, default, desc, optional in prompts:
        # Convert ENV_VAR to $PascalCase
        ps_var = "".join(w.capitalize() for w in env_var.lower().split("_"))
        # Show description as a comment before the prompt
        if desc:
            lines.append(f'  # {desc}')
        if default:
            lines.append(
                f'  ${ps_var} = Prompt-Value -EnvVarName "{env_var}" '
                f'-PromptText "{prompt_text}" -DefaultValue "{default}"'
            )
        elif optional:
            lines.append(
                f'  ${ps_var} = Prompt-Value -EnvVarName "{env_var}" '
                f'-PromptText "{prompt_text}" -Optional'
            )
        else:
            lines.append(
                f'  ${ps_var} = Prompt-Value -EnvVarName "{env_var}" '
                f'-PromptText "{prompt_text}"'
            )
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Code generation: OR alternatives
# ─────────────────────────────────────────────────────────────────────────────

def _gen_or_comment_bash(data: HandoffData) -> str:
    """Generate commented-out alternative blocks for ──OR── items."""
    or_pairs = _has_or_alternatives(data)
    if not or_pairs:
        return ""

    lines: list[str] = [
        "  # ─────────────────────────────────────────────────────────────────",
        "  # ──OR── Alternatives: uncomment ONE option per group",
        "  # ─────────────────────────────────────────────────────────────────",
    ]
    for primary, alt in or_pairs:
        display_a = _get_display_type(primary.type)
        display_b = _get_display_type(alt.type)
        result_a = _get_fab_command(primary)
        result_b = _get_fab_command(alt)
        lines.append(f"  # Option A: {display_a} — {primary.name}")
        if result_a:
            path_a, args_a = result_a
            bash_path_a = path_a.replace("{ws}", "$FABRIC_WORKSPACE_NAME")
            extra_a = " " + " ".join(args_a) if args_a else ""
            lines.append(f'  # fab mkdir "{bash_path_a}"{extra_a}')
        lines.append(f"  # Option B: {display_b} — {alt.name}")
        if result_b:
            path_b, args_b = result_b
            bash_path_b = path_b.replace("{ws}", "$FABRIC_WORKSPACE_NAME")
            extra_b = " " + " ".join(args_b) if args_b else ""
            lines.append(f'  # fab mkdir "{bash_path_b}"{extra_b}')
        lines.append("")

    return "\n".join(lines)


def _gen_or_comment_ps1(data: HandoffData) -> str:
    or_pairs = _has_or_alternatives(data)
    if not or_pairs:
        return ""

    lines: list[str] = [
        "  # ─────────────────────────────────────────────────────────────────",
        "  # ──OR── Alternatives: uncomment ONE option per group",
        "  # ─────────────────────────────────────────────────────────────────",
    ]
    for primary, alt in or_pairs:
        display_a = _get_display_type(primary.type)
        display_b = _get_display_type(alt.type)
        result_a = _get_fab_command(primary)
        result_b = _get_fab_command(alt)
        lines.append(f"  # Option A: {display_a} — {primary.name}")
        if result_a:
            path_a, args_a = result_a
            ps_path_a = path_a.replace("{ws}", "$WorkspaceName")
            extra_a = " " + " ".join(args_a) if args_a else ""
            lines.append(f'  # fab mkdir "{ps_path_a}"{extra_a}')
        lines.append(f"  # Option B: {display_b} — {alt.name}")
        if result_b:
            path_b, args_b = result_b
            ps_path_b = path_b.replace("{ws}", "$WorkspaceName")
            extra_b = " " + " ".join(args_b) if args_b else ""
            lines.append(f'  # fab mkdir "{ps_path_b}"{extra_b}')
        lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Template filling
# ─────────────────────────────────────────────────────────────────────────────

def _fill_template(
    template: str,
    project: str,
    data: HandoffData,
    wave_deployment: str,
    plan_preview: str,
    tf_prompts: str,
    or_comments: str,
) -> str:
    slug = _slugify(project)
    gen_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    result = template
    result = result.replace("{{PROJECT_NAME}}", project)
    result = result.replace("{{TASK_FLOW}}", data.task_flow)
    result = result.replace("{{DATE}}", gen_date)
    result = result.replace("{{PROJECT_SLUG}}", slug)
    result = result.replace("{{ITEM_COUNT}}", str(len(data.items)))
    result = result.replace("{{WAVE_COUNT}}", str(len(data.waves)))

    # Replace WAVE_DEPLOYMENT placeholder block
    wave_marker_patterns = [
        (r"  # \{\{WAVE_DEPLOYMENT\}\}\n(?:  # Agent:.*\n)*(?:  #\n)*(?:  #   .*\n)*", wave_deployment + "\n"),
    ]
    for pat, repl in wave_marker_patterns:
        result = re.sub(pat, repl, result)

    # Replace DEPLOYMENT_PLAN_PREVIEW placeholder block
    plan_marker_patterns = [
        (r"  # \{\{DEPLOYMENT_PLAN_PREVIEW\}\}\n(?:  # Agent:.*\n)*(?:  #   .*\n)*(?:  #\n)*", plan_preview + "\n"),
    ]
    for pat, repl in plan_marker_patterns:
        result = re.sub(pat, repl, result)

    # Replace TASK_FLOW_SPECIFIC_PROMPTS placeholder block
    if tf_prompts:
        tf_marker_patterns = [
            (r"  # \{\{TASK_FLOW_SPECIFIC_PROMPTS\}\}\n(?:  # Agent:.*\n)*", tf_prompts + "\n"),
        ]
    else:
        tf_marker_patterns = [
            (r"  # \{\{TASK_FLOW_SPECIFIC_PROMPTS\}\}\n(?:  # Agent:.*\n)*", ""),
        ]
    for pat, repl in tf_marker_patterns:
        result = re.sub(pat, repl, result)

    # Append OR comments before the DEPLOYMENT SUMMARY box if present
    if or_comments:
        result = result.replace(
            '  echo ""\n  echo "┌──────────────────────────────────────────────────────────────────┐"\n  echo "│  DEPLOYMENT SUMMARY',
            or_comments + '\n  echo ""\n  echo "┌──────────────────────────────────────────────────────────────────┐"\n  echo "│  DEPLOYMENT SUMMARY',
        )
        result = result.replace(
            '  Write-Host ""\n  Write-Host "┌──────────────────────────────────────────────────────────────────┐"\n  Write-Host "│  DEPLOYMENT SUMMARY',
            or_comments + '\n  Write-Host ""\n  Write-Host "┌──────────────────────────────────────────────────────────────────┐"\n  Write-Host "│  DEPLOYMENT SUMMARY',
        )

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def generate(handoff_path: str, project: str) -> tuple[str, str]:
    """Generate bash and PowerShell deploy scripts from a handoff file.

    Returns:
        Tuple of (bash_script, powershell_script).
    """
    data = parse_handoff(handoff_path)

    bash_template = (SHARED_DIR / "script-template.sh").read_text(encoding="utf-8")
    ps1_template = (SHARED_DIR / "script-template.ps1").read_text(encoding="utf-8")

    bash_script = _fill_template(
        template=bash_template,
        project=project,
        data=data,
        wave_deployment=_gen_wave_deployment_bash(data),
        plan_preview=_gen_plan_preview_bash(data),
        tf_prompts=_gen_tf_prompts_bash(data.task_flow),
        or_comments=_gen_or_comment_bash(data),
    )

    ps1_script = _fill_template(
        template=ps1_template,
        project=project,
        data=data,
        wave_deployment=_gen_wave_deployment_ps1(data),
        plan_preview=_gen_plan_preview_ps1(data),
        tf_prompts=_gen_tf_prompts_ps1(data.task_flow),
        or_comments=_gen_or_comment_ps1(data),
    )

    return bash_script, ps1_script


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate deployment scripts from architecture handoffs"
    )
    parser.add_argument(
        "--handoff", required=True,
        help="Path to architecture-handoff.md",
    )
    parser.add_argument(
        "--project", required=True,
        help="Project name",
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Directory for output scripts (default: stdout for .sh only)",
    )
    parser.add_argument(
        "--shell", choices=["bash", "powershell", "both"], default="both",
        help="Script type to generate (default: both)",
    )
    args = parser.parse_args()

    bash_script, ps1_script = generate(args.handoff, args.project)

    if args.output_dir:
        out = Path(args.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        slug = _slugify(args.project)

        if args.shell in ("bash", "both"):
            sh_path = out / f"deploy-{slug}.sh"
            sh_path.write_text(bash_script, encoding="utf-8")
            print(f"✅ {sh_path}")

        if args.shell in ("powershell", "both"):
            ps_path = out / f"deploy-{slug}.ps1"
            ps_path.write_text(ps1_script, encoding="utf-8")
            print(f"✅ {ps_path}")
    else:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if args.shell == "powershell":
            sys.stdout.write(ps1_script)
        elif args.shell == "both":
            sys.stdout.write(bash_script)
            sys.stdout.write("\n\n# " + "=" * 77 + "\n")
            sys.stdout.write("# PowerShell version follows\n")
            sys.stdout.write("# " + "=" * 77 + "\n\n")
            sys.stdout.write(ps1_script)
        else:
            sys.stdout.write(bash_script)


if __name__ == "__main__":
    main()
