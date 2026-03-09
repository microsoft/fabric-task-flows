#!/usr/bin/env python3
"""
Deterministic pre-scan for architecture handoff review.

Runs mechanical checks against an architecture-handoff.md file and outputs
pre-filled review findings in the engineer-review schema format. The LLM
reviewer then only adds judgment-based findings.

Usage:
    python scripts/review-prescan.py --handoff projects/my-project/prd/architecture-handoff.md
    python scripts/review-prescan.py --handoff handoff.md --format json
    python scripts/review-prescan.py --handoff handoff.md --output review.yaml

Importable:
    from review_prescan import prescan
    result = prescan("projects/my-project/prd/architecture-handoff.md")
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Portal-only items — cannot be created via REST API
# Source: _shared/item-type-registry.json (rest_api.creatable field)
# ---------------------------------------------------------------------------

# Portal-only items — loaded from _shared/item-type-registry.json
# Do NOT maintain this dict manually. See CONTRIBUTING.md.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / "_shared"))
from registry_loader import build_portal_only_items

PORTAL_ONLY_ITEMS: dict[str, str] = build_portal_only_items()

KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


# ---------------------------------------------------------------------------
# Lightweight YAML parser (no PyYAML dependency)
# ---------------------------------------------------------------------------

def _parse_yaml(text: str) -> Any:
    """Parse a subset of YAML sufficient for architecture handoff blocks."""
    lines = text.split("\n")
    root: dict[str, Any] = {}
    _parse_mapping(lines, 0, 0, root)
    return root


def _parse_mapping(lines: list[str], start: int, base_indent: int,
                   target: dict[str, Any]) -> int:
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


def _parse_list(lines: list[str], start: int, base_indent: int,
                target: list[Any]) -> int:
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

        item_value = stripped[2:].strip()
        if item_value.startswith("#"):
            item_value = ""

        key_match = re.match(r"^([\w\-]+)\s*:\s*(.*)", item_value)
        if key_match:
            item_dict: dict[str, Any] = {}
            k = key_match.group(1)
            v = key_match.group(2).strip()
            if v and not v.startswith("#"):
                item_dict[k] = _parse_scalar_or_inline(v)
            else:
                item_dict[k] = None

            inner_indent = indent + 2
            i += 1
            i = _parse_mapping(lines, i, inner_indent, item_dict)
            target.append(item_dict)
        elif item_value:
            target.append(_parse_scalar_or_inline(item_value))
            i += 1
        else:
            i += 1
    return i


def _next_content_line(lines: list[str], start: int) -> int:
    i = start
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped and not stripped.startswith("#"):
            return i
        i += 1
    return i


def _parse_scalar_or_inline(value: str) -> Any:
    if value.startswith("#"):
        return None

    # Strip inline comments (not inside quotes)
    comment_stripped = _strip_inline_comment(value)

    # Inline list: [1, 2, 3] or []
    if comment_stripped.startswith("[") and comment_stripped.endswith("]"):
        inner = comment_stripped[1:-1].strip()
        if not inner:
            return []
        parts = _split_inline_list(inner)
        return [_parse_scalar(p.strip()) for p in parts]

    return _parse_scalar(comment_stripped)


def _strip_inline_comment(value: str) -> str:
    in_single = False
    in_double = False
    for i, ch in enumerate(value):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            return value[:i].rstrip()
    return value


def _split_inline_list(inner: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    in_quote = False
    quote_char = ""
    for ch in inner:
        if ch in ('"', "'") and not in_quote:
            in_quote = True
            quote_char = ch
            current.append(ch)
        elif ch == quote_char and in_quote:
            in_quote = False
            current.append(ch)
        elif ch == "[":
            depth += 1
            current.append(ch)
        elif ch == "]":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0 and not in_quote:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current))
    return parts


def _parse_scalar(value: str) -> Any:
    if not value:
        return None

    # Quoted string
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]

    lower = value.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower == "null" or lower == "~":
        return None

    # Integer
    try:
        return int(value)
    except ValueError:
        pass

    # Float
    try:
        return float(value)
    except ValueError:
        pass

    return value


# ---------------------------------------------------------------------------
# Markdown extraction
# ---------------------------------------------------------------------------

def _extract_frontmatter(content: str) -> dict[str, Any]:
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}
    return _parse_yaml(match.group(1))


def _extract_yaml_blocks(content: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for match in re.finditer(r"```ya?ml\s*\n(.*?)```", content, re.DOTALL):
        raw = match.group(1)
        # Skip comment-only / template-only blocks
        lines = [l for l in raw.split("\n")
                 if l.strip() and not l.strip().startswith("#")]
        if not lines:
            continue
        parsed = _parse_yaml(raw)
        if parsed:
            blocks.append(parsed)
    return blocks


def _find_block(blocks: list[dict[str, Any]], key: str) -> Any:
    for block in blocks:
        if key in block:
            return block[key]
    return None


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------

def _check_wave_dependencies(items: list[dict], waves: list[dict]) -> list[dict]:
    findings: list[dict] = []

    # Build lookup by both id and name
    item_by_name: dict[str, dict] = {}
    item_by_id: dict[int, dict] = {}
    for item in items:
        name = item.get("name", "")
        if name:
            item_by_name[name] = item
        iid = item.get("id")
        if iid is not None:
            item_by_id[int(iid)] = item

    # Map item name/id → wave
    item_wave: dict[str, int] = {}
    for wave in waves:
        wave_id = int(wave.get("id", 0))
        wave_items = wave.get("items", [])
        for witem in wave_items:
            item_wave[str(witem)] = wave_id

    errors: list[str] = []
    warnings: list[str] = []

    for item in items:
        name = item.get("name", str(item.get("id", "?")))
        deps = item.get("dependencies", item.get("depends_on", []))
        if deps is None:
            deps = []
        # Normalize deps to strings
        deps = [str(d) for d in deps]

        my_wave = item_wave.get(name) or item_wave.get(str(item.get("id", "")))

        if my_wave is None:
            warnings.append(f"{name} not assigned to any wave")
            continue

        for dep in deps:
            dep_wave = item_wave.get(dep) or item_wave.get(str(dep))

            if dep_wave is None:
                # Dependency might use a descriptive name not matching item names
                continue
            elif dep_wave > my_wave:
                errors.append(
                    f"{name} (wave {my_wave}) depends on {dep} (wave {dep_wave})"
                )
            elif dep_wave == my_wave:
                warnings.append(
                    f"{name} and dependency {dep} both in wave {my_wave}"
                )

    # Circular dependency check via topological sort
    graph: dict[str, list[str]] = {item.get("name", str(item.get("id", ""))): [] for item in items}
    for item in items:
        key = item.get("name", str(item.get("id", "")))
        deps = item.get("dependencies", item.get("depends_on", []))
        if deps is None:
            deps = []
        for dep in deps:
            dep_str = str(dep)
            if dep_str in graph:
                graph.setdefault(key, []).append(dep_str)

    if _has_cycle(graph):
        errors.append("Circular dependency detected in items_to_deploy")

    if errors:
        for err in errors:
            findings.append({
                "area": "Wave structure",
                "severity": "red",
                "finding": _truncate(err),
                "suggestion": "Fix dependency order before deployment",
            })
    elif warnings:
        for warn in warnings:
            findings.append({
                "area": "Wave structure",
                "severity": "yellow",
                "finding": _truncate(warn),
                "suggestion": "Consider separating into different waves",
            })
    else:
        findings.append({
            "area": "Wave structure",
            "severity": "green",
            "finding": "All dependencies satisfied in correct wave order",
            "suggestion": "",
        })

    return findings


def _has_cycle(graph: dict) -> bool:
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}

    def dfs(node) -> bool:
        color[node] = GRAY
        for neighbor in graph.get(node, []):
            if neighbor not in color:
                continue
            if color[neighbor] == GRAY:
                return True
            if color[neighbor] == WHITE and dfs(neighbor):
                return True
        color[node] = BLACK
        return False

    return any(dfs(node) for node, c in list(color.items()) if c == WHITE)


def _check_cli_support(items: list[dict]) -> tuple[list[dict], list[dict]]:
    findings: list[dict] = []
    cli_entries: list[dict] = []

    for item in items:
        item_type = item.get("type", "")
        if not item_type:
            continue
        lookup = item_type.lower().strip()
        matched_fab_type = PORTAL_ONLY_ITEMS.get(lookup)

        if matched_fab_type:
            findings.append({
                "area": "CLI support",
                "severity": "yellow",
                "finding": f"{item_type} is portal-only",
                "suggestion": "Document as manual step in deployment",
            })
            cli_entries.append({
                "item_type": item_type,
                "fab_type": matched_fab_type,
                "supported": False,
                "fallback": "portal",
            })

    return findings, cli_entries


def _check_ac_coverage(items: list[dict], acs: list[dict]) -> list[dict]:
    findings: list[dict] = []

    ac_text = " ".join(
        " ".join(str(v) for v in ac.values()) for ac in acs
    ).lower()

    for item in items:
        name = item.get("name", "")
        if not name:
            continue
        if name.lower() not in ac_text:
            findings.append({
                "area": "AC coverage",
                "severity": "yellow",
                "finding": f"{name} has no acceptance criteria",
                "suggestion": f"Add AC for {name} existence check",
            })

    if not findings:
        findings.append({
            "area": "AC coverage",
            "severity": "green",
            "finding": "All items referenced in acceptance criteria",
            "suggestion": "",
        })

    return findings


def _check_item_names(items: list[dict]) -> list[dict]:
    findings: list[dict] = []
    seen_names: dict[str, int] = {}

    for item in items:
        name = item.get("name", "")
        if not name:
            continue

        lower_name = name.lower()
        if lower_name in seen_names:
            findings.append({
                "area": "Item naming",
                "severity": "red",
                "finding": f"Duplicate item name: {name}",
                "suggestion": "Use unique names for all items",
            })
        seen_names[lower_name] = seen_names.get(lower_name, 0) + 1

        if not KEBAB_RE.match(name):
            findings.append({
                "area": "Item naming",
                "severity": "yellow",
                "finding": f"{name} is not kebab-case",
                "suggestion": "Rename to kebab-case convention",
            })

    if not findings:
        findings.append({
            "area": "Item naming",
            "severity": "green",
            "finding": "All item names valid and unique",
            "suggestion": "",
        })

    return findings


def _check_wave_count(items: list[dict], waves: list[dict]) -> tuple[list[dict], dict]:
    findings: list[dict] = []
    total_waves = len(waves)
    merge_opportunities: list[dict] = []

    item_deps: dict[str, list[str]] = {}
    for item in items:
        key = str(item.get("name", item.get("id", "")))
        deps = item.get("dependencies", item.get("depends_on", []))
        item_deps[key] = [str(d) for d in (deps or [])]

    sorted_waves = sorted(waves, key=lambda w: int(w.get("id", 0)))
    for idx, wave in enumerate(sorted_waves):
        wave_id = int(wave.get("id", 0))
        wave_items = [str(x) for x in wave.get("items", [])]
        if len(wave_items) != 1:
            continue

        solo_item = wave_items[0]

        if idx > 0:
            prev_wave = sorted_waves[idx - 1]
            prev_wave_id = int(prev_wave.get("id", 0))
            prev_items = [str(x) for x in prev_wave.get("items", [])]
            deps_of_solo = item_deps.get(solo_item, [])
            depends_on_prev = any(d in prev_items for d in deps_of_solo)

            if not depends_on_prev:
                merge_opportunities.append({
                    "description": f"Merge wave {wave_id} into wave {prev_wave_id}",
                    "reason": f"Single item, no dependency on wave {prev_wave_id} items",
                })

        if idx < len(sorted_waves) - 1 and not merge_opportunities:
            next_wave = sorted_waves[idx + 1]
            next_wave_id = int(next_wave.get("id", 0))
            next_items = [str(x) for x in next_wave.get("items", [])]
            next_depends_on_solo = any(
                solo_item in item_deps.get(ni, []) for ni in next_items
            )
            if not next_depends_on_solo:
                merge_opportunities.append({
                    "description": f"Merge wave {wave_id} into wave {next_wave_id}",
                    "reason": f"Single item, no blockers for wave {next_wave_id}",
                })

    proposed = total_waves - len(merge_opportunities)
    wave_opt = {
        "current_waves": total_waves,
        "proposed_waves": max(proposed, 1),
        "changes": merge_opportunities,
    }

    if merge_opportunities:
        findings.append({
            "area": "Wave optimization",
            "severity": "yellow",
            "finding": f"{len(merge_opportunities)} wave merge opportunity(s) found",
            "suggestion": "Review merge suggestions in wave_optimization",
        })
    else:
        findings.append({
            "area": "Wave optimization",
            "severity": "green",
            "finding": f"{total_waves} waves look optimal",
            "suggestion": "",
        })

    return findings, wave_opt


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _truncate(text: str, max_words: int = 15) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words])


def _check_diagram(content: str, items: list[dict]) -> list[dict]:
    """Validate the architecture diagram in the handoff for structural correctness."""
    findings: list[dict] = []

    # Extract diagram from Architecture Diagram section
    section = re.split(r"##\s+Architecture Diagram", content, maxsplit=1)
    if len(section) < 2:
        findings.append({
            "area": "Diagram",
            "severity": "yellow",
            "finding": "No Architecture Diagram section found",
            "suggestion": "Add ## Architecture Diagram with ASCII data flow",
        })
        return findings

    match = re.search(r"```\s*\n(.*?)```", section[1], re.DOTALL)
    if not match:
        findings.append({
            "area": "Diagram",
            "severity": "yellow",
            "finding": "No code block found in Architecture Diagram section",
            "suggestion": "Wrap diagram in ``` code fences",
        })
        return findings

    diagram = match.group(1)
    stripped = diagram.strip()
    if not stripped or "Replace this block" in stripped:
        findings.append({
            "area": "Diagram",
            "severity": "yellow",
            "finding": "Architecture diagram is empty or placeholder",
            "suggestion": "Draw project-specific data flow diagram",
        })
        return findings

    # Check box balance
    top_left = sum(line.count("┌") for line in diagram.split("\n"))
    bot_right = sum(line.count("┘") for line in diagram.split("\n"))
    top_right = sum(line.count("┐") for line in diagram.split("\n"))
    bot_left = sum(line.count("└") for line in diagram.split("\n"))

    if top_left != bot_right or top_right != bot_left:
        findings.append({
            "area": "Diagram",
            "severity": "yellow",
            "finding": f"Unbalanced box corners: ┌={top_left} ┘={bot_right} ┐={top_right} └={bot_left}",
            "suggestion": "Fix box-drawing characters to close all boxes",
        })
    else:
        findings.append({
            "area": "Diagram",
            "severity": "green",
            "finding": f"Diagram box characters balanced ({top_left} boxes)",
            "suggestion": "",
        })

    # Check item name coverage
    item_names = [i.get("name", "") for i in items if i.get("name")]
    diagram_lower = diagram.lower()
    missing = [n for n in item_names if n.lower() not in diagram_lower]
    if missing:
        findings.append({
            "area": "Diagram",
            "severity": "yellow",
            "finding": f"{len(missing)} item(s) missing from diagram: {', '.join(missing[:5])}",
            "suggestion": "Ensure all items appear in the architecture diagram",
        })

    return findings


# ---------------------------------------------------------------------------
# Core prescan function
# ---------------------------------------------------------------------------

def prescan(handoff_path: str) -> dict:
    """Run all deterministic checks on an architecture handoff.

    Returns a dict matching the engineer-review.md schema, augmented with
    scan_type: automated.
    """
    with open(handoff_path, "r", encoding="utf-8") as f:
        content = f.read()

    frontmatter = _extract_frontmatter(content)
    yaml_blocks = _extract_yaml_blocks(content)

    project = frontmatter.get("project", "unknown")
    task_flow = frontmatter.get("task_flow", "unknown")

    # Fall back to markdown headers if no YAML frontmatter
    if project == "unknown":
        m = re.search(r"\*\*Project:\*\*\s*(.+)", content)
        if m:
            project = m.group(1).strip()
    if task_flow == "unknown":
        m = re.search(r"\*\*Task Flow:\*\*\s*(.+)", content)
        if m:
            task_flow = m.group(1).strip()

    # Support both key conventions: items/items_to_deploy, waves/deployment_waves
    items = (_find_block(yaml_blocks, "items")
             or _find_block(yaml_blocks, "items_to_deploy") or [])
    waves = (_find_block(yaml_blocks, "waves")
             or _find_block(yaml_blocks, "deployment_waves") or [])
    acs = _find_block(yaml_blocks, "acceptance_criteria") or []

    # Normalize key variants (scaffolder uses item_name/item_type/wave_number)
    for idx, item in enumerate(items):
        if "item_name" in item and "name" not in item:
            item["name"] = item["item_name"]
        if "item_type" in item and "type" not in item:
            item["type"] = item["item_type"]
        if "id" not in item:
            item["id"] = idx + 1
    for wave in waves:
        if "wave_number" in wave and "id" not in wave:
            wave["id"] = wave["wave_number"]

    warnings: list[str] = []
    if not items:
        warnings.append("No items_to_deploy block found")
    if not waves:
        warnings.append("No deployment_waves block found")
    if not acs:
        warnings.append("No acceptance_criteria block found")

    all_findings: list[dict] = []

    # 1. Wave dependency validation
    if items and waves:
        all_findings.extend(_check_wave_dependencies(items, waves))
    elif not items or not waves:
        all_findings.append({
            "area": "Wave structure",
            "severity": "yellow",
            "finding": "Cannot validate — missing items or waves block",
            "suggestion": "Ensure handoff has items and waves YAML blocks",
        })

    # 2. CLI support cross-reference
    cli_entries: list[dict] = []
    if items:
        cli_findings, cli_entries = _check_cli_support(items)
        all_findings.extend(cli_findings)

    # 3. AC coverage check
    if items and acs:
        all_findings.extend(_check_ac_coverage(items, acs))
    elif items and not acs:
        all_findings.append({
            "area": "AC coverage",
            "severity": "yellow",
            "finding": "No acceptance_criteria block — cannot verify coverage",
            "suggestion": "Add acceptance_criteria YAML block to handoff",
        })

    # 4. Item name validation
    if items:
        all_findings.extend(_check_item_names(items))

    # 5. Wave count assessment
    wave_opt: dict = {"current_waves": 0, "proposed_waves": 0, "changes": []}
    if items and waves:
        wave_findings, wave_opt = _check_wave_count(items, waves)
        all_findings.extend(wave_findings)

    # 6. Architecture diagram validation
    diagram_findings = _check_diagram(content, items)
    all_findings.extend(diagram_findings)

    # Number findings
    for idx, f in enumerate(all_findings, start=1):
        f["id"] = f"F-{idx}"

    # Classify findings
    must_fix = [f["id"] for f in all_findings if f["severity"] == "red"]
    should_fix = [f["id"] for f in all_findings if f["severity"] == "yellow"]
    no_change = [f["id"] for f in all_findings if f["severity"] == "green"]
    assessment = "needs-changes" if must_fix else "ready"

    # Emit warnings as extra findings
    for w in warnings:
        idx = len(all_findings) + 1
        fid = f"F-{idx}"
        all_findings.append({
            "id": fid,
            "area": "Parse warning",
            "severity": "yellow",
            "finding": w,
            "suggestion": "Check handoff file structure",
        })
        should_fix.append(fid)

    return {
        "project": project,
        "task_flow": task_flow,
        "review_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "architecture_version": "draft",
        "scan_type": "automated",
        "findings": all_findings,
        "wave_optimization": wave_opt,
        "cli_verification": cli_entries,
        "prerequisites": [],
        "assessment": assessment,
        "must_fix": must_fix,
        "should_fix": should_fix,
        "no_change": no_change,
    }


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def _yaml_str(value: str) -> str:
    if not value:
        return '""'
    if any(c in value for c in (":", "#", "'", '"', "\n", "[", "]", "{", "}")):
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'
    return f'"{value}"'


def _to_yaml(data: dict) -> str:
    lines: list[str] = []
    lines.append(f"project: {_yaml_str(data['project'])}")
    lines.append(f"task_flow: {_yaml_str(data['task_flow'])}")
    lines.append(f"review_date: {_yaml_str(data['review_date'])}")
    lines.append(f"architecture_version: {data['architecture_version']}")
    lines.append(f"scan_type: {data['scan_type']}")
    lines.append("")

    lines.append("findings:")
    for f in data["findings"]:
        lines.append(f"  - id: {f['id']}")
        lines.append(f"    area: {_yaml_str(f['area'])}")
        lines.append(f"    severity: {f['severity']}")
        lines.append(f"    finding: {_yaml_str(f['finding'])}")
        lines.append(f"    suggestion: {_yaml_str(f.get('suggestion', ''))}")
    lines.append("")

    wo = data["wave_optimization"]
    lines.append("wave_optimization:")
    lines.append(f"  current_waves: {wo['current_waves']}")
    lines.append(f"  proposed_waves: {wo['proposed_waves']}")
    if wo["changes"]:
        lines.append("  changes:")
        for ch in wo["changes"]:
            lines.append(f"    - description: {_yaml_str(ch['description'])}")
            lines.append(f"      reason: {_yaml_str(ch['reason'])}")
    else:
        lines.append("  changes: []")
    lines.append("")

    lines.append("cli_verification:")
    if data["cli_verification"]:
        for entry in data["cli_verification"]:
            lines.append(f"  - item_type: {_yaml_str(entry['item_type'])}")
            lines.append(f"    fab_type: {entry['fab_type']}")
            lines.append(f"    supported: {'true' if entry['supported'] else 'false'}")
            lines.append(f"    fallback: {entry.get('fallback', '')}")
    else:
        lines.append("  []")
    lines.append("")

    lines.append("prerequisites: []")
    lines.append("")

    lines.append(f"assessment: {data['assessment']}")
    lines.append(f"must_fix: {json.dumps(data['must_fix'])}")
    lines.append(f"should_fix: {json.dumps(data['should_fix'])}")
    lines.append(f"no_change: {json.dumps(data['no_change'])}")

    return "\n".join(lines) + "\n"


def _to_json(data: dict) -> str:
    return json.dumps(data, indent=2) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deterministic pre-scan of architecture handoff for review"
    )
    parser.add_argument(
        "--handoff", required=True,
        help="Path to architecture-handoff.md",
    )
    parser.add_argument(
        "--output", default=None,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--format", choices=["yaml", "json"], default="yaml",
        help="Output format (default: yaml)",
    )
    args = parser.parse_args()

    result = prescan(args.handoff)

    text = _to_yaml(result) if args.format == "yaml" else _to_json(result)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
