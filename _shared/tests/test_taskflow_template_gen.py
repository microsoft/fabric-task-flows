"""Tests for taskflow-template-gen.py — verifies Fabric Task Flow JSON generation."""

import importlib.util
import json
import sys
from pathlib import Path

SHARED_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SHARED_DIR / "lib"))

REPO_ROOT = SHARED_DIR.parent
SCRIPT_PATH = (
    REPO_ROOT / ".github" / "skills" / "fabric-deploy" / "scripts" / "taskflow-template-gen.py"
)

# Import the hyphenated module via importlib
_spec = importlib.util.spec_from_file_location(
    "taskflow_template_gen", str(SCRIPT_PATH)
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["taskflow_template_gen"] = _mod
_spec.loader.exec_module(_mod)

_extract_task_flow = _mod._extract_task_flow
_parse_items_block = _mod._parse_items_block
parse_handoff = _mod.parse_handoff
_resolve_task_type = _mod._resolve_task_type
generate_taskflow_json = _mod.generate_taskflow_json
Item = _mod.Item
HandoffData = _mod.HandoffData
TASK_TYPE_MAP = _mod.TASK_TYPE_MAP


# ── _extract_task_flow tests ───────────────────────────────────────


class TestExtractTaskFlow:
    def test_from_frontmatter(self):
        md = "---\ntask_flow: medallion\nproject: Test\n---\n# Handoff\n"
        assert _extract_task_flow(md) == "medallion"

    def test_from_markdown_pattern(self):
        md = "# Handoff\n\n**Task Flow:** lambda\n"
        assert _extract_task_flow(md) == "lambda"

    def test_strips_parenthetical(self):
        md = "# Handoff\n\n**Task Flow:** medallion (standard)\n"
        assert _extract_task_flow(md) == "medallion"

    def test_unknown_when_missing(self):
        md = "# Just a document\nNo task flow here.\n"
        assert _extract_task_flow(md) == "unknown"


# ── _parse_items_block tests ───────────────────────────────────────


SAMPLE_ITEMS_YAML = """\
- id: 1
  name: bronze-lakehouse
  type: Lakehouse
  depends_on: []
  purpose: Bronze storage
- id: 2
  name: transform-notebook
  type: Notebook
  depends_on: [1]
  purpose: Silver transform
"""


class TestParseItemsBlock:
    def test_parses_items(self):
        items = _parse_items_block(SAMPLE_ITEMS_YAML)
        assert len(items) == 2

    def test_item_fields(self):
        items = _parse_items_block(SAMPLE_ITEMS_YAML)
        assert items[0].name == "bronze-lakehouse"
        assert items[0].type == "Lakehouse"
        assert items[0].purpose == "Bronze storage"

    def test_item_id(self):
        items = _parse_items_block(SAMPLE_ITEMS_YAML)
        assert items[0].id == 1
        assert items[1].id == 2

    def test_depends_on_parsed(self):
        items = _parse_items_block(SAMPLE_ITEMS_YAML)
        assert items[0].depends_on == []
        assert items[1].depends_on == [1]

    def test_empty_block(self):
        items = _parse_items_block("")
        assert items == []

    def test_comments_ignored(self):
        yaml = "# comment\n- id: 1\n  name: test\n  type: Lakehouse\n"
        items = _parse_items_block(yaml)
        assert len(items) == 1


# ── parse_handoff integration ──────────────────────────────────────


SAMPLE_HANDOFF = """\
---
project: Test Project
task_flow: medallion
---

# Architecture Handoff

```yaml
items:
  - id: 1
    name: bronze-lakehouse
    type: Lakehouse
    depends_on: []
    purpose: Bronze storage
  - id: 2
    name: silver-notebook
    type: Notebook
    depends_on: [1]
    purpose: Silver transform
  - id: 3
    name: gold-report
    type: Report
    depends_on: [2]
    purpose: Analytics dashboard
```
"""


class TestParseHandoff:
    def test_extracts_task_flow(self, tmp_path):
        f = tmp_path / "handoff.md"
        f.write_text(SAMPLE_HANDOFF, encoding="utf-8")
        data = parse_handoff(str(f))
        assert data.task_flow == "medallion"

    def test_extracts_items(self, tmp_path):
        f = tmp_path / "handoff.md"
        f.write_text(SAMPLE_HANDOFF, encoding="utf-8")
        data = parse_handoff(str(f))
        assert len(data.items) == 3

    def test_item_types(self, tmp_path):
        f = tmp_path / "handoff.md"
        f.write_text(SAMPLE_HANDOFF, encoding="utf-8")
        data = parse_handoff(str(f))
        types = [i.type for i in data.items]
        assert "Lakehouse" in types
        assert "Notebook" in types
        assert "Report" in types

    def test_empty_handoff(self, tmp_path):
        f = tmp_path / "handoff.md"
        f.write_text("---\ntask_flow: test\n---\n# Empty\n", encoding="utf-8")
        data = parse_handoff(str(f))
        assert data.items == []


# ── _resolve_task_type tests ───────────────────────────────────────


class TestResolveTaskType:
    def test_known_type(self):
        assert _resolve_task_type("Lakehouse") in TASK_TYPE_MAP.values()

    def test_unknown_type_returns_general(self):
        assert _resolve_task_type("CompletelyUnknownType") == "general"

    def test_case_and_spacing_normalized(self):
        # The function normalizes case, spaces, hyphens, underscores
        result1 = _resolve_task_type("Lakehouse")
        result2 = _resolve_task_type("lakehouse")
        assert result1 == result2


# ── Item and HandoffData dataclasses ───────────────────────────────


class TestDataClasses:
    def test_item_defaults(self):
        item = Item(id=1, name="test", type="Lakehouse")
        assert item.depends_on == []
        assert item.purpose == ""

    def test_item_with_depends(self):
        item = Item(id=2, name="nb", type="Notebook", depends_on=[1])
        assert item.depends_on == [1]

    def test_handoff_data(self):
        items = [Item(id=1, name="lh", type="Lakehouse")]
        data = HandoffData(task_flow="medallion", items=items, project="Test")
        assert data.task_flow == "medallion"
        assert len(data.items) == 1
        assert data.project == "Test"


# ── generate_taskflow_json tests ───────────────────────────────────


class TestGenerateTaskflowJson:
    def _sample_data(self):
        return HandoffData(
            task_flow="medallion",
            items=[
                Item(id=1, name="bronze-lakehouse", type="Lakehouse",
                     purpose="Bronze storage"),
                Item(id=2, name="silver-notebook", type="Notebook",
                     depends_on=[1], purpose="Silver transform"),
                Item(id=3, name="gold-report", type="Report",
                     depends_on=[2], purpose="Dashboard"),
            ],
        )

    def test_returns_dict(self):
        result = generate_taskflow_json(self._sample_data(), "Test Project")
        assert isinstance(result, dict)

    def test_has_required_keys(self):
        result = generate_taskflow_json(self._sample_data(), "Test Project")
        assert "tasks" in result
        assert "edges" in result
        assert "name" in result
        assert "description" in result

    def test_task_count_matches_items(self):
        result = generate_taskflow_json(self._sample_data(), "Test Project")
        assert len(result["tasks"]) == 3

    def test_task_has_required_fields(self):
        result = generate_taskflow_json(self._sample_data(), "Test Project")
        for task in result["tasks"]:
            assert "id" in task
            assert "name" in task
            assert "type" in task
            assert "description" in task

    def test_task_ids_are_uuid_format(self):
        result = generate_taskflow_json(self._sample_data(), "Test Project")
        import uuid as _uuid
        for task in result["tasks"]:
            _uuid.UUID(task["id"])  # raises ValueError if not valid UUID

    def test_task_names_match_items(self):
        result = generate_taskflow_json(self._sample_data(), "Test Project")
        names = {t["name"] for t in result["tasks"]}
        assert "bronze-lakehouse" in names
        assert "silver-notebook" in names
        assert "gold-report" in names

    def test_edges_from_dependencies(self):
        result = generate_taskflow_json(self._sample_data(), "Test Project")
        assert len(result["edges"]) == 2
        for edge in result["edges"]:
            assert "source" in edge
            assert "target" in edge

    def test_edge_source_target_are_task_ids(self):
        result = generate_taskflow_json(self._sample_data(), "Test Project")
        task_ids = {t["id"] for t in result["tasks"]}
        for edge in result["edges"]:
            assert edge["source"] in task_ids
            assert edge["target"] in task_ids

    def test_flow_name_uses_project(self):
        result = generate_taskflow_json(self._sample_data(), "My Cool Project")
        assert result["name"] == "My Cool Project"

    def test_flow_name_fallback_to_task_flow(self):
        result = generate_taskflow_json(self._sample_data(), "")
        assert "Medallion" in result["name"]

    def test_description_includes_item_count(self):
        result = generate_taskflow_json(self._sample_data(), "Test")
        assert "3 items" in result["description"]

    def test_no_dependencies_no_edges(self):
        data = HandoffData(
            task_flow="simple",
            items=[
                Item(id=1, name="lh", type="Lakehouse"),
                Item(id=2, name="nb", type="Notebook"),
            ],
        )
        result = generate_taskflow_json(data, "Test")
        assert result["edges"] == []

    def test_purpose_used_in_description(self):
        result = generate_taskflow_json(self._sample_data(), "Test")
        descriptions = [t["description"] for t in result["tasks"]]
        assert any("Bronze storage" in d for d in descriptions)

    def test_serializable_to_json(self):
        result = generate_taskflow_json(self._sample_data(), "Test")
        output = json.dumps(result, indent=2)
        assert isinstance(output, str)
        parsed = json.loads(output)
        assert parsed["tasks"] == result["tasks"]
