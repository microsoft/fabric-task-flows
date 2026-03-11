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
