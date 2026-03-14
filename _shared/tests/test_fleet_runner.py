"""Tests for fleet-runner.py — verifies problem parsing, discovery brief
generation, result structure, and fleet summary formatting."""

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SHARED_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SHARED_DIR.parent
SCRIPT_PATH = SHARED_DIR / "scripts" / "fleet-runner.py"

# Ensure lib is importable (fleet-runner.py depends on new-project.py which
# imports text_utils from _shared/lib).
sys.path.insert(0, str(SHARED_DIR / "lib"))
sys.path.insert(0, str(SHARED_DIR / "scripts"))


def _load_module():
    """Dynamically load fleet-runner.py (hyphenated name requires importlib)."""
    spec = importlib.util.spec_from_file_location("fleet_runner", str(SCRIPT_PATH))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["fleet_runner"] = mod
    spec.loader.exec_module(mod)
    return mod


fr = _load_module()


# ── Module-level sanity ──────────────────────────────────────────────────


def test_module_loads():
    """fleet-runner.py should import without errors."""
    assert fr is not None


def test_module_has_expected_functions():
    """Module exposes the key public functions."""
    for name in (
        "parse_problem_file",
        "run_signal_mapper",
        "generate_discovery_brief",
        "process_project",
        "print_fleet_summary",
        "update_projects_md",
    ):
        assert hasattr(fr, name), f"Missing function: {name}"


# ── parse_problem_file ───────────────────────────────────────────────────


class TestParseProblemFile:
    """Verify problem-statements.md parsing."""

    def test_parses_numbered_problems(self, tmp_path):
        """Numbered items under ## headings should be parsed."""
        md = tmp_path / "problems.md"
        md.write_text(
            '## IoT\n'
            '1. "Sensor data from 500 factories needs real-time monitoring"\n'
            '2. "Temperature alerts must fire within 5 seconds"\n'
            '## Batch\n'
            '3. "Nightly sales aggregation across 12 regions"\n',
            encoding="utf-8",
        )
        result = fr.parse_problem_file(str(md))
        assert len(result) == 3
        assert result[0]["category"] == "IoT"
        assert result[0]["id"] == 1
        assert "500 factories" in result[0]["text"]
        assert result[2]["category"] == "Batch"

    def test_empty_file_returns_empty_list(self, tmp_path):
        """An empty markdown file should produce no problems."""
        md = tmp_path / "empty.md"
        md.write_text("", encoding="utf-8")
        result = fr.parse_problem_file(str(md))
        assert result == []

    def test_no_numbered_items(self, tmp_path):
        """File with headings but no numbered items returns empty."""
        md = tmp_path / "headings.md"
        md.write_text("## Category A\nSome text\n## Category B\n", encoding="utf-8")
        result = fr.parse_problem_file(str(md))
        assert result == []

    def test_problem_has_name_field(self, tmp_path):
        """Each parsed problem should have a kebab-case name."""
        md = tmp_path / "p.md"
        md.write_text(
            '## Analytics\n1. "Build a dashboard for sales"\n',
            encoding="utf-8",
        )
        result = fr.parse_problem_file(str(md))
        assert len(result) == 1
        name = result[0]["name"]
        assert name == name.lower()
        assert " " not in name

    def test_problem_ids_are_sequential(self, tmp_path):
        """IDs should be 1-based sequential integers."""
        md = tmp_path / "seq.md"
        md.write_text(
            '## A\n1. "First"\n2. "Second"\n3. "Third"\n',
            encoding="utf-8",
        )
        result = fr.parse_problem_file(str(md))
        ids = [p["id"] for p in result]
        assert ids == [1, 2, 3]

    def test_display_name_field(self, tmp_path):
        """Each problem should carry a display_name."""
        md = tmp_path / "dn.md"
        md.write_text('## CatX\n1. "Problem text"\n', encoding="utf-8")
        result = fr.parse_problem_file(str(md))
        assert "display_name" in result[0]
        assert "CatX" in result[0]["display_name"]


# ── generate_discovery_brief ─────────────────────────────────────────────


class TestGenerateDiscoveryBrief:
    """Verify deterministic discovery brief generation."""

    @pytest.fixture()
    def problem(self):
        return {
            "id": 1,
            "name": "test-project",
            "category": "IoT",
            "text": "Sensor data from 500 factories needs real-time monitoring",
            "display_name": "Test Project",
        }

    @pytest.fixture()
    def signals(self):
        return {
            "signals": [
                {"category": "Velocity", "value": "Real-time"},
                {"category": "Use-Case", "value": "IoT"},
            ],
            "task_flow_candidates": [
                {"id": "iot-streaming", "signals": ["velocity", "iot"]},
                {"id": "lambda", "signals": ["mixed"]},
            ],
            "primary_velocity": "real-time",
            "keyword_coverage": 0.25,
        }

    def test_brief_contains_problem_text(self, problem, signals):
        brief = fr.generate_discovery_brief(problem, signals)
        assert problem["text"] in brief

    def test_brief_contains_project_name(self, problem, signals):
        brief = fr.generate_discovery_brief(problem, signals)
        assert problem["name"] in brief

    def test_brief_contains_candidates(self, problem, signals):
        brief = fr.generate_discovery_brief(problem, signals)
        assert "iot-streaming" in brief

    def test_brief_with_empty_signals(self, problem):
        empty = {
            "signals": [],
            "task_flow_candidates": [],
            "primary_velocity": "unknown",
            "keyword_coverage": 0,
        }
        brief = fr.generate_discovery_brief(problem, empty)
        assert "Discovery Brief" in brief
        assert "basic-data-analytics" in brief  # default fallback

    def test_brief_velocity_confidence(self, problem, signals):
        """High keyword_coverage (>0.1) → high confidence."""
        brief = fr.generate_discovery_brief(problem, signals)
        assert "high" in brief.lower()

    def test_brief_low_coverage_medium_confidence(self, problem):
        low_cov = {
            "signals": [],
            "task_flow_candidates": [],
            "primary_velocity": "batch",
            "keyword_coverage": 0.05,
        }
        brief = fr.generate_discovery_brief(problem, low_cov)
        # velocity confidence should be medium
        lines = [l for l in brief.splitlines() if "Data Velocity" in l]
        assert len(lines) == 1
        assert "medium" in lines[0]


# ── process_project result structure ─────────────────────────────────────


class TestProcessProjectResult:
    """Verify the result dict structure from process_project (dry-run)."""

    def test_dry_run_result_keys(self, monkeypatch):
        """Dry-run result should contain all expected keys."""
        monkeypatch.setattr(fr, "run_signal_mapper", lambda text: None)
        problem = {
            "id": 42,
            "name": "dry-test",
            "category": "Test",
            "text": "Some problem",
            "display_name": "Dry Test",
        }
        result = fr.process_project(problem, dry_run=True)
        for key in ("id", "name", "category", "status",
                     "task_flow_candidates", "signals_matched",
                     "keyword_coverage", "error"):
            assert key in result, f"Missing key: {key}"

    def test_dry_run_status(self, monkeypatch):
        """Dry-run should set status to 'dry-run'."""
        monkeypatch.setattr(fr, "run_signal_mapper", lambda text: None)
        problem = {
            "id": 1, "name": "x", "category": "C",
            "text": "t", "display_name": "X",
        }
        result = fr.process_project(problem, dry_run=True)
        assert result["status"] == "dry-run"


# ── print_fleet_summary ─────────────────────────────────────────────────


class TestPrintFleetSummary:
    """Verify summary output doesn't crash on edge cases."""

    def test_empty_results(self, capsys):
        """Empty result list should not raise."""
        fr.print_fleet_summary([])
        out = capsys.readouterr().out
        assert "FLEET DEPLOYMENT SUMMARY" in out

    def test_summary_with_results(self, capsys):
        results = [
            {"id": 1, "name": "proj-a", "category": "IoT",
             "status": "dry-run", "task_flow_candidates": ["iot-streaming"],
             "signals_matched": 3, "keyword_coverage": 0.2, "error": None},
            {"id": 2, "name": "proj-b", "category": "Batch",
             "status": "scaffold-failed", "task_flow_candidates": [],
             "signals_matched": 0, "keyword_coverage": 0, "error": "oops"},
        ]
        fr.print_fleet_summary(results)
        out = capsys.readouterr().out
        assert "proj-a" in out
        assert "proj-b" in out
        assert "Success: 1" in out
        assert "Failed: 1" in out


# ── update_projects_md ───────────────────────────────────────────────────


class TestUpdateProjectsMd:
    """Verify PROJECTS.md update logic."""

    def test_skips_already_present(self, tmp_path, monkeypatch, capsys):
        """Projects already in PROJECTS.md should not be duplicated."""
        monkeypatch.setattr(fr, "REPO_ROOT", tmp_path)
        pm = tmp_path / "PROJECTS.md"
        pm.write_text("| existing-proj | … |\n> Project rows\n", encoding="utf-8")
        results = [
            {"id": 1, "name": "existing-proj", "category": "C",
             "status": "discovery-complete", "task_flow_candidates": ["x"]},
        ]
        fr.update_projects_md(results)
        content = pm.read_text(encoding="utf-8")
        assert content.count("existing-proj") == 1  # no duplicate

    def test_inserts_new_project(self, tmp_path, monkeypatch):
        """New projects should be appended before the marker."""
        monkeypatch.setattr(fr, "REPO_ROOT", tmp_path)
        pm = tmp_path / "PROJECTS.md"
        pm.write_text("# Projects\n\n> Project rows\n", encoding="utf-8")
        results = [
            {"id": 1, "name": "brand-new", "category": "IoT",
             "status": "discovery-complete",
             "task_flow_candidates": ["iot-streaming"]},
        ]
        fr.update_projects_md(results)
        content = pm.read_text(encoding="utf-8")
        assert "brand-new" in content
