"""
Item Type Registry loader.

All scripts that need item type metadata MUST import from here instead of
maintaining their own dictionaries.  The single source of truth is
``registry/item-type-registry.json``.

Usage::

    from registry_loader import load_registry, build_fab_type_map, build_phase_map
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

from paths import REPO_ROOT, REGISTRY_DIR

REGISTRY_PATH = REGISTRY_DIR / "item-type-registry.json"

_cache: dict | None = None
_full_cache: dict | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Core loaders
# ─────────────────────────────────────────────────────────────────────────────

def load_registry() -> dict[str, dict]:
    """Load the item type registry.  Returns the ``types`` dict.

    Applies ``$defaults`` (naming, availability) and reconstructs derived
    fields (``fab_type`` defaults to key name, ``rest_api`` from flat booleans,
    auto-generated lowercase alias) so downstream code sees the full shape.

    The result is cached after the first successful call so repeated imports
    across scripts share a single in-memory copy.

    Raises:
        FileNotFoundError: Registry JSON file does not exist.
        ValueError: JSON is malformed or missing the ``types`` key.
    """
    global _cache
    if _cache is None:
        data = _read_registry_file()
        if "types" not in data or not isinstance(data["types"], dict):
            raise ValueError(
                f"Registry at {REGISTRY_PATH} is missing a valid 'types' dict"
            )
        defaults = data.get("$defaults", {})
        types = data["types"]
        for name, item in types.items():
            # Apply naming default
            if "naming" not in item and "naming" in defaults:
                item["naming"] = defaults["naming"].copy()
            # Apply availability default
            if "availability" not in item and "availability" in defaults:
                item["availability"] = defaults["availability"]
            # Default fab_type to key name
            if "fab_type" not in item:
                # Check nested api.fab_type first (v1.0.0 schema)
                if "api" in item and "fab_type" in item["api"]:
                    item["fab_type"] = item["api"]["fab_type"]
                else:
                    item["fab_type"] = name
            # Auto-generate lowercase alias
            auto_alias = name.lower()
            if "aliases" not in item:
                item["aliases"] = [auto_alias]
            elif auto_alias not in item["aliases"]:
                item["aliases"].insert(0, auto_alias)
            # Reconstruct rest_api from api object (v1.0.0 schema) or flat booleans (legacy)
            if "rest_api" not in item:
                if "api" in item:
                    api = item["api"]
                    item["rest_api"] = {
                        "creatable": api.get("creatable", False),
                        "definition": api.get("definition", False),
                    }
                    if "name" in api:
                        item["rest_api"]["api_name"] = api["name"]
                    # Preserve api_path at top level for backward compat
                    if "api_path" not in item:
                        item["api_path"] = api.get("path", "items")
                elif "api_creatable" in item:
                    item["rest_api"] = {
                        "creatable": item.pop("api_creatable", False),
                        "definition": item.pop("api_definition", False),
                    }
                    if "api_name" in item:
                        item["rest_api"]["api_name"] = item.pop("api_name")
            # Derive phase_order from $phase legend position (v1.0.0)
            if "phase_order" not in item:
                phase_legend = data.get("$phase", {})
                phase_keys = list(phase_legend.keys())
                phase_name = item.get("phase", "")
                if phase_name in phase_keys:
                    item["phase_order"] = phase_keys.index(phase_name) + 1
                else:
                    item["phase_order"] = 99
        _cache = types
    return _cache


def load_full_registry() -> dict:
    """Load the complete registry JSON including schema/version metadata.

    Use this when you need the full structure for round-trip read → modify →
    save (e.g. ``sync-item-types.py``).  The ``types`` dict inside is the
    same cached object returned by :func:`load_registry`.
    """
    global _full_cache
    if _full_cache is None:
        _full_cache = _read_registry_file()
        # Ensure types cache is also populated
        global _cache
        if _cache is None:
            _cache = _full_cache.get("types", {})
    return _full_cache


def _read_registry_file() -> dict:
    """Read and parse the registry JSON with clear error messages."""
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(
            f"Item type registry not found at {REGISTRY_PATH}. "
            f"Expected repo root: {REPO_ROOT}"
        )
    try:
        with open(REGISTRY_PATH, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in {REGISTRY_PATH}: {exc}"
        ) from exc


# ─────────────────────────────────────────────────────────────────────────────
# Normalisation utilities
# ─────────────────────────────────────────────────────────────────────────────

def normalize_type_key(item_type: str) -> str:
    """Normalize an item type string for case-insensitive lookups.

    Strips spaces, hyphens, and underscores then lowercases::

        "Data Pipeline" → "datapipeline"
        "data-pipeline" → "datapipeline"
        "DATA_PIPELINE" → "datapipeline"
    """
    return item_type.lower().replace(" ", "").replace("-", "").replace("_", "")


# ─────────────────────────────────────────────────────────────────────────────
# Generic builder factory — eliminates copy-paste across 7+ builders
# ─────────────────────────────────────────────────────────────────────────────

def _build_variant_map(
    value_fn: Callable[[str, dict], Any],
    *,
    include_capitalized_aliases: bool = False,
) -> dict:
    """Build a dict mapping type-name variants → derived value.

    For each registry entry the map includes keys for the canonical name,
    ``fab_type``, ``display_name``, and every alias.  When
    *include_capitalized_aliases* is ``True``, multi-word aliases also get
    a ``" ".join(w.capitalize())`` form for fuzzy handoff matching.

    *value_fn(canonical, data)* returns the value to store, or ``None`` to
    skip the entry entirely.
    """
    registry = load_registry()
    result: dict = {}

    for canonical, data in registry.items():
        value = value_fn(canonical, data)
        if value is None:
            continue

        result[canonical] = value
        result[data.get("fab_type", canonical)] = value
        result[data.get("display_name", canonical)] = value

        for alias in data.get("aliases", []):
            result[alias] = value
            if include_capitalized_aliases:
                parts = alias.split()
                if len(parts) > 1:
                    result[" ".join(w.capitalize() for w in parts)] = value

    return result


def build_fab_commands() -> dict[str, bool]:
    """Map lowercase type variants → REST API creatability flag.

    Returns ``{lowercase_alias: True/False}``.

    .. deprecated:: Name kept for backward compatibility; now returns
       REST API creatability flags, not CLI commands.
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
    """Map lowercase type variants → display name."""
    registry = load_registry()
    result: dict[str, str] = {}
    for canonical, data in registry.items():
        display = data.get("display_name", canonical)
        result[canonical.lower()] = display
        for alias in data.get("aliases", []):
            result[alias.lower()] = display
    return result


def build_phase_map() -> dict[str, tuple[str, int]]:
    """Map type-name variants → ``(phase_name, phase_order)``.

    Entries with ``phase == "TBD"`` are skipped.
    """
    def _value(canonical: str, data: dict) -> tuple[str, int] | None:
        phase = data.get("phase", "")
        if not phase or phase == "TBD":
            return None
        return (phase, data.get("phase_order", 99))

    return _build_variant_map(_value, include_capitalized_aliases=True)


def build_task_type_map() -> dict[str, str]:
    """Map type-name variants → Fabric task type string.

    Entries with empty or ``"TBD"`` task_type are skipped.
    """
    def _value(_c: str, data: dict) -> str | None:
        tt = data.get("task_type", "")
        return tt if tt and tt != "TBD" else None

    return _build_variant_map(_value, include_capitalized_aliases=True)


def build_portal_only_items() -> dict[str, str]:
    """Map lowercase name → ``fab_type`` for portal-only items.

    Items that *can* be created via the REST API are excluded.
    """
    registry = load_registry()
    result: dict[str, str] = {}
    for canonical, data in registry.items():
        if not data.get("rest_api", {}).get("creatable", False):
            fab = data.get("fab_type", canonical)
            result[canonical.lower()] = fab
            result[data.get("display_name", canonical).lower()] = fab
            for alias in data.get("aliases", []):
                result[alias.lower()] = fab
    return result


def build_api_creatable_items() -> set[str]:
    """Return ``fab_type`` values creatable via the Fabric REST API."""
    registry = load_registry()
    return {
        data.get("fab_type", name)
        for name, data in registry.items()
        if data.get("rest_api", {}).get("creatable", False)
    }


def build_api_name_remap() -> dict[str, str]:
    """Map ``fab_type`` → REST API name where they differ."""
    registry = load_registry()
    return {
        data.get("fab_type", name): data["rest_api"]["api_name"]
        for name, data in registry.items()
        if "api_name" in data.get("rest_api", {})
    }


def build_availability_map() -> dict[str, str]:
    """Map type-name variants → availability status (``'general availability'`` or ``'public preview'``)."""
    def _value(_c: str, data: dict) -> str:
        return data.get("availability", "general availability")

    return _build_variant_map(_value, include_capitalized_aliases=True)


def build_fab_type_map() -> dict[str, str]:
    """Map display-name variants → ``fab_type``.

    Includes canonical key, ``display_name``, ``fab_type`` (identity), and
    every alias plus title-cased forms so any LLM-generated string resolves
    to the correct ``fab_type``.
    """
    registry = load_registry()
    result: dict[str, str] = {}
    for canonical, data in registry.items():
        fab_type = data.get("fab_type", canonical)
        result[canonical] = fab_type
        result[fab_type] = fab_type
        result[data.get("display_name", canonical)] = fab_type
        for alias in data.get("aliases", []):
            result[alias] = fab_type
            result[alias.title()] = fab_type
            parts = alias.split()
            if len(parts) > 1:
                result[" ".join(w.capitalize() for w in parts)] = fab_type
    return result


def build_cicd_type_set() -> set[str]:
    """Return ``fab_type`` values deployable via fabric-cicd.

    Derived from ``cicd.strategy`` — types with ``platform_only`` or
    ``content`` strategy are supported.
    """
    registry = load_registry()
    return {
        data.get("fab_type", name)
        for name, data in registry.items()
        if data.get("cicd", {}).get("strategy") in ("platform_only", "content")
    }


def build_type_remap() -> dict[str, str]:
    """Map ``display_name`` / alias → ``fab_type`` where they differ.

    Only entries where the display-name or title-cased alias is not equal
    to ``fab_type`` are included.
    """
    registry = load_registry()
    result: dict[str, str] = {}
    for _canonical, data in registry.items():
        fab_type = data.get("fab_type", _canonical)
        display = data.get("display_name", _canonical)
        if display != fab_type:
            result[display] = fab_type
        for alias in data.get("aliases", []):
            titled = alias.title()
            if titled != fab_type:
                result[titled] = fab_type
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Review & test plan pre-computation builders
# ─────────────────────────────────────────────────────────────────────────────

def build_deploy_method_map() -> dict[str, dict]:
    """Map type-name variants → deployment metadata dict.

    Each value contains ``method``, ``strategy``, ``verified``,
    ``creatable``, ``has_definition``, and ``availability`` keys.
    """
    def _value(_c: str, data: dict) -> dict:
        creatable = data.get("rest_api", {}).get("creatable", False)
        has_def = data.get("rest_api", {}).get("definition", False)
        cicd = data.get("cicd", {})
        strategy = cicd.get("strategy")
        verified = cicd.get("verified", False)
        availability = data.get("availability", "general availability")

        if strategy in ("content", "platform_only"):
            method = "cicd"
        elif creatable:
            method = "rest_api"
        else:
            method = "portal"

        return {
            "method": method,
            "strategy": strategy,
            "verified": verified,
            "creatable": creatable,
            "has_definition": has_def,
            "availability": availability,
        }

    return _build_variant_map(_value)


def build_test_method_map() -> dict[str, dict]:
    """Map type-name variants → test method metadata dict.

    Each value contains ``verify_method``, ``definition_check``,
    ``manual_fallback``, ``api_path``, ``supports_definition``,
    ``is_portal_only``, ``phase``, ``phase_order``, and ``notes``.
    """
    def _value(_c: str, data: dict) -> dict:
        creatable = data.get("rest_api", {}).get("creatable", False)
        has_def = data.get("rest_api", {}).get("definition", False)
        api_path = data.get("api_path", "items")
        phase = data.get("phase", "Other")
        phase_order = data.get("phase_order", 99)
        notes = data.get("notes", "")

        if creatable and has_def:
            verify = f"REST API GET /{api_path} | verify {{item}} exists"
            def_check = f"REST API GET /{api_path}/{{item}} | check definition"
        elif creatable:
            verify = f"REST API GET /{api_path} | verify {{item}} exists"
            def_check = None
        else:
            verify = "Verify {item} exists in Fabric portal"
            def_check = None

        return {
            "verify_method": verify,
            "definition_check": def_check,
            "manual_fallback": "Verify {item} exists in Fabric portal",
            "api_path": api_path,
            "supports_definition": has_def,
            "is_portal_only": not creatable,
            "phase": phase,
            "phase_order": phase_order,
            "notes": notes,
        }

    return _build_variant_map(_value)


def build_item_notes_map() -> dict[str, str]:
    """Map type-name variants → notes string.  Empty-notes entries skipped."""
    def _value(_c: str, data: dict) -> str | None:
        notes = data.get("notes", "")
        return notes if notes else None

    return _build_variant_map(_value)


def build_skillset_map() -> dict[str, list[str]]:
    """Map type-name variants → skillset list (e.g. ``["LC"]``)."""
    def _value(_c: str, data: dict) -> list[str]:
        return data.get("skillset", [])

    return _build_variant_map(_value)


def build_alternatives_map() -> dict[str, list[str]]:
    """Map canonical type name → list of alternative item type names.

    Reads the ``alternatives`` field from each item type in the registry.
    Returns only items that have alternatives defined.
    """
    registry = load_registry()
    result: dict[str, list[str]] = {}
    for canonical, data in registry.items():
        alts = data.get("alternatives")
        if alts and isinstance(alts, list):
            result[canonical] = alts
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Registry validation
# ─────────────────────────────────────────────────────────────────────────────

def validate_registry() -> list[str]:
    """Check the registry for structural issues.

    Returns a list of error messages (empty if valid).  Useful for CI
    checks and maintenance scripts.
    """
    errors: list[str] = []
    registry = load_registry()

    _REQUIRED_FIELDS = {"fab_type", "display_name", "phase", "task_type", "aliases"}
    _VALID_PHASES = {
        "Environment", "Foundation", "IQ", "Ingestion",
        "ML", "Monitoring", "Transformation", "Visualization", "TBD",
    }
    _VALID_TASK_TYPES = {
        "get data", "mirror data", "store data", "prepare data",
        "analyze and train data", "track data", "visualize",
        "distribute data", "develop", "govern data", "TBD", "",
    }

    for name, data in registry.items():
        # Check required fields
        missing = _REQUIRED_FIELDS - set(data.keys())
        if missing:
            errors.append(f"{name}: missing fields {sorted(missing)}")

        # Check phase validity
        phase = data.get("phase", "")
        if phase and phase not in _VALID_PHASES:
            errors.append(f"{name}: invalid phase '{phase}'")

        # Check task_type validity
        task_type = data.get("task_type", "")
        if task_type and task_type not in _VALID_TASK_TYPES:
            errors.append(f"{name}: invalid task_type '{task_type}'")

        # Check aliases are lowercase
        for alias in data.get("aliases", []):
            if alias != alias.lower():
                errors.append(f"{name}: alias '{alias}' is not lowercase")

        # Check fab_type is present and non-empty
        if not data.get("fab_type"):
            errors.append(f"{name}: empty or missing fab_type")

    return errors
