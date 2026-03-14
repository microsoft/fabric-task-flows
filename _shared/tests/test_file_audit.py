"""Tests for _shared/scripts/file-audit.py."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

# ── import hyphenated module via importlib (project convention) ───────────────
SHARED_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SHARED_DIR.parent
SCRIPT_PATH = SHARED_DIR / "scripts" / "file-audit.py"

spec = importlib.util.spec_from_file_location("file_audit", str(SCRIPT_PATH))
file_audit = importlib.util.module_from_spec(spec)
sys.modules["file_audit"] = file_audit
spec.loader.exec_module(file_audit)

FileMetrics = file_audit.FileMetrics
categorize = file_audit.categorize
categorize_path = file_audit.categorize_path
scan_repo = file_audit.scan_repo


# ── categorize_path ──────────────────────────────────────────────────────────


class TestCategorizePath:
    def test_copilot_instructions(self):
        assert categorize_path(".github/copilot-instructions.md") == "copilot-instructions"

    def test_agent_instructions(self):
        assert categorize_path(".github/agents/fabric-advisor.agent.md") == "agent-instructions"

    def test_skill_instructions(self):
        assert categorize_path(".github/skills/fabric-deploy/SKILL.md") == "skill-instructions"

    def test_skill_references(self):
        assert (
            categorize_path(".github/skills/fabric-deploy/references/cicd-reference.md")
            == "skill-references"
        )

    def test_skill_schemas(self):
        assert (
            categorize_path(".github/skills/fabric-test/schemas/test-plan.md")
            == "skill-schemas"
        )

    def test_skill_scripts(self):
        assert (
            categorize_path(".github/skills/fabric-deploy/scripts/deploy-script-gen.py")
            == "skill-scripts"
        )

    def test_decision_guides(self):
        assert categorize_path("decisions/storage-selection.md") == "decision-guides"

    def test_diagrams(self):
        assert categorize_path("diagrams/medallion.md") == "diagrams"

    def test_registry_data(self):
        assert categorize_path("_shared/registry/deployment-order.json") == "registry-data"

    def test_workflow_guide(self):
        assert categorize_path("_shared/workflow-guide.md") == "workflow-guide"

    def test_shared_lib(self):
        assert categorize_path("_shared/lib/text_utils.py") == "shared-lib"

    def test_shared_scripts(self):
        assert categorize_path("_shared/scripts/run-pipeline.py") == "shared-scripts"

    def test_shared_tests(self):
        assert categorize_path("_shared/tests/test_file_audit.py") == "shared-tests"

    def test_project_docs(self):
        assert (
            categorize_path("_projects/football-intelligence/docs/architecture-handoff.md")
            == "project-docs"
        )

    def test_heal_batches(self):
        assert (
            categorize_path(".github/skills/fabric-heal/problem-statements-batch1.md")
            == "heal-batches"
        )

    def test_fallback_other(self):
        assert categorize_path("README.md") == "other"
        assert categorize_path("CHANGELOG.md") == "other"

    def test_backslash_normalisation(self):
        """Windows-style paths should still categorise correctly."""
        assert categorize_path("decisions\\storage-selection.md") == "decision-guides"
        assert (
            categorize_path(".github\\skills\\fabric-deploy\\SKILL.md")
            == "skill-instructions"
        )


# ── FileMetrics ──────────────────────────────────────────────────────────────


class TestFileMetrics:
    def test_size_kb(self):
        m = FileMetrics(path="a.md", size_bytes=15360, chars=10000, lines=200, category="other")
        assert m.size_kb == 15.0

    def test_size_kb_rounding(self):
        m = FileMetrics(path="b.md", size_bytes=1500, chars=500, lines=10, category="other")
        assert m.size_kb == 1.5


# ── scan_repo ────────────────────────────────────────────────────────────────


class TestScanRepo:
    def test_scan_finds_files(self, tmp_path: Path):
        """scan_repo should find files with matching extensions."""
        (tmp_path / "a.md").write_text("hello world", encoding="utf-8")
        (tmp_path / "b.json").write_text('{"k": 1}', encoding="utf-8")
        (tmp_path / "c.txt").write_text("ignored", encoding="utf-8")

        results = scan_repo(tmp_path, extensions={".md", ".json"})
        paths = {r.path for r in results}
        assert "a.md" in paths
        assert "b.json" in paths
        assert "c.txt" not in paths

    def test_scan_metrics_accuracy(self, tmp_path: Path):
        """Verify size, chars, and lines are accurate."""
        content = "line one\nline two\nline three\n"
        # Write binary to avoid OS newline translation affecting size
        (tmp_path / "test.md").write_bytes(content.encode("utf-8"))

        results = scan_repo(tmp_path, extensions={".md"})
        assert len(results) == 1
        m = results[0]
        assert m.chars == len(content)
        assert m.lines == 3
        assert m.size_bytes == len(content.encode("utf-8"))

    def test_scan_skips_hidden_dirs(self, tmp_path: Path):
        """Hidden directories (except .github) should be skipped."""
        hidden = tmp_path / ".hidden"
        hidden.mkdir()
        (hidden / "secret.md").write_text("secret", encoding="utf-8")

        github = tmp_path / ".github"
        github.mkdir()
        (github / "config.md").write_text("config", encoding="utf-8")

        results = scan_repo(tmp_path, extensions={".md"})
        paths = {r.path for r in results}
        assert ".github\\config.md" in paths or ".github/config.md" in paths
        assert not any("hidden" in p for p in paths)

    def test_scan_respects_extensions(self, tmp_path: Path):
        """Only specified extensions should be included."""
        (tmp_path / "a.md").write_text("md", encoding="utf-8")
        (tmp_path / "b.py").write_text("py", encoding="utf-8")

        results = scan_repo(tmp_path, extensions={".md"})
        assert len(results) == 1
        assert results[0].path == "a.md"


# ── categorize ───────────────────────────────────────────────────────────────


class TestCategorize:
    def test_groups_and_sorts(self):
        files = [
            FileMetrics("decisions/a.md", 100, 100, 10, "decision-guides"),
            FileMetrics("decisions/b.md", 500, 500, 50, "decision-guides"),
            FileMetrics("diagrams/x.md", 200, 200, 20, "diagrams"),
        ]
        grouped = categorize(files)
        assert set(grouped.keys()) == {"decision-guides", "diagrams"}
        # Sorted by size descending
        assert grouped["decision-guides"][0].path == "decisions/b.md"
        assert grouped["decision-guides"][1].path == "decisions/a.md"

    def test_empty_input(self):
        assert categorize([]) == {}


# ── threshold flagging ───────────────────────────────────────────────────────


class TestThresholdFlagging:
    def test_flag_by_size(self):
        m = FileMetrics("big.md", 16384, 5000, 100, "other")  # 16 KB
        assert "size" in file_audit._flag(m, 15, 15000)

    def test_flag_by_chars(self):
        m = FileMetrics("wordy.md", 5000, 20000, 500, "other")
        assert "chars" in file_audit._flag(m, 15, 15000)

    def test_flag_both(self):
        m = FileMetrics("huge.md", 20480, 20000, 500, "other")
        result = file_audit._flag(m, 15, 15000)
        assert "size" in result
        assert "chars" in result

    def test_no_flag(self):
        m = FileMetrics("small.md", 1024, 500, 10, "other")
        assert file_audit._flag(m, 15, 15000) == ""


# ── JSON output ──────────────────────────────────────────────────────────────


class TestJsonOutput:
    def test_to_json_valid(self):
        files = [
            FileMetrics("a.md", 1024, 500, 10, "other"),
        ]
        result = json.loads(file_audit.to_json(files))
        assert len(result) == 1
        assert result[0]["path"] == "a.md"
        assert result[0]["size_kb"] == 1.0
        assert result[0]["chars"] == 500
