"""Tests for registry_loader.py — verifies the item-type registry is valid."""

import sys
from pathlib import Path

# Ensure _shared/lib is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from registry_loader import (
    load_registry,
    build_display_names,
    build_phase_map,
    build_task_type_map,
    build_fab_type_map,
    build_deploy_method_map,
    build_test_method_map,
    build_layer_map,
    build_type_to_decision_map,
    validate_registry,
)

VALID_TASK_TYPES = {
    "get data", "mirror data", "store data", "prepare data",
    "analyze and train data", "track data", "visualize",
    "distribute data", "develop data",
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


def test_fab_type_map_covers_canonical():
    registry = load_registry()
    fab_map = build_fab_type_map()
    for name in registry:
        assert name in fab_map, f"Canonical type {name} missing from fab_type_map"


VALID_AVAILABILITY = {"ga", "pupr", "prpr"}


def test_availability_values_are_valid():
    registry = load_registry()
    for name, data in registry.items():
        avail = data["availability"]
        assert avail in VALID_AVAILABILITY, f"{name} has invalid availability: {avail}"


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


# ── validate_registry─────────────────────────────────────────────────────


def test_validate_registry_returns_no_errors():
    """The live registry should pass all validation checks."""
    errors = validate_registry()
    assert errors == [], f"Registry validation errors:\n" + "\n".join(errors)


# ── Cross-field consistency tests ─────────────────────────────────────────


def test_cicd_content_requires_definition():
    """If cicd.strategy is 'content', api.definition must be true."""
    registry = load_registry()
    for name, data in registry.items():
        strategy = data.get("cicd", {}).get("strategy")
        definition = data.get("rest_api", {}).get("definition", False)
        if strategy == "content":
            assert definition, (
                f"{name}: cicd.strategy='content' but api.definition=False — "
                "content deployment requires definition support"
            )


def test_cicd_verified_requires_supported_strategy():
    """If cicd.verified is true, strategy must not be 'unsupported'."""
    registry = load_registry()
    for name, data in registry.items():
        cicd = data.get("cicd", {})
        if cicd.get("verified") is True:
            assert cicd.get("strategy") != "unsupported", (
                f"{name}: cicd.verified=True but strategy='unsupported' — "
                "cannot verify an unsupported deployment strategy"
            )


def test_code_first_items_have_query_language():
    """Code-first items (skillset includes 'CF') should have query_language populated."""
    registry = load_registry()
    for name, data in registry.items():
        skillset = data.get("skillset", [])
        if "CF" in skillset and data.get("task_type") in ("prepare", "train", "model", "query"):
            ql = data.get("query_language", [])
            assert len(ql) > 0, (
                f"{name}: skillset includes 'CF' with task_type "
                f"'{data['task_type']}' but query_language is empty"
            )


def test_alternatives_are_symmetric():
    """If item A lists B as an alternative, B should list A back."""
    registry = load_registry()
    for name, data in registry.items():
        for alt in data.get("alternatives", []):
            alt_data = registry.get(alt)
            assert alt_data is not None, (
                f"{name}: alternative '{alt}' does not exist in registry"
            )
            alt_alternatives = alt_data.get("alternatives", [])
            assert name in alt_alternatives, (
                f"{name} lists {alt} as alternative but {alt} "
                f"does not list {name} back"
            )


# ── Layer map tests ───────────────────────────────────────────────────────

EXPECTED_LAYERS = {
    "Lakehouse":    ("Store",     "🗄️"),
    "Warehouse":    ("Store",     "🗄️"),
    "Notebook":     ("Process",   "⚙️"),
    "DataPipeline": ("Ingest",    "📥"),
    "MLModel":      ("AI / ML",   "🤖"),
    "Reflex":       ("Alert",     "🔔"),
    "Environment":  ("Config",    "🔧"),
}


def test_build_layer_map_returns_dict():
    lm = build_layer_map()
    assert isinstance(lm, dict)
    assert len(lm) > 0


def test_layer_map_known_types():
    """Known canonical types map to the correct (layer, emoji) tuples."""
    lm = build_layer_map()
    for canonical, expected in EXPECTED_LAYERS.items():
        assert lm.get(canonical) == expected, (
            f"{canonical}: expected {expected}, got {lm.get(canonical)}"
        )


def test_layer_map_resolves_aliases():
    """Aliases and fab_type variants resolve to the same layer."""
    lm = build_layer_map()
    # Lakehouse aliases
    assert lm.get("lh") == ("Store", "🗄️")
    assert lm.get("lake house") == ("Store", "🗄️")
    # Notebook aliases
    assert lm.get("nb") == ("Process", "⚙️")
    # DataPipeline aliases
    assert lm.get("pipeline") == ("Ingest", "📥")


def test_layer_map_values_are_tuples():
    """Every value in the layer map is a (str, str) tuple."""
    lm = build_layer_map()
    for key, val in lm.items():
        assert isinstance(val, tuple) and len(val) == 2, (
            f"{key}: expected 2-tuple, got {val!r}"
        )
        assert isinstance(val[0], str) and isinstance(val[1], str)


def test_layer_map_covers_canonical():
    """Every canonical registry type appears in the layer map."""
    registry = load_registry()
    lm = build_layer_map()
    for name in registry:
        assert name in lm, f"Canonical type {name} missing from layer_map"


# ── Type-to-decision map tests ───────────────────────────────────────────

EXPECTED_DECISIONS = {
    "lakehouse":    "storage",
    "warehouse":    "storage",
    "notebook":     "processing",
    "datapipeline": "ingestion",
}


def test_build_type_to_decision_map_returns_dict():
    dm = build_type_to_decision_map()
    assert isinstance(dm, dict)
    assert len(dm) > 0


def test_decision_map_known_types():
    """Known types map to the correct decision category."""
    dm = build_type_to_decision_map()
    for key, expected in EXPECTED_DECISIONS.items():
        assert dm.get(key) == expected, (
            f"{key}: expected {expected!r}, got {dm.get(key)!r}"
        )


def test_decision_map_keys_are_lowercase():
    """All keys in the decision map must be lowercase."""
    dm = build_type_to_decision_map()
    for key in dm:
        assert key == key.lower(), f"Key {key!r} is not lowercase"


def test_decision_map_resolves_aliases():
    """Aliases resolve correctly in the decision map."""
    dm = build_type_to_decision_map()
    assert dm.get("lh") == "storage"
    assert dm.get("nb") == "processing"
    assert dm.get("pipeline") == "ingestion"


def test_decision_map_excludes_unmapped_phases():
    """Types with ML, IQ, Monitoring, or Environment phases are excluded."""
    dm = build_type_to_decision_map()
    # MLModel has phase=ML → no decision mapping
    assert "mlmodel" not in dm
    # Reflex has phase=Monitoring → no decision mapping
    assert "reflex" not in dm
    # Environment has phase=Environment → no decision mapping
    assert "environment" not in dm
