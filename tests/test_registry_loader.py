"""Tests for registry_loader.py — verifies the item-type registry is valid."""

import sys
from pathlib import Path

# Ensure _shared/ is importable (registry_loader lives there now)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))

from registry_loader import (
    load_registry,
    build_fab_commands,
    build_display_names,
    build_phase_map,
    build_task_type_map,
    build_portal_only_items,
    build_fab_type_map,
)

VALID_TASK_TYPES = {
    "get data", "mirror data", "store data", "prepare data",
    "analyze and train data", "track data", "visualize",
    "distribute data", "develop", "govern data",
}

VALID_PHASES = {
    "Foundation", "Ingestion", "Transformation", "Visualization",
    "Monitoring", "Governance", "ML", "Environment", "TBD",
}


def test_registry_loads():
    registry = load_registry()
    assert isinstance(registry, dict)
    assert len(registry) >= 10, f"Expected ≥10 item types, got {len(registry)}"


def test_every_type_has_required_fields():
    registry = load_registry()
    required = {"fab_type", "display_name", "cli_supported", "mkdir_supported",
                "phase", "phase_order", "task_type", "aliases"}
    for name, data in registry.items():
        missing = required - set(data.keys())
        assert not missing, f"{name} missing fields: {missing}"


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
    # Lakehouse should be present and have a path template
    assert "lakehouse" in cmds
    assert cmds["lakehouse"] is not None
    path_template, args = cmds["lakehouse"]
    assert "{ws}" in path_template
    assert "{name}" in path_template


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


def test_portal_only_excludes_mkdir_supported():
    registry = load_registry()
    portal_only = build_portal_only_items()
    for name, data in registry.items():
        if data["mkdir_supported"]:
            assert name.lower() not in portal_only, \
                f"{name} is mkdir_supported but appears in portal_only"


def test_fab_type_map_covers_canonical():
    registry = load_registry()
    fab_map = build_fab_type_map()
    for name in registry:
        assert name in fab_map, f"Canonical type {name} missing from fab_type_map"
