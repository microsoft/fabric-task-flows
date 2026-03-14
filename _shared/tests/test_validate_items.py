"""Tests for validate-items.py — verifies config checklist generation."""

import importlib.util
import sys
import types
from pathlib import Path

SHARED_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SHARED_DIR / "lib"))

REPO_ROOT = SHARED_DIR.parent
SCRIPT_PATH = (
    REPO_ROOT / ".github" / "skills" / "fabric-test" / "scripts" / "validate-items.py"
)

# Now import the module
_spec = importlib.util.spec_from_file_location("validate_items", str(SCRIPT_PATH))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

_parse_handoff = _mod._parse_handoff
_load_validation_checklists = _mod._load_validation_checklists
_get_manual_steps = _mod._get_manual_steps


# ── Sample handoff data ───────────────────────────────────────────

SAMPLE_DEPLOYMENT_HANDOFF = """\
# Deployment Handoff

project: "Test Project"
task_flow: "medallion"
workspace: "test-workspace-dev"

items_deployed:
  - name: bronze-lakehouse
    type: Lakehouse
    wave: 1
    status: deployed
  - name: transform-notebook
    type: Notebook
    wave: 2
    status: deployed
  - name: analytics-report
    type: Report
    wave: 3
    status: deployed
"""

INLINE_DEPLOYMENT_HANDOFF = """\
project: "Inline Test"
task_flow: "lambda"
workspace: "inline-ws"

items:
  - { name: lh-bronze, type: Lakehouse, wave: 1, status: deployed }
  - { name: nb-silver, type: Notebook, wave: 2, status: deployed }
"""


# ── _parse_handoff tests ──────────────────────────────────────────


class TestParseHandoff:
    def test_parses_multiline_format(self, tmp_path):
        p = tmp_path / "handoff.md"
        p.write_text(SAMPLE_DEPLOYMENT_HANDOFF)
        project, task_flow, workspace, items = _parse_handoff(str(p))

        assert project == "Test Project"
        assert task_flow == "medallion"
        assert workspace == "test-workspace-dev"
        assert len(items) == 3

    def test_parses_inline_format(self, tmp_path):
        p = tmp_path / "handoff.md"
        p.write_text(INLINE_DEPLOYMENT_HANDOFF)
        project, task_flow, workspace, items = _parse_handoff(str(p))

        assert project == "Inline Test"
        assert task_flow == "lambda"
        assert workspace == "inline-ws"
        assert len(items) == 2

    def test_extracts_item_details(self, tmp_path):
        p = tmp_path / "handoff.md"
        p.write_text(SAMPLE_DEPLOYMENT_HANDOFF)
        _, _, _, items = _parse_handoff(str(p))

        assert items[0]["name"] == "bronze-lakehouse"
        assert items[0]["type"] == "Lakehouse"
        assert items[0]["wave"] == "1"
        assert items[0]["status"] == "deployed"

    def test_handles_inline_items(self, tmp_path):
        p = tmp_path / "handoff.md"
        p.write_text(INLINE_DEPLOYMENT_HANDOFF)
        _, _, _, items = _parse_handoff(str(p))

        assert items[0]["name"] == "lh-bronze"
        assert items[0]["type"] == "Lakehouse"

    def test_empty_file_returns_empty_items(self, tmp_path):
        p = tmp_path / "empty.md"
        p.write_text("# Empty handoff\n")
        project, task_flow, workspace, items = _parse_handoff(str(p))

        assert items == []


# ── _load_validation_checklists tests ─────────────────────────────


class TestLoadValidationChecklists:
    def test_loads_checklists(self):
        checklists = _load_validation_checklists()
        # Should load successfully from registry
        assert isinstance(checklists, dict)

    def test_has_task_flows_key(self):
        checklists = _load_validation_checklists()
        if checklists:  # Only test if file exists
            assert "task_flows" in checklists or checklists == {}


# ── _get_manual_steps tests ───────────────────────────────────────


class TestGetManualSteps:
    def test_returns_empty_for_unknown_task_flow(self):
        checklists = {"task_flows": {}}
        result = _get_manual_steps("nonexistent", checklists)
        assert result == []

    def test_returns_manual_steps_for_known_task_flow(self):
        checklists = {
            "task_flows": {
                "medallion": {
                    "manual_steps": [
                        {"item_type": "Lakehouse", "action": "Create tables"}
                    ]
                }
            }
        }
        result = _get_manual_steps("medallion", checklists)
        assert len(result) == 1
        assert result[0]["item_type"] == "Lakehouse"

    def test_handles_missing_manual_steps_key(self):
        checklists = {"task_flows": {"medallion": {}}}
        result = _get_manual_steps("medallion", checklists)
        assert result == []


# ── Integration test ──────────────────────────────────────────────


class TestIntegration:
    def test_script_can_be_imported(self):
        """Verify the script imports without errors."""
        assert _parse_handoff is not None
        assert _load_validation_checklists is not None
        assert _get_manual_steps is not None


# ══════════════════════════════════════════════════════════════════════════════
# NEW TESTS — _parse_handoff edge cases
# ══════════════════════════════════════════════════════════════════════════════

MIXED_HANDOFF = """\
project: "Mixed"
task_flow: "event-analytics"
workspace: "mixed-ws"

items_deployed:
  - { name: evs-ingest, type: Eventstream, wave: 1, status: deployed }
  - name: kql-db
    type: KQLDatabase
    wave: 2
    status: deployed
"""

MINIMAL_HANDOFF = """\
project: "Mini"
task_flow: "medallion"
workspace: "mini-ws"

items:
  - name: lh-only
    type: Lakehouse
    wave: 1
"""

NO_METADATA_HANDOFF = """\
items_deployed:
  - { name: orphan-nb, type: Notebook, wave: 1 }
"""

HANDOFF_WITH_ITEM_TYPE_ALIASES = """\
project: "Alias"
task_flow: "medallion"
workspace: "alias-ws"

items:
  - item_name: aliased-lh
    item_type: Lakehouse
    wave: 1
    status: deployed
"""

DUPLICATE_NAMES_HANDOFF = """\
project: "Dups"
task_flow: "medallion"
workspace: "dup-ws"

items:
  - name: shared-name
    type: Lakehouse
    wave: 1
  - name: shared-name
    type: Notebook
    wave: 2
"""


class TestParseHandoffEdgeCases:
    def test_mixed_inline_and_multiline(self, tmp_path):
        p = tmp_path / "handoff.md"
        p.write_text(MIXED_HANDOFF)
        project, task_flow, workspace, items = _parse_handoff(str(p))
        assert project == "Mixed"
        assert task_flow == "event-analytics"
        assert len(items) == 2

    def test_minimal_handoff(self, tmp_path):
        p = tmp_path / "handoff.md"
        p.write_text(MINIMAL_HANDOFF)
        project, task_flow, workspace, items = _parse_handoff(str(p))
        assert project == "Mini"
        assert len(items) == 1
        assert items[0]["name"] == "lh-only"

    def test_default_status_is_deployed(self, tmp_path):
        p = tmp_path / "handoff.md"
        p.write_text(MINIMAL_HANDOFF)
        _, _, _, items = _parse_handoff(str(p))
        assert items[0]["status"] == "deployed"

    def test_no_metadata(self, tmp_path):
        p = tmp_path / "handoff.md"
        p.write_text(NO_METADATA_HANDOFF)
        project, task_flow, workspace, items = _parse_handoff(str(p))
        assert project == ""
        assert task_flow == ""
        assert workspace == ""
        assert len(items) == 1

    def test_item_name_aliases(self, tmp_path):
        p = tmp_path / "handoff.md"
        p.write_text(HANDOFF_WITH_ITEM_TYPE_ALIASES)
        _, _, _, items = _parse_handoff(str(p))
        assert items[0]["name"] == "aliased-lh"
        assert items[0]["type"] == "Lakehouse"

    def test_duplicate_names_both_parsed(self, tmp_path):
        p = tmp_path / "handoff.md"
        p.write_text(DUPLICATE_NAMES_HANDOFF)
        _, _, _, items = _parse_handoff(str(p))
        assert len(items) == 2
        types = {item["type"] for item in items}
        assert types == {"Lakehouse", "Notebook"}


# ══════════════════════════════════════════════════════════════════════════════
# NEW TESTS — _get_manual_steps more cases
# ══════════════════════════════════════════════════════════════════════════════


class TestGetManualStepsExtended:
    def test_returns_empty_for_empty_checklists(self):
        result = _get_manual_steps("medallion", {})
        assert result == []

    def test_multiple_steps(self):
        checklists = {
            "task_flows": {
                "medallion": {
                    "manual_steps": [
                        {"item_type": "Lakehouse", "action": "Create tables"},
                        {"item_type": "Notebook", "action": "Attach environment"},
                        {"item_type": "Report", "action": "Set data source"},
                    ]
                }
            }
        }
        result = _get_manual_steps("medallion", checklists)
        assert len(result) == 3

    def test_returns_empty_list_not_none(self):
        checklists = {"task_flows": {"medallion": {"manual_steps": []}}}
        result = _get_manual_steps("medallion", checklists)
        assert result == []
        assert result is not None


# ══════════════════════════════════════════════════════════════════════════════
# NEW TESTS — _load_validation_checklists edge cases
# ══════════════════════════════════════════════════════════════════════════════


class TestLoadValidationChecklistsExtended:
    def test_returns_dict(self):
        result = _load_validation_checklists()
        assert isinstance(result, dict)

    def test_task_flows_values_are_dicts(self):
        checklists = _load_validation_checklists()
        if checklists and "task_flows" in checklists:
            for tf_name, tf_data in checklists["task_flows"].items():
                assert isinstance(tf_data, dict), \
                    f"task_flow '{tf_name}' value should be a dict"


# ══════════════════════════════════════════════════════════════════════════════
# NEW TESTS — Malformed/edge input to _parse_handoff
# ══════════════════════════════════════════════════════════════════════════════


class TestParseHandoffMalformed:
    def test_only_comments(self, tmp_path):
        p = tmp_path / "handoff.md"
        p.write_text("# Just a comment\n## Another comment\n")
        _, _, _, items = _parse_handoff(str(p))
        assert items == []

    def test_items_keyword_but_no_entries(self, tmp_path):
        p = tmp_path / "handoff.md"
        p.write_text("items_deployed:\n\nsome_other_section: true\n")
        _, _, _, items = _parse_handoff(str(p))
        assert items == []

    def test_metadata_with_extra_whitespace(self, tmp_path):
        content = '  project:   "Spaced"  \n  task_flow:   medallion  \n'
        p = tmp_path / "handoff.md"
        p.write_text(content)
        project, task_flow, _, _ = _parse_handoff(str(p))
        assert project == "Spaced"
        assert task_flow == "medallion"

    def test_inline_status_override(self, tmp_path):
        content = """\
items_deployed:
  - { name: failed-item, type: Notebook, wave: 1, status: failed }
"""
        p = tmp_path / "handoff.md"
        p.write_text(content)
        _, _, _, items = _parse_handoff(str(p))
        assert len(items) == 1
        assert items[0]["status"] == "failed"
