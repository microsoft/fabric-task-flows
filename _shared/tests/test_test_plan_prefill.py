"""Tests for test-plan-prefill.py — verifies test plan pre-fill from architecture handoffs."""

import importlib.util
import sys
from pathlib import Path

import pytest

SHARED_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SHARED_DIR / "lib"))

REPO_ROOT = SHARED_DIR.parent
SCRIPT_PATH = (
    REPO_ROOT / ".github" / "skills" / "fabric-test" / "scripts" / "test-plan-prefill.py"
)

# Import the hyphenated module via importlib
_spec = importlib.util.spec_from_file_location("test_plan_prefill", str(SCRIPT_PATH))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

_parse_frontmatter = _mod._parse_frontmatter
_parse_handoff = _mod._parse_handoff
_load_checklist_phases = _mod._load_checklist_phases
_parse_checklist_phases = _mod._parse_checklist_phases
_detect_item_type = _mod._detect_item_type
_build_test_method = _mod._build_test_method
_build_phase_ref = _mod._build_phase_ref
prefill = _mod.prefill
_emit_yaml = _mod._emit_yaml
PHASE_MAP = _mod.PHASE_MAP


# ── Frontmatter parsing ────────────────────────────────────────────


class TestParseFrontmatter:
    def test_extracts_fields(self):
        text = "---\nproject: My Project\ntask_flow: medallion\n---\n# Body\n"
        fm = _parse_frontmatter(text)
        assert fm["project"] == "My Project"
        assert fm["task_flow"] == "medallion"

    def test_returns_empty_without_frontmatter(self):
        text = "# No frontmatter here\n"
        assert _parse_frontmatter(text) == {}

    def test_strips_quotes(self):
        text = '---\nproject: "Quoted Project"\ntask_flow: \'single\'\n---\n'
        fm = _parse_frontmatter(text)
        assert fm["project"] == "Quoted Project"
        assert fm["task_flow"] == "single"


# ── Handoff parsing ────────────────────────────────────────────────


SAMPLE_HANDOFF_TEXT = """\
---
project: Test Project
task_flow: medallion
created: "2025-01-15"
---

# Architecture Handoff

**Project:** Test Project
**Task Flow:** medallion

```yaml
items_to_deploy:
  - item_name: bronze-lakehouse
    item_type: Lakehouse
  - item_name: transform-notebook
    item_type: Notebook
```

```yaml
acceptance_criteria:
  - ac_id: AC-1
    criterion: bronze-lakehouse Lakehouse exists
    target: bronze-lakehouse
    type: structural
    verification_method: REST API check
  - ac_id: AC-2
    criterion: transform-notebook Notebook exists
    target: transform-notebook
    type: structural
    verification_method: REST API check
```
"""


class TestParseHandoff:
    def test_extracts_project(self):
        result = _parse_handoff(SAMPLE_HANDOFF_TEXT)
        assert result["project"] == "Test Project"

    def test_extracts_task_flow(self):
        result = _parse_handoff(SAMPLE_HANDOFF_TEXT)
        assert result["task_flow"] == "medallion"

    def test_extracts_created(self):
        result = _parse_handoff(SAMPLE_HANDOFF_TEXT)
        assert result["created"] == "2025-01-15"

    def test_extracts_items(self):
        result = _parse_handoff(SAMPLE_HANDOFF_TEXT)
        items = result["items_to_deploy"]
        assert len(items) >= 2
        names = [i.get("name") or i.get("item_name") for i in items]
        assert "bronze-lakehouse" in names

    def test_normalizes_item_keys(self):
        result = _parse_handoff(SAMPLE_HANDOFF_TEXT)
        for item in result["items_to_deploy"]:
            assert "name" in item
            assert "type" in item

    def test_extracts_acceptance_criteria(self):
        result = _parse_handoff(SAMPLE_HANDOFF_TEXT)
        acs = result["acceptance_criteria"]
        assert len(acs) >= 2
        ids = [ac.get("ac_id") or ac.get("id") for ac in acs]
        assert "AC-1" in ids

    def test_fallback_to_markdown_project(self):
        text = "# Handoff\n\n**Project:** Fallback Project\n**Task Flow:** lambda\n"
        text += "\n```yaml\nitems_to_deploy:\n  - item_name: lh\n    item_type: Lakehouse\n```\n"
        result = _parse_handoff(text)
        assert result["project"] == "Fallback Project"
        assert result["task_flow"] == "lambda"


# ── Checklist loading ──────────────────────────────────────────────


class TestLoadChecklistPhases:
    def test_loads_known_task_flow(self):
        phases = _load_checklist_phases("medallion")
        # medallion should have phases defined in the validation-checklists.json
        assert isinstance(phases, dict)

    def test_returns_empty_for_unknown_flow(self):
        phases = _load_checklist_phases("nonexistent-flow-xyz")
        assert phases == {}


class TestParseChecklistPhases:
    def test_parses_phase_headings(self):
        text = (
            "### Phase 1: Foundation\nContent\n"
            "### Phase 2: Ingestion\nContent\n"
            "### Phase 3: Transformation\nContent\n"
        )
        phases = _parse_checklist_phases(text)
        assert phases[1] == "Foundation"
        assert phases[2] == "Ingestion"
        assert phases[3] == "Transformation"

    def test_returns_empty_without_phases(self):
        text = "# No phases here\n"
        assert _parse_checklist_phases(text) == {}


# ── Item type detection ────────────────────────────────────────────


class TestDetectItemType:
    def test_detects_from_target_match(self):
        items = [{"name": "bronze-lh", "type": "Lakehouse"}]
        ac = {"target": "bronze-lh", "criterion": "exists"}
        result = _detect_item_type(ac, items)
        assert result == "Lakehouse"

    def test_detects_from_text_scan(self):
        items = []
        ac = {"criterion": "Notebook exists in workspace", "target": "", "verify": ""}
        result = _detect_item_type(ac, items)
        assert result == "Notebook"

    def test_returns_none_for_no_match(self):
        items = []
        ac = {"criterion": "something generic", "target": "", "verify": "", "type": ""}
        result = _detect_item_type(ac, items)
        assert result is None


# ── Test method building ───────────────────────────────────────────


class TestBuildTestMethod:
    def test_data_flow_type(self):
        ac = {"type": "data-flow"}
        ac_type, method, note = _build_test_method(ac, "Lakehouse", [])
        assert ac_type == "data-flow"
        assert "connections configured" in method

    def test_unknown_item_type(self):
        ac = {"verify": "check manually"}
        ac_type, method, note = _build_test_method(ac, None, [])
        assert method == "check manually"

    def test_known_item_type_generates_api_method(self):
        ac = {"criterion": "exists", "verify": "", "type": "structural"}
        ac_type, method, note = _build_test_method(ac, "Lakehouse", [])
        assert "GET" in method or "verify" in method.lower()


# ── Phase reference building ───────────────────────────────────────


class TestBuildPhaseRef:
    def test_format(self):
        ref = _build_phase_ref(1, "Foundation")
        assert ref == "Phase 1: Foundation"

    def test_different_numbers(self):
        ref = _build_phase_ref(3, "Transformation")
        assert ref == "Phase 3: Transformation"


# ── PHASE_MAP ──────────────────────────────────────────────────────


class TestPhaseMap:
    def test_lakehouse_in_phase_map(self):
        assert "Lakehouse" in PHASE_MAP

    def test_phase_map_returns_tuple(self):
        phase_name, phase_order = PHASE_MAP["Lakehouse"]
        assert isinstance(phase_name, str)
        assert isinstance(phase_order, int)


# ── YAML output ────────────────────────────────────────────────────


class TestEmitYaml:
    def _sample_data(self):
        return {
            "project": "Test",
            "task_flow": "medallion",
            "architecture_date": "2025-01-15",
            "test_plan_date": "2025-01-20",
            "scan_type": "automated",
            "criteria_mapping": [
                {
                    "ac_id": "AC-1",
                    "type": "structural",
                    "phase": "Phase 1: Foundation",
                    "test_method": "GET /workspaces/{id}/lakehouses",
                },
            ],
            "critical_verification": ["Storage items exist"],
            "edge_cases": ["LLM: Add failure scenarios"],
            "blockers": {"architecture": [], "deployment": []},
        }

    def test_contains_project(self):
        yaml = _emit_yaml(self._sample_data())
        assert 'project: "Test"' in yaml

    def test_contains_criteria_mapping(self):
        yaml = _emit_yaml(self._sample_data())
        assert "criteria_mapping:" in yaml
        assert "ac_id: AC-1" in yaml

    def test_contains_critical_verification(self):
        yaml = _emit_yaml(self._sample_data())
        assert "critical_verification:" in yaml
        assert "Storage items exist" in yaml

    def test_contains_blockers(self):
        yaml = _emit_yaml(self._sample_data())
        assert "blockers:" in yaml
        assert "architecture: []" in yaml

    def test_empty_criteria_mapping(self):
        data = self._sample_data()
        data["criteria_mapping"] = []
        yaml = _emit_yaml(data)
        assert "criteria_mapping:" in yaml


# ── Prefill integration ────────────────────────────────────────────


class TestPrefill:
    def test_returns_dict_with_required_keys(self, tmp_path):
        handoff = tmp_path / "architecture-handoff.md"
        handoff.write_text(SAMPLE_HANDOFF_TEXT, encoding="utf-8")
        result = prefill(str(handoff))
        assert "project" in result
        assert "task_flow" in result
        assert "criteria_mapping" in result
        assert "critical_verification" in result
        assert "edge_cases" in result
        assert "blockers" in result

    def test_extracts_project_and_task_flow(self, tmp_path):
        handoff = tmp_path / "architecture-handoff.md"
        handoff.write_text(SAMPLE_HANDOFF_TEXT, encoding="utf-8")
        result = prefill(str(handoff))
        assert result["project"] == "Test Project"
        assert result["task_flow"] == "medallion"

    def test_criteria_mapping_populated(self, tmp_path):
        handoff = tmp_path / "architecture-handoff.md"
        handoff.write_text(SAMPLE_HANDOFF_TEXT, encoding="utf-8")
        result = prefill(str(handoff))
        assert len(result["criteria_mapping"]) > 0
        for entry in result["criteria_mapping"]:
            assert "ac_id" in entry
            assert "type" in entry
            assert "test_method" in entry

    def test_scan_type_automated(self, tmp_path):
        handoff = tmp_path / "architecture-handoff.md"
        handoff.write_text(SAMPLE_HANDOFF_TEXT, encoding="utf-8")
        result = prefill(str(handoff))
        assert result["scan_type"] == "automated"

    def test_nonexistent_file_exits(self, tmp_path):
        with pytest.raises(SystemExit):
            prefill(str(tmp_path / "nonexistent.md"))
