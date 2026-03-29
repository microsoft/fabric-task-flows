"""
Shared YAML parsing utilities for task-flows scripts.

Consolidates duplicated YAML extraction and parsing logic that was
previously copy-pasted across deploy-script-gen.py, taskflow-gen.py,
taskflow-template-gen.py, and test-plan-prefill.py.
"""

from __future__ import annotations

import re
from typing import Any

# ─────────────────────────────────────────────────────────────────────────────
# Compiled patterns
# ─────────────────────────────────────────────────────────────────────────────

YAML_FENCE_RE = re.compile(r"```ya?ml\s*\n(.*?)```", re.DOTALL)
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


# ─────────────────────────────────────────────────────────────────────────────
# Block extraction
# ─────────────────────────────────────────────────────────────────────────────

def extract_yaml_blocks(text: str) -> list[str]:
    """Extract raw YAML strings from ```yaml fenced code blocks."""
    return [m.group(1) for m in YAML_FENCE_RE.finditer(text)]


def extract_and_parse_yaml_blocks(content: str) -> list[dict[str, Any]]:
    """Extract YAML blocks and parse each into a dict.

    Skips comment-only or empty blocks. Uses the recursive parser.
    """
    blocks: list[dict[str, Any]] = []
    for match in YAML_FENCE_RE.finditer(content):
        raw = match.group(1)
        lines = [line for line in raw.split("\n")
                 if line.strip() and not line.strip().startswith("#")]
        if not lines:
            continue
        parsed = parse_yaml(raw)
        if parsed:
            blocks.append(parsed)
    return blocks


def extract_frontmatter(text: str) -> dict[str, Any]:
    """Parse YAML frontmatter from ``--- ... ---`` delimiters."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    return parse_yaml(match.group(1))


def extract_task_flow(content: str) -> str | None:
    """Extract task_flow value from markdown content.

    Searches YAML frontmatter first (``task_flow:`` or ``task-flow:`` or
    ``taskflow:``), then falls back to body patterns like
    ``**Task Flow:** value``.  Returns the lowercased value or ``None``.
    """
    # 1. Try YAML frontmatter (--- ... ---)
    fm = FRONTMATTER_RE.match(content)
    if fm:
        m = re.search(r'(?:task[-_]?flow)\s*:\s*(\S+)', fm.group(1), re.IGNORECASE)
        if m:
            return m.group(1).strip().strip('"').strip("'").lower()

    # 2. Try body: task_flow/task-flow/taskflow key anywhere in content
    m = re.search(r'(?:task[-_]?flow)\s*:\s*(\S+)', content, re.IGNORECASE)
    if m:
        return m.group(1).strip().strip('"').strip("'").lower()

    # 3. Fallback: **Task Flow:** value pattern
    m = re.search(r'\*\*Task\s+[Ff]low:\*\*\s*(\S+)', content)
    if m:
        val = m.group(1).strip().lower()
        # Take first word (might have extra description after)
        val = re.split(r'\s*[\(\[]', val)[0].strip()
        return val if val else None

    # 4. Fallback: "Task Flow: `value`" or "Task Flow: value" in body
    m = re.search(r'Task\s+Flow\s*:\s*`?(\S+?)`?(?:\s|$)', content)
    if m:
        return m.group(1).strip().lower()

    return None


def find_block(blocks: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
    """Return the first parsed block that contains *key*."""
    for b in blocks:
        if key in b:
            return b
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Scalar / value parsing
# ─────────────────────────────────────────────────────────────────────────────

def split_list(s: str) -> list[str]:
    """Split comma-separated values, respecting quotes."""
    parts: list[str] = []
    current: list[str] = []
    in_quotes = False
    quote_char = ""
    for ch in s:
        if ch in ('"', "'") and not in_quotes:
            in_quotes = True
            quote_char = ch
            current.append(ch)
        elif ch == quote_char and in_quotes:
            in_quotes = False
            current.append(ch)
        elif ch == "," and not in_quotes:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current).strip())
    return parts


def parse_yaml_value(raw: str) -> str | int | float | bool | list | None:
    """Parse a YAML scalar or inline list into a Python value."""
    raw = raw.strip()
    if raw in ("", "~", "null"):
        return None
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [parse_yaml_value(v) for v in split_list(inner)]
    if raw.lower() in ("true", "yes"):
        return True
    if raw.lower() in ("false", "no"):
        return False
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    # Strip quotes
    if (raw.startswith('"') and raw.endswith('"')) or \
       (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]
    return raw


def parse_inline_mapping(line: str) -> dict[str, Any]:
    """Parse a YAML inline mapping like ``{id: 1, name: foo, depends_on: [1,2]}``."""
    line = line.strip()
    if line.startswith("{") and line.endswith("}"):
        line = line[1:-1]

    result: dict[str, Any] = {}
    depth = 0
    in_quotes = False
    quote_char = ""
    parts: list[str] = []
    current: list[str] = []

    for ch in line:
        if ch in ('"', "'") and not in_quotes:
            in_quotes = True
            quote_char = ch
            current.append(ch)
        elif ch == quote_char and in_quotes:
            in_quotes = False
            current.append(ch)
        elif ch == "[":
            depth += 1
            current.append(ch)
        elif ch == "]":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0 and not in_quotes:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current))

    for part in parts:
        part = part.strip()
        colon_idx = part.find(":")
        if colon_idx == -1:
            continue
        key = part[:colon_idx].strip()
        val = part[colon_idx + 1:].strip()
        result[key] = parse_yaml_value(val)

    return result


def parse_yaml_scalar(block: str, key: str) -> str | None:
    """Extract a single scalar value for *key* from a YAML block."""
    match = re.search(rf"^{key}:\s*(.+)$", block, re.MULTILINE)
    if match:
        return match.group(1).strip().strip('"').strip("'")
    return None


def parse_yaml_list(block: str, key: str) -> list[dict[str, str]]:
    """Parse a YAML list of mappings nested under *key*.

    Handles blocks like::

        acceptance_criteria:
          - id: AC-1
            type: structural
            criterion: "Bronze Lakehouse exists"
    """
    items: list[dict[str, str]] = []
    pattern = re.compile(rf"^{key}:\s*$", re.MULTILINE)
    match = pattern.search(block)
    if not match:
        return items

    remainder = block[match.end():]
    current: dict[str, str] | None = None

    for line in remainder.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # Stop at a new top-level key
        if re.match(r"^[a-zA-Z_]", line) and not line.startswith(" "):
            break
        item_start = re.match(r"^\s+-\s+(.*)", line)
        if item_start:
            if current is not None:
                items.append(current)
            current = {}
            kv = item_start.group(1)
            kv_match = re.match(r'(\w+):\s*(.*)', kv)
            if kv_match:
                current[kv_match.group(1)] = kv_match.group(2).strip().strip('"').strip("'")
        elif current is not None:
            kv_match = re.match(r'\s+(\w+):\s*(.*)', line)
            if kv_match:
                current[kv_match.group(1)] = kv_match.group(2).strip().strip('"').strip("'")

    if current is not None:
        items.append(current)

    return items


# ─────────────────────────────────────────────────────────────────────────────
# Full recursive YAML parser (no PyYAML dependency)
# ─────────────────────────────────────────────────────────────────────────────

def parse_yaml(text: str) -> dict[str, Any]:
    """Parse a subset of YAML sufficient for architecture handoff blocks.

    Handles nested mappings, lists, inline lists, and scalars without
    requiring PyYAML.
    """
    lines = text.split("\n")
    root: dict[str, Any] = {}
    _parse_mapping(lines, 0, 0, root)
    return root


def _next_content_line(lines: list[str], start: int) -> int:
    """Skip blank lines and comments, return index of next content line."""
    i = start
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped and not stripped.startswith("#"):
            return i
        i += 1
    return i


def _strip_inline_comment(value: str) -> str:
    """Remove trailing ``# comment`` from a value string."""
    in_quotes = False
    quote_char = ""
    for i, ch in enumerate(value):
        if ch in ('"', "'") and not in_quotes:
            in_quotes = True
            quote_char = ch
        elif ch == quote_char and in_quotes:
            in_quotes = False
        elif ch == "#" and not in_quotes:
            return value[:i].rstrip()
    return value


def _split_inline_list(value: str) -> list[str]:
    """Split ``[a, b, c]`` into ``['a', 'b', 'c']``."""
    inner = value.strip()
    if inner.startswith("[") and inner.endswith("]"):
        inner = inner[1:-1].strip()
    if not inner:
        return []
    return [v.strip().strip('"').strip("'") for v in inner.split(",") if v.strip()]


def _parse_scalar(value: str) -> Any:
    """Convert a scalar string to an appropriate Python type."""
    value = _strip_inline_comment(value)
    if not value or value in ("~", "null", "Null", "NULL"):
        return None
    if value.lower() in ("true", "yes"):
        return True
    if value.lower() in ("false", "no"):
        return False
    # Inline list
    if value.startswith("[") and value.endswith("]"):
        return _split_inline_list(value)
    # Quoted string
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def _parse_scalar_or_inline(value: str) -> Any:
    """Parse a value that may be a scalar, inline list, or inline mapping."""
    value = _strip_inline_comment(value).strip()
    if value.startswith("{") and value.endswith("}"):
        return parse_inline_mapping(value)
    return _parse_scalar(value)


def _parse_list(lines: list[str], start: int, base_indent: int,
                target: list[Any]) -> int:
    """Parse a YAML list into *target*."""
    i = start
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        indent = len(line) - len(line.lstrip())
        if indent < base_indent:
            return i

        if not stripped.startswith("- "):
            return i

        value_part = stripped[2:].strip()

        if ":" in value_part and not value_part.startswith('"'):
            # List of mappings: ``- key: value``
            child: dict[str, Any] = {}
            key_match = re.match(r"([\w\-]+)\s*:\s*(.*)", value_part)
            if key_match:
                k = key_match.group(1)
                v = key_match.group(2).strip()
                child[k] = _parse_scalar_or_inline(v) if v else None

            # Consume continuation lines of this mapping
            i += 1
            while i < len(lines):
                nxt = lines[i]
                nxt_stripped = nxt.strip()
                if not nxt_stripped or nxt_stripped.startswith("#"):
                    i += 1
                    continue
                nxt_indent = len(nxt) - len(nxt.lstrip())
                if nxt_indent <= base_indent or nxt_stripped.startswith("- "):
                    break
                km = re.match(r"([\w\-]+)\s*:\s*(.*)", nxt_stripped)
                if km:
                    child[km.group(1)] = _parse_scalar_or_inline(km.group(2).strip()) \
                        if km.group(2).strip() else None
                i += 1

            target.append(child)
        else:
            target.append(_parse_scalar(value_part))
            i += 1

    return i


def _parse_mapping(lines: list[str], start: int, base_indent: int,
                   target: dict[str, Any]) -> int:
    """Recursively parse a YAML mapping into *target*."""
    i = start
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        indent = len(line) - len(line.lstrip())
        if indent < base_indent:
            return i

        key_match = re.match(r"^(\s*)([\w\-]+)\s*:\s*(.*)", line)
        if not key_match:
            i += 1
            continue

        indent = len(key_match.group(1))
        if indent != base_indent:
            if indent < base_indent:
                return i
            i += 1
            continue

        key = key_match.group(2)
        value_str = key_match.group(3).strip()

        if value_str.startswith("#"):
            value_str = ""

        if value_str:
            target[key] = _parse_scalar_or_inline(value_str)
            i += 1
        else:
            next_i = _next_content_line(lines, i + 1)
            if next_i >= len(lines):
                target[key] = None
                i = next_i
                continue

            next_line = lines[next_i]
            next_indent = len(next_line) - len(next_line.lstrip())
            next_stripped = next_line.strip()

            if next_indent <= base_indent:
                target[key] = None
                i = next_i
                continue

            if next_stripped.startswith("- "):
                lst: list[Any] = []
                i = _parse_list(lines, next_i, next_indent, lst)
                target[key] = lst
            else:
                child: dict[str, Any] = {}
                i = _parse_mapping(lines, next_i, next_indent, child)
                target[key] = child
    return i
