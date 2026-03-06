"""
Item Type Registry loader.

All scripts that need item type metadata MUST import from here instead of
maintaining their own dictionaries. The single source of truth is
_shared/item-type-registry.json.

Usage:
    from registry_loader import load_registry, build_fab_commands, build_phase_map, ...
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "_shared" / "item-type-registry.json"

_cache: dict | None = None


def load_registry() -> dict[str, dict]:
    """Load the item type registry. Returns the 'types' dict. Cached after first call."""
    global _cache
    if _cache is None:
        with open(REGISTRY_PATH, encoding="utf-8") as f:
            _cache = json.load(f)["types"]
    return _cache


def build_fab_commands() -> dict[str, tuple[str, list[str]] | None]:
    """Build the FAB_COMMANDS dict for deploy-script-gen.py.

    Returns a dict mapping lowercase alias → (path_template, extra_args) or None
    if the item can't be created via fab mkdir.
    """
    registry = load_registry()
    result: dict[str, tuple[str, list[str]] | None] = {}

    for canonical, data in registry.items():
        fab_type = data["fab_type"]
        mkdir_supported = data.get("mkdir_supported", False)

        if mkdir_supported:
            path_template = "{ws}.Workspace/{name}." + fab_type
            args = list(data.get("mkdir_args", []))
            value = (path_template, args)
        else:
            value = None

        # Add canonical lowercase
        result[canonical.lower()] = value
        # Add all aliases
        for alias in data.get("aliases", []):
            result[alias.lower()] = value

    return result


def build_display_names() -> dict[str, str]:
    """Build the DISPLAY_NAMES dict for deploy-script-gen.py.

    Returns a dict mapping lowercase alias → display name.
    """
    registry = load_registry()
    result: dict[str, str] = {}

    for canonical, data in registry.items():
        display = data["display_name"]
        result[canonical.lower()] = display
        for alias in data.get("aliases", []):
            result[alias.lower()] = display

    return result


def build_phase_map() -> dict[str, tuple[str, int]]:
    """Build the PHASE_MAP dict for test-plan-prefill.py.

    Returns a dict mapping type name variants → (phase_name, phase_order).
    """
    registry = load_registry()
    result: dict[str, tuple[str, int]] = {}

    for canonical, data in registry.items():
        phase = data["phase"]
        order = data["phase_order"]
        if phase == "TBD":
            continue
        value = (phase, order)
        result[canonical] = value
        result[data["fab_type"]] = value
        result[data["display_name"]] = value
        for alias in data.get("aliases", []):
            # Use title-case aliases for matching against handoff text
            result[alias] = value
            # Also add common forms
            parts = alias.split()
            if len(parts) > 1:
                result[" ".join(w.capitalize() for w in parts)] = value

    return result


def build_task_type_map() -> dict[str, str]:
    """Build the ITEM_TO_TASK_TYPE dict for taskflow-gen.py.

    Returns a dict mapping type name variants → Fabric task type string.
    """
    registry = load_registry()
    result: dict[str, str] = {}

    for canonical, data in registry.items():
        task_type = data.get("task_type", "")
        if not task_type or task_type == "TBD":
            continue
        result[canonical] = task_type
        result[data["fab_type"]] = task_type
        result[data["display_name"]] = task_type
        for alias in data.get("aliases", []):
            result[alias] = task_type
            parts = alias.split()
            if len(parts) > 1:
                result[" ".join(w.capitalize() for w in parts)] = task_type

    return result


def build_portal_only_items() -> dict[str, str]:
    """Build the PORTAL_ONLY_ITEMS dict for review-prescan.py.

    Returns a dict mapping lowercase name → fab_type for items that can't use fab mkdir.
    """
    registry = load_registry()
    result: dict[str, str] = {}

    for canonical, data in registry.items():
        if not data.get("mkdir_supported", False):
            result[canonical.lower()] = data["fab_type"]
            result[data["display_name"].lower()] = data["fab_type"]
            for alias in data.get("aliases", []):
                result[alias.lower()] = data["fab_type"]

    return result


def build_fab_type_map() -> dict[str, str]:
    """Build the FAB_TYPE_MAP dict for handoff-scaffolder.py.

    Returns a dict mapping display name variants → fab_type.
    """
    registry = load_registry()
    result: dict[str, str] = {}

    for canonical, data in registry.items():
        fab_type = data["fab_type"]
        result[canonical] = fab_type
        result[data["display_name"]] = fab_type
        for alias in data.get("aliases", []):
            parts = alias.split()
            if len(parts) > 1:
                result[" ".join(w.capitalize() for w in parts)] = fab_type

    return result


def build_ps1_fab_types() -> dict[str, str]:
    """Build the $FabTypes hashtable content for validate-items.ps1.

    Returns a dict mapping fab_type → fab_type for types where CLI is supported.
    """
    registry = load_registry()
    result: dict[str, str] = {}

    for canonical, data in registry.items():
        if data.get("cli_supported", False):
            result[data["fab_type"]] = data["fab_type"]

    return result


def build_ps1_portal_only() -> list[str]:
    """Build the $PortalOnly array content for validate-items.ps1.

    Returns a list of fab_type values for portal-only items.
    """
    registry = load_registry()
    return sorted({
        data["fab_type"]
        for data in registry.values()
        if not data.get("mkdir_supported", False)
    })
