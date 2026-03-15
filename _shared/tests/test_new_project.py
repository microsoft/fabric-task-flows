"""Tests for new-project.py — verifies name sanitisation, scaffold structure,
template content, pipeline state, and PROJECTS.md updates."""

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

SHARED_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SHARED_DIR.parent
SCRIPT_PATH = SHARED_DIR / "scripts" / "new-project.py"

# Ensure _shared/lib is importable (new-project.py imports text_utils).
sys.path.insert(0, str(SHARED_DIR / "lib"))


def _load_module():
    """Dynamically load new-project.py (hyphenated name requires importlib)."""
    spec = importlib.util.spec_from_file_location("new_project", str(SCRIPT_PATH))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["new_project"] = mod
    spec.loader.exec_module(mod)
    return mod


np = _load_module()


# ── sanitize_name ────────────────────────────────────────────────────────


class TestSanitizeName:
    """Verify kebab-case conversion rules."""

    def test_basic_conversion(self):
        assert np.sanitize_name("Energy Field Intelligence") == "energy-field-intelligence"

    def test_strips_special_chars(self):
        result = np.sanitize_name("My Project! (v2)")
        assert "!" not in result
        assert "(" not in result
        assert ")" not in result

    def test_lowercase(self):
        assert np.sanitize_name("LOUD NAME") == "loud-name"

    def test_collapses_whitespace(self):
        result = np.sanitize_name("  hello   world  ")
        assert result == "hello-world"

    def test_empty_string(self):
        result = np.sanitize_name("")
        assert result == ""

    def test_already_kebab(self):
        assert np.sanitize_name("already-kebab") == "already-kebab"

    def test_numbers_preserved(self):
        result = np.sanitize_name("Project 42")
        assert "42" in result


# ── today() ──────────────────────────────────────────────────────────────


def test_today_format():
    """today() should return YYYY-MM-DD."""
    import re
    assert re.match(r"\d{4}-\d{2}-\d{2}", np.today())


# ── Template generators ─────────────────────────────────────────────────


class TestTemplateGenerators:
    """Verify template content for all template functions."""

    def test_discovery_brief_contains_project(self):
        brief = np.discovery_brief("my-proj")
        assert "my-proj" in brief
        assert "Discovery Brief" in brief

    def test_architecture_handoff_yaml_frontmatter(self):
        doc = np.architecture_handoff("test-proj")
        assert doc.startswith("---")
        assert "project: test-proj" in doc

    def test_engineer_review_contains_project(self):
        doc = np.engineer_review("proj-x")
        assert "proj-x" in doc
        assert "Engineer Review" in doc

    def test_tester_review_contains_project(self):
        doc = np.tester_review("proj-y")
        assert "proj-y" in doc
        assert "Tester Review" in doc

    def test_test_plan_contains_project(self):
        doc = np.test_plan("proj-z")
        assert "proj-z" in doc
        assert "Test Plan" in doc

    def test_deployment_handoff_contains_project(self):
        doc = np.deployment_handoff("dep-proj")
        assert "dep-proj" in doc
        assert "Deployment Handoff" in doc

    def test_validation_report_phases(self):
        doc = np.validation_report("val-proj")
        for phase in ("Foundation", "Ingestion", "Transformation", "Visualization"):
            assert phase in doc

    def test_status_md_display_name(self):
        doc = np.status_md("my-proj", "My Project")
        assert "My Project" in doc
        assert "my-proj" in doc


# ── pipeline_state ───────────────────────────────────────────────────────


class TestPipelineState:
    """Verify pipeline-state.json structure."""

    def test_valid_json(self):
        raw = np.pipeline_state("test")
        state = json.loads(raw)
        assert isinstance(state, dict)

    def test_initial_phase(self):
        state = json.loads(np.pipeline_state("test"))
        assert state["current_phase"] == "0a-discovery"

    def test_all_phases_present(self):
        state = json.loads(np.pipeline_state("test"))
        expected = {
            "0a-discovery", "1-design", "2a-test-plan",
            "2b-sign-off", "2c-deploy", "3-validate", "4-document",
        }
        assert set(state["phases"].keys()) == expected

    def test_transitions_list(self):
        state = json.loads(np.pipeline_state("test"))
        assert isinstance(state["transitions"], list)
        assert len(state["transitions"]) >= 5

    def test_project_name_embedded(self):
        state = json.loads(np.pipeline_state("cool-proj"))
        assert state["project"] == "cool-proj"


# ── scaffold ─────────────────────────────────────────────────────────────


class TestScaffold:
    """Verify full project scaffolding creates expected tree."""

    def test_creates_directory_tree(self, tmp_path):
        (tmp_path / "task-flows.md").touch()

        np.scaffold(str(tmp_path), "Test Scaffold")

        project_dir = tmp_path / "_projects" / "test-scaffold"
        assert project_dir.is_dir()
        assert (project_dir / "docs").is_dir()
        assert (project_dir / "deploy").is_dir()

    def test_creates_template_files(self, tmp_path):
        np.scaffold(str(tmp_path), "File Check")

        proj = tmp_path / "_projects" / "file-check"
        expected_files = [
            "docs/discovery-brief.md",
            "docs/architecture-handoff.md",
            "pipeline-state.json",
        ]
        for rel in expected_files:
            assert (proj / rel).exists(), f"Missing: {rel}"

    def test_pipeline_state_is_valid_json(self, tmp_path):
        np.scaffold(str(tmp_path), "Json Test")

        state_path = tmp_path / "_projects" / "json-test" / "pipeline-state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        assert state["project"] == "json-test"

    def test_existing_directory_exits(self, tmp_path):
        """scaffold should sys.exit(1) if project directory already exists."""
        proj_dir = tmp_path / "_projects" / "dup-proj"
        proj_dir.mkdir(parents=True)

        with pytest.raises(SystemExit):
            np.scaffold(str(tmp_path), "Dup Proj")

    def test_pipeline_state_content(self, tmp_path):
        np.scaffold(str(tmp_path), "Status Demo")

        state = (tmp_path / "_projects" / "status-demo" / "pipeline-state.json").read_text(
            encoding="utf-8"
        )
        assert "status-demo" in state
        assert "0a-discovery" in state


# ── update_projects_md ───────────────────────────────────────────────────


class TestUpdateProjectsMd:
    """Verify PROJECTS.md row insertion."""

    def test_adds_new_row(self, tmp_path):
        pm = tmp_path / "PROJECTS.md"
        pm.write_text("# Projects\n\n> Project rows\n", encoding="utf-8")
        np.update_projects_md(str(tmp_path), "new-proj")
        content = pm.read_text(encoding="utf-8")
        assert "new-proj" in content

    def test_skips_duplicate(self, tmp_path, capsys):
        pm = tmp_path / "PROJECTS.md"
        pm.write_text("| existing |\n> Project rows\n", encoding="utf-8")
        np.update_projects_md(str(tmp_path), "existing")
        out = capsys.readouterr().out
        assert "already exists" in out

    def test_missing_projects_md(self, tmp_path, capsys):
        """Should print a warning and not crash."""
        np.update_projects_md(str(tmp_path), "ghost")
        out = capsys.readouterr().out
        assert "not found" in out
