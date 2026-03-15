"""Tests for handoff-scaffolder.py — verifies architecture handoff template generation."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

SHARED_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SHARED_DIR / "lib"))

REPO_ROOT = SHARED_DIR.parent
DESIGN_SKILL = REPO_ROOT / ".github" / "skills" / "fabric-design"

# ── Import helpers from the script under test ─────────────────────────────

_spec = importlib.util.spec_from_file_location(
    "handoff_scaffolder",
    str(DESIGN_SKILL / "scripts" / "handoff-scaffolder.py"),
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["handoff_scaffolder"] = _mod
_spec.loader.exec_module(_mod)

scaffold = _mod.scaffold
parse_diagram = _mod.parse_diagram
DiagramItem = _mod.DiagramItem
DeployItem = _mod.DeployItem
Wave = _mod.Wave
_build_deploy_items = _mod._build_deploy_items
_build_waves = _mod._build_waves
_emit_items_yaml = _mod._emit_items_yaml
_emit_waves_yaml = _mod._emit_waves_yaml
_emit_ac_yaml = _mod._emit_ac_yaml
_to_kebab = _mod._to_kebab
_wave_number = _mod._wave_number
_purpose_from = _mod._purpose_from
_filter_by_decisions = _mod._filter_by_decisions

# ── Mock deployment-order data ────────────────────────────────────────────

MOCK_REGISTRY = {
    "mock-flow": {
        "primaryStorage": "Lakehouse",
        "items": [
            {
                "order": "1a",
                "itemType": "Lakehouse",
                "dependsOn": [],
                "requiredFor": ["Bronze storage"],
            },
            {
                "order": "1b",
                "itemType": "Warehouse",
                "dependsOn": [],
                "requiredFor": ["Gold layer queries"],
            },
            {
                "order": "2a",
                "itemType": "Notebook",
                "dependsOn": ["Lakehouse"],
                "requiredFor": ["Bronze → Silver transform"],
            },
            {
                "order": "3a",
                "itemType": "Data Pipeline",
                "dependsOn": ["Notebook", "Lakehouse"],
                "requiredFor": ["Orchestration"],
            },
        ],
    },
    "single-item": {
        "primaryStorage": "Lakehouse",
        "items": [
            {
                "order": "1a",
                "itemType": "Lakehouse",
                "dependsOn": [],
                "requiredFor": ["Storage"],
            },
        ],
    },
    "alt-flow": {
        "primaryStorage": "Lakehouse / Warehouse",
        "items": [
            {
                "order": "1a",
                "itemType": "Lakehouse",
                "dependsOn": [],
                "requiredFor": ["Storage"],
                "alternativeGroup": "gold-storage",
            },
            {
                "order": "1a",
                "itemType": "Warehouse",
                "dependsOn": [],
                "requiredFor": ["Storage"],
                "alternativeGroup": "gold-storage",
            },
        ],
    },
    "alt-ingestion-flow": {
        "primaryStorage": "Lakehouse",
        "items": [
            {
                "order": "1a",
                "itemType": "Lakehouse",
                "dependsOn": [],
                "requiredFor": ["Storage"],
            },
            {
                "order": "2a",
                "itemType": "Copy Job",
                "dependsOn": ["Lakehouse"],
                "requiredFor": ["Ingestion"],
                "alternativeGroup": "ingestion",
            },
            {
                "order": "2a",
                "itemType": "Pipeline",
                "dependsOn": ["Lakehouse"],
                "requiredFor": ["Ingestion"],
                "alternativeGroup": "ingestion",
            },
        ],
    },
}


def _mock_get_deployment_items(task_flow: str):
    """Return items from the mock registry."""
    flow_data = MOCK_REGISTRY.get(task_flow, {})
    return flow_data.get("items", [])


# ── Naming helper tests ──────────────────────────────────────────────────

class TestToKebab:
    def test_simple_type(self):
        assert _to_kebab("Notebook") == "notebook"

    def test_multi_word(self):
        assert _to_kebab("Data Pipeline") == "data-pipeline"

    def test_lakehouse_modifier(self):
        assert _to_kebab("Lakehouse Bronze") == "bronze-lakehouse"

    def test_warehouse_modifier(self):
        assert _to_kebab("Warehouse Gold") == "gold-warehouse"

    def test_plain_lakehouse(self):
        assert _to_kebab("Lakehouse") == "lakehouse"

    def test_copy_job(self):
        assert _to_kebab("Copy Job") == "copy-job"


class TestWaveNumber:
    def test_simple_digit(self):
        assert _wave_number("1") == 1

    def test_letter_suffix(self):
        assert _wave_number("2a") == 2

    def test_multi_digit(self):
        assert _wave_number("10b") == 10

    def test_no_digit(self):
        assert _wave_number("abc") == 0

    def test_whitespace(self):
        assert _wave_number("  3b ") == 3


class TestPurposeFrom:
    def test_required_for_text(self):
        assert _purpose_from("Notebook", "Bronze → Silver") == "Interactive Spark processing for Bronze → Silver"

    def test_optional_fallback(self):
        assert _purpose_from("Notebook", "(optional)") == "Interactive Spark processing for data workloads"

    def test_empty_fallback(self):
        assert _purpose_from("Notebook", "") == "Interactive Spark processing for data workloads"

    def test_whitespace_only_fallback(self):
        assert _purpose_from("Notebook", "   ") == "Interactive Spark processing for data workloads"

    def test_unknown_type_with_required_for(self):
        assert _purpose_from("CustomWidget", "dashboard") == "dashboard"

    def test_unknown_type_no_required_for(self):
        assert _purpose_from("CustomWidget", "") == "CustomWidget deployment"

    def test_base_type_lookup(self):
        assert _purpose_from("Lakehouse Bronze", "raw ingestion") == "Delta Lake storage for raw ingestion"


# ── parse_diagram tests ──────────────────────────────────────────────────

class TestParseDiagram:
    @patch.object(_mod, "get_deployment_items", side_effect=_mock_get_deployment_items)
    def test_returns_diagram_items(self, _mock):
        items = parse_diagram("mock-flow")
        assert len(items) == 4
        assert all(isinstance(i, DiagramItem) for i in items)

    @patch.object(_mod, "get_deployment_items", side_effect=_mock_get_deployment_items)
    def test_preserves_order(self, _mock):
        items = parse_diagram("mock-flow")
        orders = [i.order for i in items]
        assert orders == ["1a", "1b", "2a", "3a"]

    @patch.object(_mod, "get_deployment_items", side_effect=_mock_get_deployment_items)
    def test_unknown_task_flow_raises_value_error(self, _mock):
        try:
            parse_diagram("nonexistent-flow")
            assert False, "Expected ValueError"
        except ValueError as e:
            assert "nonexistent-flow" in str(e)

    @patch.object(_mod, "get_deployment_items", return_value=[])
    def test_empty_registry_raises_value_error(self, _mock):
        try:
            parse_diagram("empty-flow")
            assert False, "Expected ValueError"
        except ValueError as e:
            assert "empty-flow" in str(e)

    @patch.object(_mod, "get_deployment_items", side_effect=_mock_get_deployment_items)
    def test_alternative_items_flagged(self, _mock):
        items = parse_diagram("alt-flow")
        assert len(items) == 2
        assert all(i.is_alternative for i in items)


# ── _build_deploy_items tests ─────────────────────────────────────────────

class TestBuildDeployItems:
    def _make_diagram_items(self):
        return [
            DiagramItem(order="1a", item_type="Lakehouse", skillset="[LC]",
                        depends_on="", required_for="Bronze storage"),
            DiagramItem(order="2a", item_type="Notebook", skillset="[LC]",
                        depends_on="Lakehouse", required_for="Transform"),
        ]

    def test_returns_deploy_items(self):
        result = _build_deploy_items(self._make_diagram_items())
        assert len(result) == 2
        assert all(isinstance(i, DeployItem) for i in result)

    def test_item_names_are_kebab(self):
        result = _build_deploy_items(self._make_diagram_items())
        assert result[0].item_name == "lakehouse"
        assert result[1].item_name == "notebook"

    def test_wave_numbers_from_order(self):
        result = _build_deploy_items(self._make_diagram_items())
        assert result[0].wave == 1
        assert result[1].wave == 2

    def test_dependencies_parsed(self):
        result = _build_deploy_items(self._make_diagram_items())
        assert result[0].dependencies == []
        assert result[1].dependencies == ["Lakehouse"]

    def test_purpose_uses_required_for(self):
        result = _build_deploy_items(self._make_diagram_items())
        assert result[0].purpose == "Delta Lake storage for Bronze storage"


# ── _build_waves tests ────────────────────────────────────────────────────

class TestBuildWaves:
    def _make_deploy_items(self):
        return [
            DeployItem(item_name="lakehouse", item_type="Lakehouse",
                       fab_type="Lakehouse", wave=1),
            DeployItem(item_name="warehouse", item_type="Warehouse",
                       fab_type="Warehouse", wave=1),
            DeployItem(item_name="notebook", item_type="Notebook",
                       fab_type="Notebook", wave=2,
                       dependencies=["Lakehouse"]),
        ]

    def test_groups_by_wave(self):
        waves = _build_waves(self._make_deploy_items())
        assert len(waves) == 2
        assert waves[0].wave_number == 1
        assert waves[1].wave_number == 2

    def test_wave_items(self):
        waves = _build_waves(self._make_deploy_items())
        assert set(waves[0].items) == {"lakehouse", "warehouse"}
        assert waves[1].items == ["notebook"]

    def test_parallel_capable_when_multiple(self):
        waves = _build_waves(self._make_deploy_items())
        assert waves[0].parallel_capable is True
        assert waves[1].parallel_capable is False

    def test_wave_dependencies(self):
        waves = _build_waves(self._make_deploy_items())
        assert waves[0].dependencies == []
        assert waves[1].dependencies == ["Lakehouse"]

    def test_sorted_wave_order(self):
        items = [
            DeployItem(item_name="z", item_type="T", fab_type="T", wave=3),
            DeployItem(item_name="a", item_type="T", fab_type="T", wave=1),
        ]
        waves = _build_waves(items)
        assert [w.wave_number for w in waves] == [1, 3]


# ── YAML emitter tests ───────────────────────────────────────────────────

class TestEmitItemsYaml:
    def test_contains_items_key(self):
        items = [DeployItem(item_name="lh", item_type="Lakehouse",
                            fab_type="Lakehouse", wave=1, purpose="store")]
        yaml = _emit_items_yaml(items)
        assert yaml.startswith("items:")

    def test_item_fields_present(self):
        items = [DeployItem(item_name="lh", item_type="Lakehouse",
                            fab_type="Lakehouse", wave=1,
                            dependencies=["dep1"], purpose="store")]
        yaml = _emit_items_yaml(items)
        assert 'name: "lh"' in yaml
        assert 'type: "Lakehouse"' in yaml
        assert "depends_on: [dep1]" in yaml
        assert 'purpose: "store"' in yaml

    def test_alternative_note_included(self):
        items = [DeployItem(item_name="wh", item_type="Warehouse",
                            fab_type="Warehouse", wave=1,
                            is_alternative=True,
                            alternative_note="Alternative to lakehouse")]
        yaml = _emit_items_yaml(items)
        assert "Alternative to lakehouse" in yaml

    def test_portal_only_note(self):
        items = [DeployItem(item_name="x", item_type="X",
                            fab_type="X", wave=1, portal_only=True)]
        yaml = _emit_items_yaml(items)
        assert "portal-only" in yaml


class TestEmitWavesYaml:
    def test_contains_waves_key(self):
        waves = [Wave(wave_number=1, items=["a"], parallel_capable=False)]
        yaml = _emit_waves_yaml(waves)
        assert yaml.startswith("waves:")

    def test_wave_fields_present(self):
        waves = [Wave(wave_number=1, items=["a", "b"],
                      dependencies=["dep"], parallel_capable=True)]
        yaml = _emit_waves_yaml(waves)
        assert "id: 1" in yaml
        assert "items: [a, b]" in yaml
        assert "parallel: true" in yaml


class TestEmitAcYaml:
    def test_contains_ac_key(self):
        items = [DeployItem(item_name="lh", item_type="Lakehouse",
                            fab_type="Lakehouse", wave=1)]
        yaml = _emit_ac_yaml(items, "test")
        assert yaml.startswith("acceptance_criteria:")

    def test_ac_ids_sequential(self):
        items = [
            DeployItem(item_name="a", item_type="A", fab_type="A", wave=1),
            DeployItem(item_name="b", item_type="B", fab_type="B", wave=2),
        ]
        yaml = _emit_ac_yaml(items, "test")
        assert "id: AC-1" in yaml
        assert "id: AC-2" in yaml

    def test_ac_references_item_name(self):
        items = [DeployItem(item_name="my-lh", item_type="Lakehouse",
                            fab_type="Lakehouse", wave=1)]
        yaml = _emit_ac_yaml(items, "test")
        assert "my-lh exists" in yaml

    def test_ac_portal_only_suffix(self):
        items = [DeployItem(item_name="x", item_type="X",
                            fab_type="X", wave=1, portal_only=True)]
        yaml = _emit_ac_yaml(items, "test")
        assert "portal-only" in yaml


# ── Full scaffold integration tests ──────────────────────────────────────

class TestScaffold:
    @patch.object(_mod, "get_deployment_items", side_effect=_mock_get_deployment_items)
    def test_returns_markdown_string(self, _mock):
        md = scaffold("mock-flow", "Test Project")
        assert isinstance(md, str)
        assert len(md) > 0

    @patch.object(_mod, "get_deployment_items", side_effect=_mock_get_deployment_items)
    def test_contains_header(self, _mock):
        md = scaffold("mock-flow", "Test Project")
        assert "# Architecture Handoff" in md

    @patch.object(_mod, "get_deployment_items", side_effect=_mock_get_deployment_items)
    def test_contains_project_name(self, _mock):
        md = scaffold("mock-flow", "My Cool Project")
        assert "My Cool Project" in md

    @patch.object(_mod, "get_deployment_items", side_effect=_mock_get_deployment_items)
    def test_contains_task_flow(self, _mock):
        md = scaffold("mock-flow", "Test Project")
        assert "**Task flow:** mock-flow" in md

    @patch.object(_mod, "get_deployment_items", side_effect=_mock_get_deployment_items)
    def test_contains_yaml_blocks(self, _mock):
        md = scaffold("mock-flow", "Test Project")
        assert "items:" in md
        assert "waves:" in md
        assert "acceptance_criteria:" in md

    @patch.object(_mod, "get_deployment_items", side_effect=_mock_get_deployment_items)
    def test_contains_all_items(self, _mock):
        md = scaffold("mock-flow", "Test Project")
        assert "lakehouse" in md
        assert "warehouse" in md
        assert "notebook" in md
        assert "data-pipeline" in md

    @patch.object(_mod, "get_deployment_items", side_effect=_mock_get_deployment_items)
    def test_wave_ordering_correct(self, _mock):
        md = scaffold("mock-flow", "Test Project")
        wave1_pos = md.index("id: 1")
        wave2_pos = md.index("id: 2")
        wave3_pos = md.index("id: 3")
        assert wave1_pos < wave2_pos < wave3_pos

    @patch.object(_mod, "get_deployment_items", side_effect=_mock_get_deployment_items)
    def test_contains_scaffold_warning(self, _mock):
        md = scaffold("mock-flow", "Test Project")
        assert "Items to Deploy" in md

    @patch.object(_mod, "get_deployment_items", side_effect=_mock_get_deployment_items)
    def test_unknown_task_flow_raises(self, _mock):
        try:
            scaffold("nonexistent", "Test Project")
            assert False, "Expected ValueError"
        except ValueError:
            pass

    @patch.object(_mod, "get_deployment_items", side_effect=_mock_get_deployment_items)
    def test_single_item_flow(self, _mock):
        md = scaffold("single-item", "Test Project")
        assert "items:" in md
        assert "lakehouse" in md
        assert "AC-1" in md
        # Only one item → one AC
        assert "AC-2" not in md

    @patch.object(_mod, "get_deployment_items", side_effect=_mock_get_deployment_items)
    def test_alternative_items_annotated(self, _mock):
        md = scaffold("alt-flow", "Test Project")
        assert "Alternative to" in md


# ── Decision filtering regression tests ──────────────────────────────────


class TestFilterByDecisions:
    """Tests for _filter_by_decisions — verifies alternative pruning and fallback."""

    def _make_alt_items(self):
        """Create a list of items with an alternative group (Lakehouse vs Warehouse)."""
        return [
            DiagramItem(order="1a", item_type="Lakehouse", skillset="[LC]",
                        depends_on="", required_for="Storage",
                        is_alternative=True, alternative_group="Warehouse"),
            DiagramItem(order="1a", item_type="Warehouse", skillset="[LC]",
                        depends_on="", required_for="Storage",
                        is_alternative=True, alternative_group="Lakehouse"),
        ]

    def test_matching_decision_prunes_unchosen(self):
        """High-confidence Lakehouse decision should prune Warehouse."""
        items = self._make_alt_items()
        decisions = {"decisions": {"storage": {"choice": "Lakehouse", "confidence": "high"}}}
        result = _filter_by_decisions(items, decisions)
        types = [i.item_type for i in result]
        assert "Lakehouse" in types
        assert "Warehouse" not in types

    def test_mismatched_decision_falls_back(self):
        """Decision resolving to Eventhouse (not in flow) should recover first alternative."""
        items = self._make_alt_items()
        decisions = {"decisions": {"storage": {"choice": "Eventhouse", "confidence": "high"}}}
        result = _filter_by_decisions(items, decisions)
        types = [i.item_type for i in result]
        # Should NOT lose both items — at least one must survive as fallback
        assert len(types) >= 1, "All alternatives lost — fallback failed"
        # The fallback item should no longer be marked as an alternative
        for item in result:
            if item.item_type in ("Lakehouse", "Warehouse"):
                assert not item.is_alternative, "Fallback item should not be marked as alternative"

    def test_ambiguous_decision_keeps_all(self):
        """Ambiguous decisions should keep all alternatives (no pruning)."""
        items = self._make_alt_items()
        decisions = {"decisions": {"storage": {"choice": "Lakehouse", "confidence": "ambiguous"}}}
        result = _filter_by_decisions(items, decisions)
        types = [i.item_type for i in result]
        assert "Lakehouse" in types
        assert "Warehouse" in types

    @patch.object(_mod, "get_deployment_items", side_effect=_mock_get_deployment_items)
    def test_ingestion_mismatch_recovers(self, _mock):
        """Ingestion decision=Eventstream (not in flow) should fall back to first ingestion item."""
        items = parse_diagram("alt-ingestion-flow")
        decisions = {"decisions": {"ingestion": {"choice": "Eventstream", "confidence": "high"}}}
        result = _filter_by_decisions(items, decisions)
        types = [i.item_type for i in result]
        # Lakehouse (non-alternative) should always survive
        assert "Lakehouse" in types
        # At least one ingestion item should survive as fallback
        ingestion_items = [t for t in types if t in ("Copy Job", "Pipeline")]
        assert len(ingestion_items) >= 1, f"All ingestion items lost — got {types}"
