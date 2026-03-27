"""Tests for check-drift.py — verifies documentation drift detection logic."""

import importlib.util
import json
from pathlib import Path

import pytest

SHARED_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SHARED_DIR.parent
CHECK_DRIFT_PATH = (
    REPO_ROOT / ".github" / "skills" / "fabric-test" / "scripts" / "check-drift.py"
)

# Import the hyphenated module via importlib
spec = importlib.util.spec_from_file_location("check_drift", str(CHECK_DRIFT_PATH))
check_drift = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_drift)

DriftChecker = check_drift.DriftChecker

# At least 10 task flows needed for coverage checks
SAMPLE_FLOWS = [
    "medallion", "lambda", "event-analytics", "real-time-analytics",
    "data-warehouse", "data-lakehouse", "translytical", "batch-etl",
    "iot-analytics", "streaming-etl",
]


# ── scaffold helper ─────────────────────────────────────────────────


def _scaffold_repo(tmp_path, flows=None):
    """Build a minimal mock repo tree; returns dict of paths to monkeypatch."""
    flows = flows or list(SAMPLE_FLOWS)
    paths = {}

    # task-flows.md — H2 headings produce slugified IDs
    tf = tmp_path / "task-flows.md"
    lines = ["# Task Flows\n"]
    for f in flows:
        heading = f.replace("-", " ").title()
        lines.append(f"## {heading}\n")
    tf.write_text("\n".join(lines), encoding="utf-8")
    paths["TASK_FLOW_SOURCE"] = tf

    # diagrams/ — one .md per flow + _index.md
    diagrams = tmp_path / "diagrams"
    diagrams.mkdir()
    idx_lines = ["| id | desc |\n", "|---|---|\n"]
    for f in flows:
        (diagrams / f"{f}.md").write_text(f"# {f}\n", encoding="utf-8")
        idx_lines.append(f"| `{f}` | D |\n")
    (diagrams / "_index.md").write_text("".join(idx_lines), encoding="utf-8")
    paths["DIAGRAMS_DIR"] = diagrams

    # validation registry
    reg_dir = tmp_path / "registry"
    reg_dir.mkdir()
    val = reg_dir / "validation-checklists.json"
    val.write_text(
        json.dumps({"task_flows": {f: {} for f in flows}}), encoding="utf-8"
    )
    paths["VALIDATION_REGISTRY"] = val

    # item-type registry
    item_reg = reg_dir / "item-type-registry.json"
    item_data = {
        "$version": "1.0",
        "types": {
            "lakehouse": {
                "fab_type": "Lakehouse",
                "display_name": "Lakehouse",
                "aliases": [],
                "phase": "Foundation",
                "phase_order": 1,
                "task_type": "store data",
                "rest_api": True,
                "availability": "GA",
            },
            "notebook": {
                "fab_type": "Notebook",
                "display_name": "Notebook",
                "aliases": [],
                "phase": "Transformation",
                "phase_order": 3,
                "task_type": "prepare data",
                "rest_api": True,
                "availability": "GA",
            },
        },
    }
    item_reg.write_text(json.dumps(item_data), encoding="utf-8")
    paths["REGISTRY_PATH"] = item_reg

    # advisor — Integration First, Better Together, signal table (≥30 rows)
    advisor = tmp_path / "advisor.md"
    adv_lines = [
        "# Advisor\n\n",
        "## Integration First\n\n",
        "Databricks Better Together with Fabric.\n",
        "Snowflake Better Together with Fabric.\n\n",
        "| Signal Words | Velocity | Use Case | Task Flow Candidates |\n",
        "|---|---|---|---|\n",
    ]
    for i, f in enumerate(flows):
        adv_lines.append(f"| signal-{i} | low | case-{i} | {f} |\n")
    for i in range(len(flows), 32):
        f = flows[i % len(flows)]
        adv_lines.append(f"| signal-{i} | low | case-{i} | {f} |\n")
    adv_lines.append("\nEnd of table\n")
    advisor.write_text("".join(adv_lines), encoding="utf-8")
    paths["ADVISOR_PATH"] = advisor

    # decisions/ — index + two guide files
    decisions = tmp_path / "decisions"
    decisions.mkdir()
    (decisions / "_index.md").write_text(
        "| id | desc |\n|---|---|\n"
        "| `ingestion` | [ingestion-selection.md](ingestion-selection.md) |\n"
        "| `skillset` | [skillset-selection.md](skillset-selection.md) |\n",
        encoding="utf-8",
    )
    (decisions / "ingestion-selection.md").write_text(
        "---\n"
        "id: ingestion\n"
        "title: Ingestion Selection\n"
        "triggers: [ingestion]\n"
        "options:\n"
        "  - id: copy-job\n"
        "    label: Copy Job\n"
        "  - id: mirroring\n"
        "    label: Mirroring\n"
        "  - id: dataflow-gen2\n"
        "    label: Dataflow Gen2\n"
        "---\n\n"
        "# Ingestion Selection\n\n"
        "| Criteria | Copy Job | Dataflow Gen2 | Mirroring |\n"
        "|---|---|---|---|\n"
        "| Speed | Fast | Medium | Fast |\n\n"
        "**Mirroring** supports Azure SQL, Cosmos DB, Snowflake\n\n"
        "### Choose Copy Job when\nUse for bulk loads.\n\n"
        "### Choose Mirroring when\nSource is Azure SQL, Cosmos DB, Snowflake.\n\n"
        "### Choose Dataflow Gen2 when\nNeed transformations.\n",
        encoding="utf-8",
    )
    (decisions / "skillset-selection.md").write_text(
        "---\n"
        "id: skillset\n"
        "title: Skillset Selection\n"
        "triggers: [skillset]\n"
        "options:\n"
        "  - id: spark\n"
        "    label: Spark\n"
        "---\n\n"
        "# Skillset Selection\n\n"
        "## Evolution Paths\nUse evolution paths.\n",
        encoding="utf-8",
    )
    paths["DECISIONS_DIR"] = decisions

    return paths


@pytest.fixture
def mock_repo(tmp_path, monkeypatch):
    """Scaffold a consistent mock repo and patch module-level constants."""
    paths = _scaffold_repo(tmp_path)
    for attr, path in paths.items():
        monkeypatch.setattr(check_drift, attr, path)
    return tmp_path


# ── DriftChecker class ──────────────────────────────────────────────


class TestDriftChecker:
    def test_pass_is_recorded(self):
        dc = DriftChecker()
        dc.check("ok", True, "")
        assert len(dc.passes) == 1
        assert len(dc.failures) == 0

    def test_fail_is_recorded(self):
        dc = DriftChecker()
        dc.check("bad", False, "something wrong")
        assert len(dc.failures) == 1
        assert "something wrong" in dc.failures[0]
        assert len(dc.passes) == 0

    def test_report_returns_zero_when_all_pass(self):
        dc = DriftChecker()
        dc.check("a", True, "")
        dc.check("b", True, "")
        assert dc.report() == 0

    def test_report_returns_one_on_failure(self):
        dc = DriftChecker()
        dc.check("a", True, "")
        dc.check("b", False, "problem")
        assert dc.report() == 1

    def test_verbose_shows_passes(self, capsys):
        dc = DriftChecker(verbose=True)
        dc.check("my-pass", True, "")
        dc.report()
        assert "my-pass" in capsys.readouterr().out

    def test_non_verbose_hides_passes(self, capsys):
        dc = DriftChecker(verbose=False)
        dc.check("my-pass", True, "")
        dc.report()
        assert "my-pass" not in capsys.readouterr().out

    def test_failures_always_printed(self, capsys):
        dc = DriftChecker(verbose=False)
        dc.check("my-fail", False, "oops")
        dc.report()
        assert "my-fail" in capsys.readouterr().out

    def test_mixed_counts(self):
        dc = DriftChecker()
        for i in range(5):
            dc.check(f"p{i}", True, "")
        for i in range(3):
            dc.check(f"f{i}", False, f"err{i}")
        assert len(dc.passes) == 5
        assert len(dc.failures) == 3


# ── Helper functions ────────────────────────────────────────────────


class TestExtractTaskFlowIds:
    def test_extracts_h2_slugs(self, tmp_path, monkeypatch):
        md = tmp_path / "tf.md"
        md.write_text(
            "## Medallion\n## Lambda\n## Event Analytics\n", encoding="utf-8"
        )
        monkeypatch.setattr(check_drift, "TASK_FLOW_SOURCE", md)
        ids = check_drift.extract_task_flow_ids_from_taskflows_md()
        assert ids == {"medallion", "lambda", "event-analytics"}

    def test_skips_meta_headings(self, tmp_path, monkeypatch):
        md = tmp_path / "tf.md"
        md.write_text(
            "## Overview\n## Quick Reference\n## How to Use\n## Medallion\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(check_drift, "TASK_FLOW_SOURCE", md)
        ids = check_drift.extract_task_flow_ids_from_taskflows_md()
        assert ids == {"medallion"}


class TestExtractIdsFromIndex:
    def test_parses_table_rows(self, tmp_path):
        index = tmp_path / "_index.md"
        index.write_text(
            "| id | desc |\n|---|---|\n"
            "| `medallion` | M |\n| `lambda` | L |\n",
            encoding="utf-8",
        )
        ids = check_drift.extract_ids_from_index(index)
        assert ids == {"medallion", "lambda"}

    def test_ignores_header_row(self, tmp_path):
        index = tmp_path / "_index.md"
        index.write_text(
            "| id | desc |\n|---|---|\n| `alpha` | A |\n", encoding="utf-8"
        )
        ids = check_drift.extract_ids_from_index(index)
        assert "id" not in ids
        assert "alpha" in ids


class TestExtractSignalTaskFlows:
    def test_extracts_hyphenated_and_single_word(self, tmp_path):
        advisor = tmp_path / "advisor.md"
        advisor.write_text(
            "| Signal Words | Velocity | Use Case | Task Flow Candidates |\n"
            "|---|---|---|---|\n"
            "| batch | low | BI | medallion |\n"
            "| stream | high | IoT | event-analytics |\n"
            "\nEnd\n",
            encoding="utf-8",
        )
        ids = check_drift.extract_signal_task_flows(advisor)
        assert "medallion" in ids
        assert "event-analytics" in ids

    def test_stops_at_table_end(self, tmp_path):
        advisor = tmp_path / "advisor.md"
        advisor.write_text(
            "| Signal Words | Velocity | Use Case | Task Flow Candidates |\n"
            "|---|---|---|---|\n"
            "| a | b | c | data-warehouse |\n"
            "\nSome text with fake-flow-id here\n",
            encoding="utf-8",
        )
        ids = check_drift.extract_signal_task_flows(advisor)
        assert "data-warehouse" in ids
        assert "fake-flow-id" not in ids


class TestExtractYamlFrontmatter:
    def test_parses_frontmatter(self, tmp_path):
        md = tmp_path / "guide.md"
        md.write_text(
            "---\nid: test\ntitle: Test Guide\n---\n# Body\n", encoding="utf-8"
        )
        fm = check_drift.extract_yaml_frontmatter(md)
        assert fm["id"] == "test"

    def test_returns_none_without_frontmatter(self, tmp_path):
        md = tmp_path / "plain.md"
        md.write_text("# No frontmatter\n", encoding="utf-8")
        assert check_drift.extract_yaml_frontmatter(md) is None


class TestExtractIngestionComparisonColumns:
    def test_extracts_column_headers(self, tmp_path):
        md = tmp_path / "ing.md"
        md.write_text(
            "| Criteria | Copy Job | Dataflow Gen2 | Mirroring |\n"
            "|---|---|---|---|\n",
            encoding="utf-8",
        )
        cols = check_drift.extract_ingestion_comparison_columns(md)
        assert cols == {"Copy Job", "Dataflow Gen2", "Mirroring"}

    def test_empty_when_no_criteria_row(self, tmp_path):
        md = tmp_path / "ing.md"
        md.write_text("| A | B |\n|---|---|\n", encoding="utf-8")
        assert check_drift.extract_ingestion_comparison_columns(md) == set()


class TestExtractMirroringSources:
    def test_finds_known_sources(self, tmp_path):
        md = tmp_path / "ing.md"
        md.write_text(
            "**Mirroring** supports Azure SQL, Cosmos DB, Snowflake\n",
            encoding="utf-8",
        )
        sources = check_drift.extract_mirroring_sources(md, "**Mirroring**")
        assert "Azure SQL" in sources
        assert "Cosmos DB" in sources
        assert "Snowflake" in sources

    def test_returns_empty_when_pattern_absent(self, tmp_path):
        md = tmp_path / "ing.md"
        md.write_text("No matching pattern here.\n", encoding="utf-8")
        assert check_drift.extract_mirroring_sources(md, "**Mirroring**") == set()


# ── Check functions (integration with temp file structures) ─────────


class TestCheckTaskFlowCoverage:
    def test_passes_when_consistent(self, mock_repo):
        dc = DriftChecker()
        check_drift.check_task_flow_coverage(dc)
        assert len(dc.failures) == 0

    def test_detects_missing_diagram(self, mock_repo):
        (mock_repo / "diagrams" / "medallion.md").unlink()
        dc = DriftChecker()
        check_drift.check_task_flow_coverage(dc)
        fail_msgs = " ".join(dc.failures)
        assert "medallion" in fail_msgs

    def test_detects_missing_validation_entry(self, tmp_path, monkeypatch):
        paths = _scaffold_repo(tmp_path)
        val_data = json.loads(paths["VALIDATION_REGISTRY"].read_text(encoding="utf-8"))
        del val_data["task_flows"]["lambda"]
        paths["VALIDATION_REGISTRY"].write_text(
            json.dumps(val_data), encoding="utf-8"
        )
        for attr, path in paths.items():
            monkeypatch.setattr(check_drift, attr, path)
        dc = DriftChecker()
        check_drift.check_task_flow_coverage(dc)
        fail_msgs = " ".join(dc.failures)
        assert "lambda" in fail_msgs


class TestCheckDecisionGuides:
    def test_passes_when_consistent(self, mock_repo):
        dc = DriftChecker()
        check_drift.check_decision_guides(dc)
        assert len(dc.failures) == 0

    def test_detects_missing_frontmatter_field(self, mock_repo):
        guide = mock_repo / "decisions" / "ingestion-selection.md"
        guide.write_text(
            "---\nid: ingestion\ntitle: Ingestion\n---\n# Body\n",
            encoding="utf-8",
        )
        dc = DriftChecker()
        check_drift.check_decision_guides(dc)
        fail_msgs = " ".join(dc.failures)
        assert "options" in fail_msgs.lower()

    def test_detects_missing_referenced_file(self, mock_repo):
        idx = mock_repo / "decisions" / "_index.md"
        content = idx.read_text(encoding="utf-8")
        content += "| `missing` | [missing-selection.md](missing-selection.md) |\n"
        idx.write_text(content, encoding="utf-8")
        dc = DriftChecker()
        check_drift.check_decision_guides(dc)
        fail_msgs = " ".join(dc.failures)
        assert "missing-selection.md" in fail_msgs


class TestCheckIngestionConsistency:
    def test_passes_when_consistent(self, mock_repo):
        dc = DriftChecker()
        check_drift.check_ingestion_consistency(dc)
        assert len(dc.failures) == 0

    def test_detects_missing_choose_when_section(self, mock_repo):
        ing = mock_repo / "decisions" / "ingestion-selection.md"
        ing.write_text(
            "---\n"
            "id: ingestion\ntitle: Ingestion\ntriggers: [ingestion]\n"
            "options:\n"
            "  - id: copy-job\n    label: Copy Job\n"
            "  - id: mirroring\n    label: Mirroring\n"
            "---\n\n"
            "| Criteria | Copy Job | Mirroring |\n|---|---|---|\n| S | F | F |\n\n"
            "**Mirroring** supports Azure SQL, Cosmos DB\n\n"
            "### Choose Copy Job when\nBulk.\n\n"
            "Source is Azure SQL, Cosmos DB.\n",
            encoding="utf-8",
        )
        dc = DriftChecker()
        check_drift.check_ingestion_consistency(dc)
        fail_msgs = " ".join(dc.failures)
        assert "Mirroring" in fail_msgs


class TestCheckSignalMappingValidity:
    def test_passes_with_valid_signals(self, mock_repo):
        dc = DriftChecker()
        check_drift.check_signal_mapping_validity(dc)
        assert len(dc.failures) == 0

    def test_detects_invalid_task_flow_id(self, mock_repo):
        advisor = mock_repo / "advisor.md"
        content = advisor.read_text(encoding="utf-8")
        # Insert row before the blank line that terminates the table
        content = content.replace(
            "\n\nEnd of table",
            "\n| bogus | low | test | nonexistent-flow |\n\nEnd of table",
        )
        advisor.write_text(content, encoding="utf-8")
        dc = DriftChecker()
        check_drift.check_signal_mapping_validity(dc)
        fail_msgs = " ".join(dc.failures)
        assert "nonexistent-flow" in fail_msgs


class TestCheckRegistryReferences:
    def test_passes_with_valid_registry(self, mock_repo):
        dc = DriftChecker()
        check_drift.check_registry_references(dc)
        assert len(dc.failures) == 0

    def test_detects_missing_version(self, mock_repo):
        reg = mock_repo / "registry" / "item-type-registry.json"
        data = json.loads(reg.read_text(encoding="utf-8"))
        del data["$version"]
        reg.write_text(json.dumps(data), encoding="utf-8")
        dc = DriftChecker()
        check_drift.check_registry_references(dc)
        fail_msgs = " ".join(dc.failures)
        assert "$version" in fail_msgs


class TestCheckIntegrationFirst:
    def test_passes_with_correct_framing(self, mock_repo):
        dc = DriftChecker()
        check_drift.check_integration_first(dc)
        assert len(dc.failures) == 0

    def test_detects_missing_integration_first(self, mock_repo):
        advisor = mock_repo / "advisor.md"
        content = advisor.read_text(encoding="utf-8")
        content = content.replace("Integration First", "Some Other Section")
        advisor.write_text(content, encoding="utf-8")
        dc = DriftChecker()
        check_drift.check_integration_first(dc)
        fail_msgs = " ".join(dc.failures)
        assert "Integration First" in fail_msgs

    def test_detects_prescriptive_migration_language(self, mock_repo):
        advisor = mock_repo / "advisor.md"
        content = advisor.read_text(encoding="utf-8")
        content += "\nYou should migrate all workloads to Fabric.\n"
        advisor.write_text(content, encoding="utf-8")
        dc = DriftChecker()
        check_drift.check_integration_first(dc)
        fail_msgs = " ".join(dc.failures)
        assert "prescriptive" in fail_msgs.lower()

    def test_detects_migration_paths_in_skillset(self, mock_repo):
        skillset = mock_repo / "decisions" / "skillset-selection.md"
        content = skillset.read_text(encoding="utf-8")
        content = content.replace("Evolution Paths", "Migration Paths")
        skillset.write_text(content, encoding="utf-8")
        dc = DriftChecker()
        check_drift.check_integration_first(dc)
        fail_msgs = " ".join(dc.failures)
        assert "Migration Paths" in fail_msgs
