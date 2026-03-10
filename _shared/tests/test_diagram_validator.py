"""Tests for diagram-validator.py — validates ASCII diagram structural correctness."""

import importlib.util
from pathlib import Path

SHARED_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SHARED_DIR.parent
SCRIPT_PATH = (
    REPO_ROOT / ".github" / "skills" / "fabric-design" / "scripts" / "diagram-validator.py"
)

spec = importlib.util.spec_from_file_location("diagram_validator", str(SCRIPT_PATH))
_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_mod)

validate_diagram = _mod.validate_diagram


# ── Empty / placeholder checks ──────────────────────────────────────


class TestEmptyDiagram:
    def test_empty_string_is_invalid(self):
        result = validate_diagram("")
        assert not result["valid"]
        assert any(f["severity"] == "red" for f in result["findings"])

    def test_whitespace_only_is_invalid(self):
        result = validate_diagram("   \n  \n  ")
        assert not result["valid"]

    def test_placeholder_is_invalid(self):
        result = validate_diagram(
            "<!-- Replace this block with your ASCII diagram -->"
        )
        assert not result["valid"]
        assert any("placeholder" in f["message"].lower() for f in result["findings"])


# ── Box character balance ───────────────────────────────────────────


class TestBoxBalance:
    def test_single_balanced_box(self):
        diagram = "┌──────┐\n│ test │\n└──────┘"
        result = validate_diagram(diagram)
        assert result["valid"]
        assert result["stats"]["box_opens"] == 1
        assert result["stats"]["box_closes"] == 1

    def test_multiple_balanced_boxes(self):
        diagram = (
            "┌──────┐  ┌──────┐\n"
            "│  A   │  │  B   │\n"
            "└──────┘  └──────┘"
        )
        result = validate_diagram(diagram)
        assert result["stats"]["box_opens"] == 2
        assert result["stats"]["box_closes"] == 2
        balance_issues = [
            f for f in result["findings"] if "Unbalanced" in f["message"]
        ]
        assert len(balance_issues) == 0

    def test_unbalanced_missing_bottom(self):
        diagram = "┌──────┐\n│ test │"
        result = validate_diagram(diagram)
        balance_issues = [
            f for f in result["findings"] if "Unbalanced" in f["message"]
        ]
        assert len(balance_issues) > 0

    def test_unbalanced_extra_open(self):
        diagram = "┌──────┐\n│ test │\n└──────┘\n┌──────┐"
        result = validate_diagram(diagram)
        balance_issues = [
            f for f in result["findings"] if "Unbalanced" in f["message"]
        ]
        assert len(balance_issues) > 0

    def test_top_corners_mismatch(self):
        diagram = "┌──────\n│ test │\n└──────┘"
        result = validate_diagram(diagram)
        balance_issues = [
            f for f in result["findings"] if "top corners" in f["message"]
        ]
        assert len(balance_issues) > 0


# ── Line width checks ──────────────────────────────────────────────


class TestLineWidth:
    def test_within_default_width(self):
        diagram = "┌──────┐\n│ test │\n└──────┘"
        result = validate_diagram(diagram)
        width_issues = [
            f for f in result["findings"] if "exceed" in f["message"]
        ]
        assert len(width_issues) == 0

    def test_exceeds_default_width(self):
        long_line = "x" * 130
        diagram = f"┌──────┐\n{long_line}\n└──────┘"
        result = validate_diagram(diagram, max_width=120)
        width_issues = [
            f for f in result["findings"] if "exceed" in f["message"]
        ]
        assert len(width_issues) == 1
        assert width_issues[0]["severity"] == "yellow"

    def test_custom_max_width(self):
        line = "x" * 50
        diagram = f"┌──────┐\n{line}\n└──────┘"
        result = validate_diagram(diagram, max_width=40)
        width_issues = [
            f for f in result["findings"] if "exceed" in f["message"]
        ]
        assert len(width_issues) == 1

    def test_width_at_limit_passes(self):
        line = "x" * 120
        result = validate_diagram(line, max_width=120)
        width_issues = [
            f for f in result["findings"] if "exceed" in f["message"]
        ]
        assert len(width_issues) == 0


# ── Expected items coverage ─────────────────────────────────────────


class TestItemCoverage:
    def test_all_items_present(self):
        diagram = (
            "┌────────────┐\n│ lakehouse  │\n└────────────┘\n"
            "┌────────────┐\n│ notebook   │\n└────────────┘"
        )
        result = validate_diagram(diagram, expected_items=["lakehouse", "notebook"])
        missing = [f for f in result["findings"] if "Missing" in f["message"]]
        assert len(missing) == 0

    def test_missing_item_is_red(self):
        diagram = "┌────────────┐\n│ lakehouse  │\n└────────────┘"
        result = validate_diagram(diagram, expected_items=["lakehouse", "notebook"])
        assert not result["valid"]
        missing = [f for f in result["findings"] if "Missing" in f["message"]]
        assert len(missing) == 1
        assert missing[0]["severity"] == "red"
        assert "notebook" in missing[0]["message"]

    def test_case_insensitive_match(self):
        diagram = "┌────────────┐\n│ Lakehouse  │\n└────────────┘"
        result = validate_diagram(diagram, expected_items=["lakehouse"])
        missing = [f for f in result["findings"] if "Missing" in f["message"]]
        assert len(missing) == 0

    def test_no_expected_items_skips_check(self):
        diagram = "┌──────┐\n│ test │\n└──────┘"
        result = validate_diagram(diagram)
        missing = [f for f in result["findings"] if "Missing" in f["message"]]
        assert len(missing) == 0


# ── Result structure ────────────────────────────────────────────────


class TestResultStructure:
    def test_has_required_keys(self):
        result = validate_diagram("┌──────┐\n│ test │\n└──────┘")
        assert "valid" in result
        assert "findings" in result
        assert "stats" in result

    def test_stats_keys(self):
        result = validate_diagram("┌──────┐\n│ test │\n└──────┘")
        stats = result["stats"]
        assert "lines" in stats
        assert "max_line_width" in stats
        assert "box_opens" in stats
        assert "box_closes" in stats

    def test_line_count(self):
        result = validate_diagram("line1\nline2\nline3")
        assert result["stats"]["lines"] == 3

    def test_max_line_width(self):
        result = validate_diagram("short\nthis is a longer line\nmed")
        assert result["stats"]["max_line_width"] == len("this is a longer line")

    def test_findings_have_ids(self):
        result = validate_diagram("")
        for f in result["findings"]:
            assert f["id"].startswith("DV-")
            assert "severity" in f
            assert "message" in f

    def test_yellow_findings_still_valid(self):
        long_line = "x" * 130
        diagram = f"┌──────┐\n│ test │\n└──────┘\n{long_line}"
        result = validate_diagram(diagram, max_width=120)
        assert result["valid"]
