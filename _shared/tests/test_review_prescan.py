"""Tests for review-prescan.py — verifies architecture handoff pre-scan checks."""

import importlib.util
import sys
from pathlib import Path

SHARED_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SHARED_DIR / "lib"))

REPO_ROOT = SHARED_DIR.parent
DESIGN_SKILL = REPO_ROOT / ".github" / "skills" / "fabric-design"
SCRIPT_PATH = DESIGN_SKILL / "scripts" / "review-prescan.py"

# Import the module from its hyphenated filename
spec = importlib.util.spec_from_file_location("review_prescan", str(SCRIPT_PATH))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

prescan = mod.prescan
_check_wave_dependencies = mod._check_wave_dependencies
_check_item_names = mod._check_item_names
_check_ac_coverage = mod._check_ac_coverage
_check_wave_count = mod._check_wave_count
_check_diagram = mod._check_diagram
_check_naming_safety = mod._check_naming_safety
_truncate = mod._truncate
_has_cycle = mod._has_cycle


# ---------------------------------------------------------------------------
# Helper to write a temporary handoff file and run prescan
# ---------------------------------------------------------------------------

def _write_handoff(tmp_path: Path, content: str) -> str:
    """Write content to a temp file and return the path."""
    p = tmp_path / "handoff.md"
    p.write_text(content, encoding="utf-8")
    return str(p)


# ---------------------------------------------------------------------------
# Minimal handoff template for integration tests
# ---------------------------------------------------------------------------

MINIMAL_HANDOFF = """\
---
project: test-project
task_flow: medallion
---

# Architecture Handoff

**Project:** test-project
**Task Flow:** medallion

## Architecture Diagram

```
┌──────────┐    ┌────────────┐    ┌───────────┐
│  source  │───▶│  raw-lake  │───▶│  report   │
└──────────┘    └────────────┘    └───────────┘
```

## Items

```yaml
items:
  - id: 1
    name: raw-lake
    type: Lakehouse
    depends_on: []
  - id: 2
    name: report
    type: Report
    depends_on: [raw-lake]
```

## Waves

```yaml
waves:
  - id: 1
    items: [raw-lake]
  - id: 2
    items: [report]
```

## Acceptance Criteria

```yaml
acceptance_criteria:
  - id: AC-1
    description: raw-lake lakehouse exists
    verify: Check raw-lake exists via REST API
  - id: AC-2
    description: report is published
    verify: Check report exists in workspace
```
"""


# ── prescan integration: full pipeline ────────────────────────────────────


def test_prescan_returns_required_keys(tmp_path):
    path = _write_handoff(tmp_path, MINIMAL_HANDOFF)
    result = prescan(path)

    required = {
        "project", "task_flow", "review_date", "architecture_version",
        "scan_type", "findings", "wave_optimization", "cli_verification",
        "item_deployment_matrix", "prerequisites", "assessment",
        "must_fix", "should_fix", "no_change",
    }
    assert required.issubset(set(result.keys())), (
        f"Missing keys: {required - set(result.keys())}"
    )


def test_prescan_scan_type_is_automated(tmp_path):
    path = _write_handoff(tmp_path, MINIMAL_HANDOFF)
    result = prescan(path)
    assert result["scan_type"] == "automated"


def test_prescan_extracts_project_and_taskflow(tmp_path):
    path = _write_handoff(tmp_path, MINIMAL_HANDOFF)
    result = prescan(path)
    assert result["project"] == "test-project"
    assert result["task_flow"] == "medallion"


def test_prescan_findings_have_ids(tmp_path):
    path = _write_handoff(tmp_path, MINIMAL_HANDOFF)
    result = prescan(path)
    for f in result["findings"]:
        assert "id" in f
        assert f["id"].startswith("F-")


def test_prescan_findings_have_required_fields(tmp_path):
    path = _write_handoff(tmp_path, MINIMAL_HANDOFF)
    result = prescan(path)
    for f in result["findings"]:
        assert "area" in f
        assert "severity" in f
        assert f["severity"] in ("red", "yellow", "green")
        assert "finding" in f
        assert "suggestion" in f


def test_prescan_assessment_is_valid(tmp_path):
    path = _write_handoff(tmp_path, MINIMAL_HANDOFF)
    result = prescan(path)
    assert result["assessment"] in ("ready", "needs-changes")


def test_prescan_wave_optimization_structure(tmp_path):
    path = _write_handoff(tmp_path, MINIMAL_HANDOFF)
    result = prescan(path)
    wo = result["wave_optimization"]
    assert "current_waves" in wo
    assert "proposed_waves" in wo
    assert "changes" in wo
    assert isinstance(wo["changes"], list)


# ── prescan: fallback to markdown headers ─────────────────────────────────


def test_prescan_falls_back_to_markdown_headers(tmp_path):
    content = """\
# Architecture Handoff

**Project:** header-project
**Task Flow:** lambda

## Architecture Diagram

```
┌─────┐
│ box │
└─────┘
```
"""
    path = _write_handoff(tmp_path, content)
    result = prescan(path)
    assert result["project"] == "header-project"
    assert result["task_flow"] == "lambda"


# ── prescan: missing blocks produce warnings ──────────────────────────────


def test_prescan_warns_on_missing_blocks(tmp_path):
    content = """\
---
project: empty
task_flow: test
---
# No YAML blocks here

## Architecture Diagram

```
┌─────┐
│ box │
└─────┘
```
"""
    path = _write_handoff(tmp_path, content)
    result = prescan(path)
    warning_texts = [f["finding"] for f in result["findings"]
                     if f["area"] == "Parse warning"]
    assert any("items" in w.lower() for w in warning_texts)
    assert any("waves" in w.lower() for w in warning_texts)


# ── _check_wave_dependencies ─────────────────────────────────────────────


def test_wave_deps_green_when_correct():
    items = [
        {"name": "a", "id": 1, "dependencies": []},
        {"name": "b", "id": 2, "dependencies": ["a"]},
    ]
    waves = [
        {"id": 1, "items": ["a"]},
        {"id": 2, "items": ["b"]},
    ]
    findings = _check_wave_dependencies(items, waves)
    assert any(f["severity"] == "green" for f in findings)


def test_wave_deps_red_when_dep_in_later_wave():
    items = [
        {"name": "a", "id": 1, "dependencies": ["b"]},
        {"name": "b", "id": 2, "dependencies": []},
    ]
    waves = [
        {"id": 1, "items": ["a"]},
        {"id": 2, "items": ["b"]},
    ]
    findings = _check_wave_dependencies(items, waves)
    assert any(f["severity"] == "red" for f in findings)


def test_wave_deps_yellow_when_same_wave():
    items = [
        {"name": "a", "id": 1, "dependencies": ["b"]},
        {"name": "b", "id": 2, "dependencies": []},
    ]
    waves = [
        {"id": 1, "items": ["a", "b"]},
    ]
    findings = _check_wave_dependencies(items, waves)
    assert any(f["severity"] == "yellow" for f in findings)


def test_wave_deps_warns_unassigned_item():
    items = [
        {"name": "orphan", "id": 1, "dependencies": []},
    ]
    waves = [
        {"id": 1, "items": ["other"]},
    ]
    findings = _check_wave_dependencies(items, waves)
    assert any("not assigned" in f["finding"] for f in findings)


def test_wave_deps_detects_circular():
    items = [
        {"name": "a", "id": 1, "dependencies": ["b"]},
        {"name": "b", "id": 2, "dependencies": ["a"]},
    ]
    waves = [
        {"id": 1, "items": ["a"]},
        {"id": 2, "items": ["b"]},
    ]
    findings = _check_wave_dependencies(items, waves)
    assert any("Circular" in f["finding"] for f in findings)


# ── _has_cycle ────────────────────────────────────────────────────────────


def test_has_cycle_true():
    graph = {"a": ["b"], "b": ["a"]}
    assert _has_cycle(graph) is True


def test_has_cycle_false():
    graph = {"a": ["b"], "b": []}
    assert _has_cycle(graph) is False


def test_has_cycle_empty():
    assert _has_cycle({}) is False


def test_has_cycle_self_loop():
    graph = {"a": ["a"]}
    assert _has_cycle(graph) is True


# ── _check_item_names ────────────────────────────────────────────────────


def test_item_names_green_when_valid():
    items = [{"name": "raw-lakehouse"}, {"name": "curated-lakehouse"}]
    findings = _check_item_names(items)
    assert any(f["severity"] == "green" for f in findings)


def test_item_names_yellow_when_not_kebab():
    items = [{"name": "My Lakehouse"}]
    findings = _check_item_names(items)
    assert any(f["severity"] == "yellow" for f in findings)
    assert any("kebab" in f["finding"].lower() for f in findings)


def test_item_names_red_on_duplicates():
    items = [{"name": "lake"}, {"name": "Lake"}]
    findings = _check_item_names(items)
    assert any(f["severity"] == "red" for f in findings)
    assert any("Duplicate" in f["finding"] for f in findings)


# ── _check_ac_coverage ───────────────────────────────────────────────────


def test_ac_coverage_green_when_all_covered():
    items = [{"name": "raw-lake"}, {"name": "report"}]
    acs = [
        {"id": "AC-1", "description": "raw-lake exists"},
        {"id": "AC-2", "description": "report published"},
    ]
    findings = _check_ac_coverage(items, acs)
    assert all(f["severity"] == "green" for f in findings)


def test_ac_coverage_yellow_when_missing():
    items = [{"name": "raw-lake"}, {"name": "report"}]
    acs = [{"id": "AC-1", "description": "raw-lake exists"}]
    findings = _check_ac_coverage(items, acs)
    assert any(f["severity"] == "yellow" for f in findings)
    assert any("report" in f["finding"] for f in findings)


def test_ac_coverage_empty_acs():
    items = [{"name": "something"}]
    acs = []
    findings = _check_ac_coverage(items, acs)
    assert any(f["severity"] == "yellow" for f in findings)


# ── _check_wave_count ────────────────────────────────────────────────────


def test_wave_count_green_when_optimal():
    items = [
        {"name": "a", "id": 1, "dependencies": []},
        {"name": "b", "id": 2, "dependencies": ["a"]},
    ]
    waves = [
        {"id": 1, "items": ["a"]},
        {"id": 2, "items": ["b"]},
    ]
    findings, wave_opt = _check_wave_count(items, waves)
    assert wave_opt["current_waves"] == 2
    assert any(f["severity"] == "green" for f in findings)


def test_wave_count_suggests_merge_for_independent_single_item():
    items = [
        {"name": "a", "id": 1, "dependencies": []},
        {"name": "b", "id": 2, "dependencies": []},
        {"name": "c", "id": 3, "dependencies": []},
    ]
    waves = [
        {"id": 1, "items": ["a", "b"]},
        {"id": 2, "items": ["c"]},
    ]
    findings, wave_opt = _check_wave_count(items, waves)
    assert wave_opt["current_waves"] == 2
    assert len(wave_opt["changes"]) > 0
    assert any(f["severity"] == "yellow" for f in findings)


# ── _check_diagram ───────────────────────────────────────────────────────


def test_diagram_green_when_balanced():
    content = """\
## Architecture Diagram

```
┌──────────┐    ┌────────────┐
│   lake   │───▶│   report   │
└──────────┘    └────────────┘
```
"""
    items = [{"name": "lake"}, {"name": "report"}]
    findings = _check_diagram(content, items)
    assert any(f["severity"] == "green" and "balanced" in f["finding"]
               for f in findings)


def test_diagram_yellow_when_missing_section():
    content = "## Some Other Section\nno diagram here"
    items = [{"name": "lake"}]
    findings = _check_diagram(content, items)
    assert any(f["severity"] == "yellow"
               and "No Architecture Diagram" in f["finding"]
               for f in findings)


def test_diagram_yellow_when_no_code_block():
    content = """\
## Architecture Diagram

Just text, no code block.
"""
    items = []
    findings = _check_diagram(content, items)
    assert any(f["severity"] == "yellow"
               and "No code block" in f["finding"]
               for f in findings)


def test_diagram_yellow_on_placeholder():
    content = """\
## Architecture Diagram

```
Replace this block with a real diagram.
```
"""
    items = []
    findings = _check_diagram(content, items)
    assert any(f["severity"] == "yellow"
               and "placeholder" in f["finding"]
               for f in findings)


def test_diagram_yellow_on_unbalanced_boxes():
    content = """\
## Architecture Diagram

```
┌──────────┐
│   lake   │
```
"""
    items = [{"name": "lake"}]
    findings = _check_diagram(content, items)
    assert any(f["severity"] == "yellow"
               and "Unbalanced" in f["finding"]
               for f in findings)


def test_diagram_yellow_when_items_missing():
    content = """\
## Architecture Diagram

```
┌──────────┐
│   lake   │
└──────────┘
```
"""
    items = [{"name": "lake"}, {"name": "report"}]
    findings = _check_diagram(content, items)
    assert any(f["severity"] == "yellow"
               and "missing from diagram" in f["finding"]
               for f in findings)


# ── _check_naming_safety ─────────────────────────────────────────────────


def test_naming_safety_green_no_hyphens():
    items = [{"name": "raw_lakehouse", "type": "Lakehouse"}]
    findings = _check_naming_safety(items)
    assert any(f["severity"] == "green" for f in findings)


def test_naming_safety_yellow_with_hyphens():
    items = [{"name": "raw-lakehouse", "type": "Lakehouse"}]
    findings = _check_naming_safety(items)
    assert any(f["severity"] == "yellow" for f in findings)
    assert any("raw_lakehouse" in f["suggestion"] for f in findings)


# ── _truncate ────────────────────────────────────────────────────────────


def test_truncate_short_text():
    assert _truncate("hello world") == "hello world"


def test_truncate_long_text():
    words = " ".join(f"w{i}" for i in range(30))
    result = _truncate(words)
    assert len(result.split()) == 15


def test_truncate_custom_limit():
    assert _truncate("a b c d e", max_words=3) == "a b c"


# ── item counting / categorization (via prescan) ─────────────────────────


def test_prescan_item_deployment_matrix(tmp_path):
    path = _write_handoff(tmp_path, MINIMAL_HANDOFF)
    result = prescan(path)
    matrix = result["item_deployment_matrix"]
    assert isinstance(matrix, list)
    types_found = {e["type"] for e in matrix}
    assert "Lakehouse" in types_found or "Report" in types_found


def test_prescan_must_fix_and_should_fix_are_lists(tmp_path):
    path = _write_handoff(tmp_path, MINIMAL_HANDOFF)
    result = prescan(path)
    assert isinstance(result["must_fix"], list)
    assert isinstance(result["should_fix"], list)
    assert isinstance(result["no_change"], list)


# ── item normalization ───────────────────────────────────────────────────


def test_prescan_normalizes_item_name_and_type(tmp_path):
    content = """\
---
project: norm-test
task_flow: medallion
---

## Architecture Diagram

```
┌──────────┐
│  myitem  │
└──────────┘
```

```yaml
items:
  - item_name: myitem
    item_type: Lakehouse
```

```yaml
waves:
  - wave_number: 1
    items: [myitem]
```
"""
    path = _write_handoff(tmp_path, content)
    result = prescan(path)
    matrix = result["item_deployment_matrix"]
    assert any(e["item"] == "myitem" for e in matrix)


def test_prescan_handles_string_items(tmp_path):
    content = """\
---
project: str-test
task_flow: medallion
---

## Architecture Diagram

```
┌─────────────┐
│  my-string  │
└─────────────┘
```

```yaml
items:
  - my-string
```

```yaml
waves:
  - id: 1
    items: [my-string]
```
"""
    path = _write_handoff(tmp_path, content)
    result = prescan(path)
    # String items are normalized to dicts with a name key
    assert result["project"] == "str-test"
