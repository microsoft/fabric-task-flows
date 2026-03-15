"""Tests for diagram-gen.py — verifies ASCII architecture diagram generation."""

import importlib.util
import re
import sys
from pathlib import Path

import pytest

SHARED_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SHARED_DIR / "lib"))

REPO_ROOT = SHARED_DIR.parent
DESIGN_SKILL = REPO_ROOT / ".github" / "skills" / "fabric-design"
SCRIPT_PATH = DESIGN_SKILL / "scripts" / "diagram-gen.py"

# Load diagram-gen
_spec = importlib.util.spec_from_file_location("diagram_gen", str(SCRIPT_PATH))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

_make_box = _mod._make_box
generate_diagram = _mod.generate_diagram
LAYER_MAP = _mod.LAYER_MAP
LAYER_ORDER = _mod.LAYER_ORDER


# ── Sample handoff content ──────────────────────────────────────────


SAMPLE_HANDOFF = """\
---
project: Test Project
task_flow: medallion
---

# Architecture Handoff

**Project:** Test Project
**Task Flow:** medallion

## Items

```yaml
items:
  - id: 1
    name: bronze-lakehouse
    type: Lakehouse
    depends_on: []
  - id: 2
    name: silver-notebook
    type: Notebook
    depends_on: [bronze-lakehouse]
  - id: 3
    name: gold-report
    type: Report
    depends_on: [silver-notebook]
```

## Waves

```yaml
waves:
  - id: 1
    name: Foundation
    items: [bronze-lakehouse]
  - id: 2
    name: Processing
    items: [silver-notebook]
  - id: 3
    name: Serving
    items: [gold-report]
```
"""

EMPTY_ITEMS_HANDOFF = """\
---
project: Empty
task_flow: test
---

# Architecture Handoff

```yaml
other_data:
  - key: value
```
"""


def _write_handoff(tmp_path, content):
    """Write content to a temp handoff file and return the path."""
    p = tmp_path / "architecture-handoff.md"
    p.write_text(content, encoding="utf-8")
    return str(p)


# ── _make_box tests ─────────────────────────────────────────────────


class TestMakeBox:
    def test_box_has_correct_corners(self):
        lines = _make_box("test", "Lakehouse", wave=1, width=20)
        assert lines[0].startswith("┌")
        assert lines[0].endswith("┐")
        assert lines[-1].startswith("└")
        assert lines[-1].endswith("┘")

    def test_box_contains_name(self):
        lines = _make_box("my-lakehouse", "Lakehouse", wave=1, width=24)
        content = "\n".join(lines)
        assert "my-lakehouse" in content

    def test_box_contains_type(self):
        lines = _make_box("test", "Lakehouse", wave=1, width=20)
        content = "\n".join(lines)
        assert "(Lakehouse)" in content

    def test_box_contains_wave_when_set(self):
        lines = _make_box("test", "Lakehouse", wave=2, width=20)
        content = "\n".join(lines)
        assert "[W2]" in content

    def test_box_omits_wave_when_none(self):
        lines = _make_box("test", "Lakehouse", wave=None, width=20)
        content = "\n".join(lines)
        assert "[W" not in content

    def test_box_lines_uniform_width(self):
        lines = _make_box("test", "Lakehouse", wave=1, width=24)
        for line in lines:
            assert len(line) == 24

    def test_box_side_borders(self):
        lines = _make_box("test", "Lakehouse", wave=None, width=20)
        for line in lines[1:-1]:
            assert line.startswith("│ ")
            assert line.endswith(" │")

    def test_box_minimum_width(self):
        lines = _make_box("x", "Y", wave=None, width=20)
        assert len(lines[0]) == 20


# ── LAYER_MAP constants ────────────────────────────────────────────


class TestLayerMap:
    def test_common_types_mapped(self):
        assert LAYER_MAP["Lakehouse"] == "STORAGE"
        assert LAYER_MAP["Notebook"] == "PROCESSING"
        assert LAYER_MAP["Report"] == "SERVING"
        assert LAYER_MAP["Pipeline"] == "INGESTION"
        assert LAYER_MAP["Environment"] == "COMPUTE"

    def test_layer_order_has_all_layers(self):
        for layer in set(LAYER_MAP.values()):
            assert layer in LAYER_ORDER


# ── generate_diagram integration tests ──────────────────────────────


class TestGenerateDiagram:
    def test_returns_string(self, tmp_path):
        path = _write_handoff(tmp_path, SAMPLE_HANDOFF)
        result = generate_diagram(path)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_title_bar(self, tmp_path):
        path = _write_handoff(tmp_path, SAMPLE_HANDOFF)
        result = generate_diagram(path)
        assert "Test Project" in result
        assert "medallion" in result

    def test_contains_double_border(self, tmp_path):
        path = _write_handoff(tmp_path, SAMPLE_HANDOFF)
        result = generate_diagram(path)
        assert "╔" in result
        assert "╗" in result
        assert "╚" in result
        assert "╝" in result

    def test_contains_all_items(self, tmp_path):
        path = _write_handoff(tmp_path, SAMPLE_HANDOFF)
        result = generate_diagram(path)
        assert "bronze-lakehouse" in result
        assert "silver-notebook" in result
        assert "gold-report" in result

    def test_contains_wave_headers(self, tmp_path):
        path = _write_handoff(tmp_path, SAMPLE_HANDOFF)
        result = generate_diagram(path)
        assert "Wave 1" in result
        assert "Wave 2" in result
        assert "Wave 3" in result

    def test_wave_order_preserved(self, tmp_path):
        path = _write_handoff(tmp_path, SAMPLE_HANDOFF)
        result = generate_diagram(path)
        w1 = result.index("Wave 1")
        w2 = result.index("Wave 2")
        w3 = result.index("Wave 3")
        assert w1 < w2 < w3

    def test_contains_box_characters(self, tmp_path):
        path = _write_handoff(tmp_path, SAMPLE_HANDOFF)
        result = generate_diagram(path)
        assert "┌" in result
        assert "┐" in result
        assert "└" in result
        assert "┘" in result

    def test_box_balance(self, tmp_path):
        path = _write_handoff(tmp_path, SAMPLE_HANDOFF)
        result = generate_diagram(path)
        assert result.count("┌") == result.count("┘")
        assert result.count("┐") == result.count("└")

    def test_inter_wave_arrows(self, tmp_path):
        path = _write_handoff(tmp_path, SAMPLE_HANDOFF)
        result = generate_diagram(path)
        assert "▼" in result

    def test_no_items_returns_message(self, tmp_path):
        path = _write_handoff(tmp_path, EMPTY_ITEMS_HANDOFF)
        result = generate_diagram(path)
        assert "No items found" in result

    def test_no_blockers_message(self, tmp_path):
        path = _write_handoff(tmp_path, SAMPLE_HANDOFF)
        result = generate_diagram(path)
        assert "No blockers" in result


# ── Layer-based diagram tests ───────────────────────────────────────


class TestLayerBasedDiagram:
    """Tests for the layer-based diagram layout."""

    def test_contains_layer_labels(self, tmp_path):
        """Diagram should show architectural layer labels."""
        path = _write_handoff(tmp_path, SAMPLE_HANDOFF)
        result = generate_diagram(path)
        # SAMPLE_HANDOFF has Lakehouse (STORAGE), Notebook (PROCESSING), Report (SERVING)
        assert "STORAGE" in result
        assert "PROCESSING" in result
        assert "SERVING" in result

    def test_layer_order_preserved(self, tmp_path):
        """Layers should appear in LAYER_ORDER sequence."""
        path = _write_handoff(tmp_path, SAMPLE_HANDOFF)
        result = generate_diagram(path)
        storage_pos = result.index("STORAGE")
        processing_pos = result.index("PROCESSING")
        serving_pos = result.index("SERVING")
        assert storage_pos < processing_pos < serving_pos

    def test_items_grouped_by_layer(self, tmp_path):
        """Items should appear within their layer section."""
        path = _write_handoff(tmp_path, SAMPLE_HANDOFF)
        result = generate_diagram(path)
        # bronze-lakehouse (STORAGE) should be near STORAGE label
        storage_pos = result.index("STORAGE")
        lakehouse_pos = result.index("bronze-lakehouse")
        # Notebook (PROCESSING) should be near PROCESSING label
        processing_pos = result.index("PROCESSING")
        notebook_pos = result.index("silver-notebook")
        assert storage_pos < lakehouse_pos < processing_pos
        assert processing_pos < notebook_pos


# ── Alternative-items diagram tests ─────────────────────────────────


SAMPLE_HANDOFF_WITH_ALTERNATIVES = """\
---
project: Alt Test
task_flow: medallion
---

# Architecture Handoff

**Project:** Alt Test
**Task Flow:** medallion

## Items

```yaml
items:
  - id: 1
    name: gold-lakehouse
    type: Lakehouse
    depends_on: []
  - id: 2
    name: gold-warehouse
    type: Warehouse
    depends_on: []
    note: "Alternative to gold-lakehouse"
```

## Waves

```yaml
waves:
  - id: 1
    name: Foundation
    items: [gold-lakehouse, gold-warehouse]
```
"""


class TestAlternativeItems:
    """Tests for alternative item rendering in diagrams."""

    def test_alternatives_use_or_connector(self, tmp_path):
        """Diagram should show OR between alternative items."""
        path = _write_handoff(tmp_path, SAMPLE_HANDOFF_WITH_ALTERNATIVES)
        result = generate_diagram(path)
        assert "OR" in result


# ── LAYER_MAP coverage tests ────────────────────────────────────────


class TestLayerMapCoverage:
    """Verify every task-flow item type has a LAYER_MAP entry."""

    def test_all_item_types_mapped(self):
        """Every item type in task-flow definitions must have a LAYER_MAP entry."""
        import json

        config_path = REPO_ROOT / "_shared" / "registry" / "script-config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        layer_map = config.get("layer_map", {}).get("values", {})

        task_flows_dir = REPO_ROOT / "_shared" / "registry" / "task-flows"
        if not task_flows_dir.exists():
            pytest.skip("No task-flows directory found")

        unmapped_types = set()
        for tf_file in task_flows_dir.glob("*.yml"):
            content = tf_file.read_text(encoding="utf-8")
            for match in re.finditer(
                r'^\s*type:\s*["\']?(\w+)["\']?', content, re.MULTILINE
            ):
                item_type = match.group(1)
                if item_type not in layer_map:
                    unmapped_types.add(item_type)

        assert not unmapped_types, (
            f"Item types missing from LAYER_MAP in script-config.json: "
            f"{sorted(unmapped_types)}. "
            f"Add these to layer_map.values in _shared/registry/script-config.json."
        )
