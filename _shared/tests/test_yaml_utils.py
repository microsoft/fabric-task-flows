"""Tests for yaml_utils.py — verifies the shared YAML parsing utilities."""

from lib.yaml_utils import (
    extract_yaml_blocks,
    extract_and_parse_yaml_blocks,
    extract_frontmatter,
    extract_task_flow,
    find_block,
    split_list,
    parse_yaml_value,
    parse_inline_mapping,
    parse_yaml_scalar,
    parse_yaml_list,
    parse_yaml,
)


# ── extract_yaml_blocks ──────────────────────────────────────────────────

def test_extract_yaml_blocks_single():
    md = "Some text\n```yaml\nkey: value\n```\nMore text"
    blocks = extract_yaml_blocks(md)
    assert len(blocks) == 1
    assert "key: value" in blocks[0]


def test_extract_yaml_blocks_multiple():
    md = "```yaml\na: 1\n```\nparagraph\n```yaml\nb: 2\n```"
    blocks = extract_yaml_blocks(md)
    assert len(blocks) == 2
    assert "a: 1" in blocks[0]
    assert "b: 2" in blocks[1]


def test_extract_yaml_blocks_yml_variant():
    md = "```yml\nfoo: bar\n```"
    blocks = extract_yaml_blocks(md)
    assert len(blocks) == 1
    assert "foo: bar" in blocks[0]


def test_extract_yaml_blocks_no_blocks():
    assert extract_yaml_blocks("No yaml here") == []


def test_extract_yaml_blocks_empty_string():
    assert extract_yaml_blocks("") == []


def test_extract_yaml_blocks_other_fences_ignored():
    md = "```python\nprint('hi')\n```"
    assert extract_yaml_blocks(md) == []


# ── extract_and_parse_yaml_blocks ─────────────────────────────────────────

def test_extract_and_parse_yaml_blocks_basic():
    md = "# Heading\n```yaml\nname: medallion\nphase: Bronze\n```\n"
    blocks = extract_and_parse_yaml_blocks(md)
    assert len(blocks) == 1
    assert blocks[0]["name"] == "medallion"
    assert blocks[0]["phase"] == "Bronze"


def test_extract_and_parse_yaml_blocks_skips_comment_only():
    md = "```yaml\n# just a comment\n```"
    blocks = extract_and_parse_yaml_blocks(md)
    assert blocks == []


def test_extract_and_parse_yaml_blocks_skips_empty():
    md = "```yaml\n\n```"
    blocks = extract_and_parse_yaml_blocks(md)
    assert blocks == []


def test_extract_and_parse_yaml_blocks_multiple():
    md = (
        "```yaml\ntask_flow: medallion\n```\n"
        "text\n"
        "```yaml\ntask_flow: lambda\n```\n"
    )
    blocks = extract_and_parse_yaml_blocks(md)
    assert len(blocks) == 2
    assert blocks[0]["task_flow"] == "medallion"
    assert blocks[1]["task_flow"] == "lambda"


# ── extract_frontmatter ──────────────────────────────────────────────────

def test_extract_frontmatter_basic():
    text = "---\nid: param-select\ntitle: Parameterization\n---\n# Body"
    fm = extract_frontmatter(text)
    assert fm["id"] == "param-select"
    assert fm["title"] == "Parameterization"


def test_extract_frontmatter_with_list():
    text = "---\ntriggers:\n  - medallion\n  - lambda\n---\nbody"
    fm = extract_frontmatter(text)
    assert fm["triggers"] == ["medallion", "lambda"]


def test_extract_frontmatter_missing():
    assert extract_frontmatter("No frontmatter here") == {}


def test_extract_frontmatter_empty_string():
    assert extract_frontmatter("") == {}


def test_extract_frontmatter_not_at_start():
    text = "some text\n---\nid: late\n---\n"
    assert extract_frontmatter(text) == {}


def test_extract_frontmatter_decision_guide_style():
    text = (
        "---\n"
        "id: compute-selection\n"
        "title: Compute Engine Selection\n"
        "description: Choose between Spark, SQL, and Dataflows Gen2\n"
        "quick_decision: Use Spark for big data, SQL for warehousing\n"
        "---\n"
        "# Compute Selection Guide\n"
    )
    fm = extract_frontmatter(text)
    assert fm["id"] == "compute-selection"
    assert fm["quick_decision"] == "Use Spark for big data, SQL for warehousing"


# ── extract_task_flow ────────────────────────────────────────────────────

def test_extract_task_flow_frontmatter_underscore():
    text = "---\ntask_flow: medallion\ntitle: Test\n---\n# Body"
    assert extract_task_flow(text) == "medallion"


def test_extract_task_flow_frontmatter_hyphen():
    text = "---\ntask-flow: lambda\ntitle: Test\n---\n# Body"
    assert extract_task_flow(text) == "lambda"


def test_extract_task_flow_body_key():
    text = "# Architecture\n\ntask_flow: batch-processing\n"
    assert extract_task_flow(text) == "batch-processing"


def test_extract_task_flow_body_bold_pattern():
    text = "# Overview\n\n**Task Flow:** medallion\n\nSome description."
    assert extract_task_flow(text) == "medallion"


def test_extract_task_flow_returns_lowercase():
    text = "---\ntask_flow: Medallion\n---\n# Body"
    assert extract_task_flow(text) == "medallion"


def test_extract_task_flow_returns_none_when_missing():
    text = "# No task flow here\n\nJust some content."
    assert extract_task_flow(text) is None


def test_extract_task_flow_strips_quotes():
    text = '---\ntask_flow: "medallion"\n---\n# Body'
    assert extract_task_flow(text) == "medallion"
    text_single = "---\ntask_flow: 'lambda'\n---\n# Body"
    assert extract_task_flow(text_single) == "lambda"


def test_extract_task_flow_no_separator_variant():
    text = "---\ntaskflow: medallion\n---\n# Body"
    assert extract_task_flow(text) == "medallion"


# ── find_block ───────────────────────────────────────────────────────────

def test_find_block_present():
    blocks = [{"name": "a"}, {"items": [1, 2]}, {"name": "b"}]
    result = find_block(blocks, "items")
    assert result is not None
    assert result["items"] == [1, 2]


def test_find_block_returns_first_match():
    blocks = [{"x": 1}, {"x": 2}]
    assert find_block(blocks, "x")["x"] == 1


def test_find_block_missing():
    blocks = [{"a": 1}, {"b": 2}]
    assert find_block(blocks, "z") is None


def test_find_block_empty_list():
    assert find_block([], "key") is None


# ── split_list ───────────────────────────────────────────────────────────

def test_split_list_simple():
    assert split_list("a, b, c") == ["a", "b", "c"]


def test_split_list_quoted_commas():
    result = split_list('"hello, world", foo')
    assert result == ['"hello, world"', "foo"]


def test_split_list_single_quotes():
    result = split_list("'a, b', c")
    assert result == ["'a, b'", "c"]


def test_split_list_single_value():
    assert split_list("only") == ["only"]


def test_split_list_empty():
    assert split_list("") == []


def test_split_list_whitespace_trimmed():
    assert split_list("  x  ,  y  ") == ["x", "y"]


# ── parse_yaml_value ─────────────────────────────────────────────────────

def test_parse_yaml_value_string():
    assert parse_yaml_value("hello") == "hello"


def test_parse_yaml_value_int():
    assert parse_yaml_value("42") == 42


def test_parse_yaml_value_float():
    assert parse_yaml_value("3.14") == 3.14


def test_parse_yaml_value_true():
    assert parse_yaml_value("true") is True
    assert parse_yaml_value("yes") is True
    assert parse_yaml_value("True") is True


def test_parse_yaml_value_false():
    assert parse_yaml_value("false") is False
    assert parse_yaml_value("no") is False


def test_parse_yaml_value_null():
    assert parse_yaml_value("null") is None
    assert parse_yaml_value("~") is None
    assert parse_yaml_value("") is None


def test_parse_yaml_value_quoted():
    assert parse_yaml_value('"quoted"') == "quoted"
    assert parse_yaml_value("'single'") == "single"


def test_parse_yaml_value_inline_list():
    result = parse_yaml_value("[1, 2, 3]")
    assert result == [1, 2, 3]


def test_parse_yaml_value_inline_list_empty():
    assert parse_yaml_value("[]") == []


def test_parse_yaml_value_inline_list_strings():
    result = parse_yaml_value("[a, b, c]")
    assert result == ["a", "b", "c"]


def test_parse_yaml_value_with_whitespace():
    assert parse_yaml_value("  42  ") == 42


# ── parse_inline_mapping ─────────────────────────────────────────────────

def test_parse_inline_mapping_basic():
    result = parse_inline_mapping("{id: 1, name: foo}")
    assert result["id"] == 1
    assert result["name"] == "foo"


def test_parse_inline_mapping_with_list():
    result = parse_inline_mapping("{id: 1, deps: [2, 3]}")
    assert result["id"] == 1
    assert result["deps"] == [2, 3]


def test_parse_inline_mapping_no_braces():
    result = parse_inline_mapping("id: 1, name: bar")
    assert result["id"] == 1
    assert result["name"] == "bar"


def test_parse_inline_mapping_quoted_value():
    result = parse_inline_mapping('{name: "hello world"}')
    assert result["name"] == "hello world"


def test_parse_inline_mapping_empty():
    result = parse_inline_mapping("{}")
    assert result == {}


def test_parse_inline_mapping_bool_values():
    result = parse_inline_mapping("{active: true, deleted: false}")
    assert result["active"] is True
    assert result["deleted"] is False


# ── parse_yaml_scalar ────────────────────────────────────────────────────

def test_parse_yaml_scalar_basic():
    block = "name: medallion\nphase: Bronze"
    assert parse_yaml_scalar(block, "name") == "medallion"
    assert parse_yaml_scalar(block, "phase") == "Bronze"


def test_parse_yaml_scalar_quoted():
    block = 'title: "My Title"'
    assert parse_yaml_scalar(block, "title") == "My Title"


def test_parse_yaml_scalar_single_quoted():
    block = "title: 'My Title'"
    assert parse_yaml_scalar(block, "title") == "My Title"


def test_parse_yaml_scalar_missing_key():
    block = "name: test"
    assert parse_yaml_scalar(block, "missing") is None


def test_parse_yaml_scalar_empty_block():
    assert parse_yaml_scalar("", "key") is None


def test_parse_yaml_scalar_multiline_finds_correct():
    block = "a: first\nb: second\nc: third"
    assert parse_yaml_scalar(block, "b") == "second"


# ── parse_yaml_list ──────────────────────────────────────────────────────

def test_parse_yaml_list_basic():
    block = (
        "acceptance_criteria:\n"
        "  - id: AC-1\n"
        "    type: structural\n"
        "    criterion: Bronze Lakehouse exists\n"
        "  - id: AC-2\n"
        "    type: structural\n"
        "    criterion: Silver Lakehouse exists\n"
    )
    items = parse_yaml_list(block, "acceptance_criteria")
    assert len(items) == 2
    assert items[0]["id"] == "AC-1"
    assert items[0]["type"] == "structural"
    assert items[0]["criterion"] == "Bronze Lakehouse exists"
    assert items[1]["id"] == "AC-2"


def test_parse_yaml_list_stops_at_next_key():
    block = (
        "items:\n"
        "  - id: I-1\n"
        "    name: first\n"
        "next_key: something\n"
    )
    items = parse_yaml_list(block, "items")
    assert len(items) == 1
    assert items[0]["id"] == "I-1"


def test_parse_yaml_list_missing_key():
    block = "other: value"
    assert parse_yaml_list(block, "items") == []


def test_parse_yaml_list_empty_block():
    assert parse_yaml_list("", "items") == []


def test_parse_yaml_list_quoted_values():
    block = (
        "criteria:\n"
        '  - id: AC-1\n'
        '    criterion: "Lakehouse exists"\n'
    )
    items = parse_yaml_list(block, "criteria")
    assert len(items) == 1
    assert items[0]["criterion"] == "Lakehouse exists"


def test_parse_yaml_list_skips_comments():
    block = (
        "items:\n"
        "  # this is a comment\n"
        "  - id: X-1\n"
        "    name: first\n"
    )
    items = parse_yaml_list(block, "items")
    assert len(items) == 1
    assert items[0]["id"] == "X-1"


# ── parse_yaml (full recursive parser) ───────────────────────────────────

def test_parse_yaml_flat_mapping():
    text = "name: test\nversion: 1\nenabled: true"
    result = parse_yaml(text)
    assert result["name"] == "test"
    assert result["version"] == 1
    assert result["enabled"] is True


def test_parse_yaml_nested_mapping():
    text = "parent:\n  child: value\n  count: 5"
    result = parse_yaml(text)
    assert result["parent"]["child"] == "value"
    assert result["parent"]["count"] == 5


def test_parse_yaml_list_of_scalars():
    text = "items:\n  - alpha\n  - beta\n  - gamma"
    result = parse_yaml(text)
    assert result["items"] == ["alpha", "beta", "gamma"]


def test_parse_yaml_list_of_mappings():
    text = (
        "items:\n"
        "  - id: 1\n"
        "    name: first\n"
        "  - id: 2\n"
        "    name: second\n"
    )
    result = parse_yaml(text)
    assert len(result["items"]) == 2
    assert result["items"][0]["id"] == 1
    assert result["items"][0]["name"] == "first"
    assert result["items"][1]["id"] == 2


def test_parse_yaml_inline_list():
    text = "tags: [a, b, c]"
    result = parse_yaml(text)
    assert result["tags"] == ["a", "b", "c"]


def test_parse_yaml_inline_mapping_value():
    text = "config: {host: localhost, port: 8080}"
    result = parse_yaml(text)
    assert result["config"]["host"] == "localhost"
    assert result["config"]["port"] == 8080


def test_parse_yaml_null_values():
    text = "a: null\nb: ~\nc:"
    result = parse_yaml(text)
    assert result["a"] is None
    assert result["b"] is None
    assert result["c"] is None


def test_parse_yaml_comments_ignored():
    text = "# top comment\nkey: value\n# mid comment\nother: data"
    result = parse_yaml(text)
    assert result["key"] == "value"
    assert result["other"] == "data"
    assert "#" not in str(result.keys())


def test_parse_yaml_inline_comment_stripped():
    text = "name: test  # this is a comment"
    result = parse_yaml(text)
    assert result["name"] == "test"


def test_parse_yaml_empty_string():
    assert parse_yaml("") == {}


def test_parse_yaml_blank_lines():
    text = "\n\nkey: value\n\n"
    result = parse_yaml(text)
    assert result["key"] == "value"


def test_parse_yaml_boolean_variants():
    text = "a: true\nb: false\nc: yes\nd: no\ne: True\nf: False"
    result = parse_yaml(text)
    assert result["a"] is True
    assert result["b"] is False
    assert result["c"] is True
    assert result["d"] is False
    assert result["e"] is True
    assert result["f"] is False


def test_parse_yaml_numeric_types():
    text = "integer: 42\nfloating: 3.14\nnegative: -7"
    result = parse_yaml(text)
    assert result["integer"] == 42
    assert result["floating"] == 3.14
    assert result["negative"] == -7


def test_parse_yaml_quoted_strings():
    text = 'double: "hello"\nsingle: \'world\''
    result = parse_yaml(text)
    assert result["double"] == "hello"
    assert result["single"] == "world"


def test_parse_yaml_deeply_nested():
    text = (
        "level1:\n"
        "  level2:\n"
        "    level3: deep\n"
    )
    result = parse_yaml(text)
    assert result["level1"]["level2"]["level3"] == "deep"


def test_parse_yaml_mixed_structure():
    text = (
        "task_flow: medallion\n"
        "workspace: my-workspace\n"
        "items:\n"
        "  - name: Bronze\n"
        "    type: Lakehouse\n"
        "  - name: Silver\n"
        "    type: Lakehouse\n"
        "config:\n"
        "  region: eastus\n"
        "  capacity: F2\n"
        "tags: [prod, analytics]\n"
    )
    result = parse_yaml(text)
    assert result["task_flow"] == "medallion"
    assert result["workspace"] == "my-workspace"
    assert len(result["items"]) == 2
    assert result["items"][0]["name"] == "Bronze"
    assert result["items"][1]["type"] == "Lakehouse"
    assert result["config"]["region"] == "eastus"
    assert result["tags"] == ["prod", "analytics"]


# ── Integration: YAML blocks in markdown (skill usage pattern) ───────────

def test_architecture_handoff_pattern():
    """Simulates extracting an architecture handoff YAML block from markdown."""
    md = (
        "# Architecture Handoff\n\n"
        "```yaml\n"
        "task_flow: medallion\n"
        "workspace: contoso-analytics\n"
        "items:\n"
        "  - name: Bronze Lakehouse\n"
        "    type: Lakehouse\n"
        "    wave: 1\n"
        "  - name: Silver Lakehouse\n"
        "    type: Lakehouse\n"
        "    wave: 1\n"
        "  - name: Gold Warehouse\n"
        "    type: Warehouse\n"
        "    wave: 2\n"
        "```\n"
    )
    blocks = extract_and_parse_yaml_blocks(md)
    assert len(blocks) == 1
    handoff = blocks[0]
    assert handoff["task_flow"] == "medallion"
    assert len(handoff["items"]) == 3
    assert handoff["items"][2]["type"] == "Warehouse"
    assert handoff["items"][2]["wave"] == 2


def test_decision_guide_frontmatter_pattern():
    """Simulates reading a decision guide with frontmatter + options."""
    text = (
        "---\n"
        "id: parameterization-selection\n"
        "title: Parameterization Strategy\n"
        "description: Choose parameterization approach\n"
        "triggers:\n"
        "  - parameterization\n"
        "  - environment variables\n"
        "options:\n"
        "  - name: Variable Library\n"
        "    when: Multi-environment deployments\n"
        "  - name: parameter.yml\n"
        "    when: Simple single-environment\n"
        "---\n"
        "# Parameterization Guide\n"
        "Body text here.\n"
    )
    fm = extract_frontmatter(text)
    assert fm["id"] == "parameterization-selection"
    assert len(fm["triggers"]) == 2
    assert fm["triggers"][0] == "parameterization"
    assert len(fm["options"]) == 2
    assert fm["options"][0]["name"] == "Variable Library"


def test_parse_yaml_hyphenated_keys():
    text = "task-flow: medallion\nmy-key: my-value"
    result = parse_yaml(text)
    assert result["task-flow"] == "medallion"
    assert result["my-key"] == "my-value"
