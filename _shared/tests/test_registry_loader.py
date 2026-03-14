"""Tests for registry_loader.py — verifies the item-type registry is valid."""

import sys
from pathlib import Path

# Ensure _shared/lib is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from registry_loader import (
    load_registry,
    build_fab_commands,
    build_display_names,
    build_phase_map,
    build_task_type_map,
    build_portal_only_items,
    build_fab_type_map,
    build_api_creatable_items,
    build_api_name_remap,
    build_availability_map,
    build_deploy_method_map,
    build_test_method_map,
    build_item_notes_map,
    build_skillset_map,
    validate_registry,
)

VALID_TASK_TYPES = {
    "get data", "mirror data", "store data", "prepare data",
    "analyze and train data", "track data", "visualize",
    "distribute data", "develop", "govern data",
}

VALID_PHASES = {
    "Foundation", "Ingestion", "Transformation", "Visualization",
    "Monitoring", "Governance", "ML", "Environment", "IQ", "TBD",
}


def test_registry_loads():
    registry = load_registry()
    assert isinstance(registry, dict)
    assert len(registry) >= 10, f"Expected ≥10 item types, got {len(registry)}"


def test_every_type_has_required_fields():
    registry = load_registry()
    required = {"fab_type", "display_name",
                "phase", "phase_order", "task_type", "aliases", "rest_api",
                "availability"}
    for name, data in registry.items():
        missing = required - set(data.keys())
        assert not missing, f"{name} missing fields: {missing}"


def test_rest_api_has_required_subfields():
    registry = load_registry()
    for name, data in registry.items():
        ra = data.get("rest_api", {})
        assert "creatable" in ra, f"{name} rest_api missing 'creatable'"
        assert "definition" in ra, f"{name} rest_api missing 'definition'"
        assert isinstance(ra["creatable"], bool), f"{name} rest_api.creatable must be bool"
        assert isinstance(ra["definition"], bool), f"{name} rest_api.definition must be bool"


def test_task_types_are_valid():
    registry = load_registry()
    for name, data in registry.items():
        tt = data["task_type"]
        if tt and tt != "TBD":
            assert tt in VALID_TASK_TYPES, f"{name} has invalid task_type: {tt}"


def test_phases_are_valid():
    registry = load_registry()
    for name, data in registry.items():
        assert data["phase"] in VALID_PHASES, f"{name} has invalid phase: {data['phase']}"


def test_aliases_are_lowercase():
    registry = load_registry()
    for name, data in registry.items():
        for alias in data["aliases"]:
            assert alias == alias.lower(), f"{name} alias not lowercase: {alias}"


def test_build_fab_commands_returns_dict():
    cmds = build_fab_commands()
    assert isinstance(cmds, dict)
    assert len(cmds) > 0
    # Lakehouse should be REST API creatable
    assert "lakehouse" in cmds
    assert cmds["lakehouse"] is True
    # Non-creatable items should be False
    for key, val in cmds.items():
        assert isinstance(val, bool), f"{key} should be bool, got {type(val)}"


def test_build_display_names_returns_dict():
    names = build_display_names()
    assert isinstance(names, dict)
    assert names.get("lakehouse") == "Lakehouse"
    assert names.get("warehouse") == "Warehouse"


def test_build_task_type_map_covers_all():
    type_map = build_task_type_map()
    assert isinstance(type_map, dict)
    assert len(type_map) > 0
    # Every value should be a valid task type
    for key, val in type_map.items():
        assert val in VALID_TASK_TYPES, f"Invalid task type for {key}: {val}"


def test_build_phase_map_returns_tuples():
    phase_map = build_phase_map()
    assert isinstance(phase_map, dict)
    for key, val in phase_map.items():
        assert isinstance(val, tuple) and len(val) == 2
        phase_name, phase_order = val
        assert isinstance(phase_name, str)
        assert isinstance(phase_order, int)


def test_portal_only_excludes_api_creatable():
    registry = load_registry()
    portal_only = build_portal_only_items()
    for name, data in registry.items():
        if data.get("rest_api", {}).get("creatable", False):
            assert name.lower() not in portal_only, \
                f"{name} is REST API creatable but appears in portal_only"


def test_fab_type_map_covers_canonical():
    registry = load_registry()
    fab_map = build_fab_type_map()
    for name in registry:
        assert name in fab_map, f"Canonical type {name} missing from fab_type_map"


def test_api_creatable_items_returns_set():
    creatable = build_api_creatable_items()
    assert isinstance(creatable, set)
    assert len(creatable) > 0
    # Lakehouse and Warehouse should always be API-creatable
    assert "Lakehouse" in creatable
    assert "Warehouse" in creatable
    # DataAgent is confirmed API-creatable
    assert "DataAgent" in creatable


def test_api_creatable_excludes_non_creatable():
    registry = load_registry()
    creatable = build_api_creatable_items()
    for name, data in registry.items():
        if not data.get("rest_api", {}).get("creatable", False):
            assert data["fab_type"] not in creatable, \
                f"{name} marked not creatable but appears in build_api_creatable_items()"


def test_api_name_remap_returns_dict():
    remap = build_api_name_remap()
    assert isinstance(remap, dict)
    # Known mismatches should be present
    for fab_type, api_name in remap.items():
        assert fab_type != api_name, \
            f"Remap entry {fab_type} maps to itself — should only contain mismatches"


VALID_AVAILABILITY = {"ga", "preview"}


def test_availability_values_are_valid():
    registry = load_registry()
    for name, data in registry.items():
        avail = data["availability"]
        assert avail in VALID_AVAILABILITY, f"{name} has invalid availability: {avail}"


def test_build_availability_map_returns_dict():
    avail_map = build_availability_map()
    assert isinstance(avail_map, dict)
    assert len(avail_map) > 0
    # All values should be valid availability strings
    for key, val in avail_map.items():
        assert val in VALID_AVAILABILITY, f"Invalid availability for {key}: {val}"


def test_build_availability_map_covers_canonical():
    registry = load_registry()
    avail_map = build_availability_map()
    for name in registry:
        assert name in avail_map, f"Canonical type {name} missing from availability_map"


# ── Deploy method map tests ───────────────────────────────────────────────

VALID_DEPLOY_METHODS = {"cicd", "rest_api", "portal"}


def test_build_deploy_method_map_returns_dict():
    dm = build_deploy_method_map()
    assert isinstance(dm, dict)
    assert len(dm) > 0


def test_deploy_method_map_has_valid_methods():
    dm = build_deploy_method_map()
    for key, val in dm.items():
        assert val["method"] in VALID_DEPLOY_METHODS, \
            f"{key} has invalid deploy method: {val['method']}"


def test_deploy_method_map_lakehouse_is_cicd():
    dm = build_deploy_method_map()
    lh = dm.get("Lakehouse")
    assert lh is not None
    assert lh["method"] == "cicd"
    assert lh["strategy"] == "platform_only"
    assert lh["verified"] is True
    assert lh["creatable"] is True


def test_deploy_method_map_portal_only_items():
    dm = build_deploy_method_map()
    portal_items = {k: v for k, v in dm.items() if v["method"] == "portal"}
    assert len(portal_items) > 0, "Should have at least one portal-only item"
    for key, val in portal_items.items():
        assert val["creatable"] is False


def test_deploy_method_map_covers_canonical():
    registry = load_registry()
    dm = build_deploy_method_map()
    for name in registry:
        assert name in dm, f"Canonical type {name} missing from deploy_method_map"


# ── Test method map tests ─────────────────────────────────────────────────

def test_build_test_method_map_returns_dict():
    tm = build_test_method_map()
    assert isinstance(tm, dict)
    assert len(tm) > 0


def test_test_method_map_has_required_keys():
    tm = build_test_method_map()
    required = {"verify_method", "api_path", "supports_definition", "is_portal_only", "phase", "phase_order"}
    for key, val in tm.items():
        for req in required:
            assert req in val, f"{key} missing required key: {req}"


def test_test_method_map_portal_items_use_manual():
    tm = build_test_method_map()
    for key, val in tm.items():
        if val["is_portal_only"]:
            assert "portal" in val["verify_method"].lower(), \
                f"Portal-only {key} should have portal in verify_method"


def test_test_method_map_rest_items_use_api():
    tm = build_test_method_map()
    for key, val in tm.items():
        if not val["is_portal_only"]:
            assert "REST API GET" in val["verify_method"], \
                f"REST-capable {key} should have REST API in verify_method"


def test_test_method_map_definition_check_only_when_supported():
    tm = build_test_method_map()
    for key, val in tm.items():
        if val["supports_definition"]:
            assert val["definition_check"] is not None, \
                f"{key} supports definition but has no definition_check"
        else:
            assert val["definition_check"] is None, \
                f"{key} has definition_check but supports_definition is False"


# ── Item notes map tests ──────────────────────────────────────────────────

def test_build_item_notes_map_returns_dict():
    nm = build_item_notes_map()
    assert isinstance(nm, dict)


def test_item_notes_map_excludes_empty():
    nm = build_item_notes_map()
    for key, val in nm.items():
        assert val, f"{key} has empty notes but should be excluded"


# ── build_skillset_map ──────────────────────────────────────────────


def test_build_skillset_map_returns_dict():
    sm = build_skillset_map()
    assert isinstance(sm, dict)
    assert len(sm) > 0


def test_skillset_map_values_are_lists():
    sm = build_skillset_map()
    for key, val in sm.items():
        assert isinstance(val, list), f"{key} skillset is not a list: {val}"


VALID_SKILLSETS = {"LC", "CF", "auto", "Portal"}


def test_skillset_map_valid_tags():
    sm = build_skillset_map()
    for key, val in sm.items():
        for tag in val:
            assert tag in VALID_SKILLSETS, f"{key} has invalid skillset tag: {tag}"


def test_skillset_map_known_items():
    sm = build_skillset_map()
    assert sm.get("Notebook") == ["CF"]
    assert sm.get("Lakehouse") == ["LC"]
    assert "LC" in sm.get("Data Pipeline", []) or "LC" in sm.get("DataPipeline", [])


# ── validate_registry ─────────────────────────────────────────────────────


def test_validate_registry_returns_no_errors():
    """The live registry should pass all validation checks."""
    errors = validate_registry()
    assert errors == [], f"Registry validation errors:\n" + "\n".join(errors)
