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
REGISTRY_PATH = Path(__file__).resolve().parent / "item-type-registry.json"

_cache: dict | None = None


def load_registry() -> dict[str, dict]:
    """Load the item type registry. Returns the 'types' dict. Cached after first call."""
    global _cache
    if _cache is None:
        with open(REGISTRY_PATH, encoding="utf-8") as f:
            _cache = json.load(f)["types"]
    return _cache


def build_fab_commands() -> dict[str, bool]:
    """Build a REST API creation-support map for deploy-script-gen.py.

    Returns a dict mapping lowercase alias → True (REST API creatable) or False
    (portal-only, no programmatic creation).

    .. deprecated:: The name ``build_fab_commands`` is kept for backward
       compatibility. This now returns REST API creatability flags.
    """
    registry = load_registry()
    result: dict[str, bool] = {}

    for canonical, data in registry.items():
        creatable = data.get("rest_api", {}).get("creatable", False)

        result[canonical.lower()] = creatable
        for alias in data.get("aliases", []):
            result[alias.lower()] = creatable

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

    Returns a dict mapping lowercase name → fab_type for items that cannot
    be created via the Fabric REST API.
    """
    registry = load_registry()
    result: dict[str, str] = {}

    for canonical, data in registry.items():
        if not data.get("rest_api", {}).get("creatable", False):
            result[canonical.lower()] = data["fab_type"]
            result[data["display_name"].lower()] = data["fab_type"]
            for alias in data.get("aliases", []):
                result[alias.lower()] = data["fab_type"]

    return result


def build_api_creatable_items() -> set[str]:
    """Return the set of fab_type values that are creatable via the Fabric REST API.

    Uses the ``rest_api.creatable`` field added to each type record.
    Agents and scripts can call this instead of scanning the flat
    ``cicd_supported_types`` array.
    """
    registry = load_registry()
    return {
        data["fab_type"]
        for data in registry.values()
        if data.get("rest_api", {}).get("creatable", False)
    }


def build_api_name_remap() -> dict[str, str]:
    """Return a mapping of fab_type → REST API name where they differ.

    Derived from ``rest_api.api_name`` fields so the root-level
    ``cicd_type_remap`` dict can be deprecated.
    """
    registry = load_registry()
    return {
        data["fab_type"]: data["rest_api"]["api_name"]
        for data in registry.values()
        if "api_name" in data.get("rest_api", {})
    }


def build_availability_map() -> dict[str, str]:
    """Build a mapping of type name variants → availability status ('ga' or 'preview').

    Returns a dict mapping canonical name, fab_type, display name, and aliases
    to the availability string for that item type.
    """
    registry = load_registry()
    result: dict[str, str] = {}

    for canonical, data in registry.items():
        status = data.get("availability", "ga")
        result[canonical] = status
        result[data["fab_type"]] = status
        result[data["display_name"]] = status
        for alias in data.get("aliases", []):
            result[alias] = status
            parts = alias.split()
            if len(parts) > 1:
                result[" ".join(w.capitalize() for w in parts)] = status

    return result


def build_fab_type_map() -> dict[str, str]:
    """Build the FAB_TYPE_MAP dict for handoff-scaffolder.py and deploy-script-gen.py.

    Returns a dict mapping display name variants → fab_type.
    Maps canonical key, display_name, fab_type, and ALL aliases (including
    single-word and case variants) so that any string an LLM might put in an
    architecture handoff resolves to the correct fab_type.
    """
    registry = load_registry()
    result: dict[str, str] = {}

    for canonical, data in registry.items():
        fab_type = data["fab_type"]
        result[canonical] = fab_type
        result[fab_type] = fab_type  # identity mapping for fab_type itself
        result[data["display_name"]] = fab_type
        for alias in data.get("aliases", []):
            result[alias] = fab_type
            # Also add title-cased and capitalized forms
            result[alias.title()] = fab_type
            parts = alias.split()
            if len(parts) > 1:
                result[" ".join(w.capitalize() for w in parts)] = fab_type

    return result


def build_cicd_type_set() -> set[str]:
    """Return the set of fab_type values deployable via fabric-cicd.

    Derived from the ``cicd.strategy`` field in the registry. Types with
    strategy ``platform_only`` or ``content`` are supported by fabric-cicd.
    This replaces the hardcoded ``_FABRIC_CICD_TYPES`` set in deploy-script-gen.py.
    """
    registry = load_registry()
    return {
        data["fab_type"]
        for data in registry.values()
        if data.get("cicd", {}).get("strategy") in ("platform_only", "content")
    }


def build_type_remap() -> dict[str, str]:
    """Return a mapping of display_name → fab_type where they differ.

    This replaces the hardcoded ``_TYPE_REMAP`` dict in deploy-script-gen.py.
    Includes all aliases and display names that don't match fab_type, so
    any LLM-generated item type string resolves correctly.
    """
    registry = load_registry()
    result: dict[str, str] = {}

    for _canonical, data in registry.items():
        fab_type = data["fab_type"]
        display = data["display_name"]
        if display != fab_type:
            result[display] = fab_type
        for alias in data.get("aliases", []):
            titled = alias.title()
            if titled != fab_type:
                result[titled] = fab_type
            if alias != fab_type.lower():
                result[alias] = fab_type

    return result
