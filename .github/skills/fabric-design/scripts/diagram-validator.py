#!/usr/bin/env python3
"""
Validates ASCII architecture diagrams for structural correctness.

Checks:
- Balanced box-drawing characters (┌/┐ and └/┘ pairs)
- Line width within max (default 120)
- All expected item names appear in diagram text
- No empty diagram

Usage:
    python .github/skills/fabric-design/scripts/diagram-validator.py --diagram "..." --items "name1,name2"

Importable:
    from diagram_validator import validate_diagram
    result = validate_diagram(diagram_text, expected_items=["item-a", "item-b"])
"""

from __future__ import annotations

import argparse
import sys


def validate_diagram(
    diagram: str,
    expected_items: list[str] | None = None,
    max_width: int = 120,
) -> dict:
    """Validate an ASCII diagram and return findings.

    Returns:
        {
            "valid": bool,
            "findings": [{"id": str, "severity": str, "message": str}, ...],
            "stats": {"lines": int, "max_line_width": int, "box_opens": int, "box_closes": int}
        }
    """
    findings: list[dict] = []
    lines = diagram.split("\n")
    fid = 0

    # --- Empty check ---
    stripped = diagram.strip()
    if not stripped or stripped == "<!-- Replace this block with your ASCII diagram -->":
        fid += 1
        findings.append({
            "id": f"DV-{fid}", "severity": "red",
            "message": "Diagram is empty or placeholder"
        })
        return {"valid": False, "findings": findings,
                "stats": {"lines": 0, "max_line_width": 0,
                           "box_opens": 0, "box_closes": 0}}

    # --- Line width check ---
    max_line_width = max((len(line) for line in lines), default=0)
    over_width = [(i + 1, len(line)) for i, line in enumerate(lines)
                  if len(line) > max_width]
    if over_width:
        fid += 1
        count = len(over_width)
        findings.append({
            "id": f"DV-{fid}", "severity": "yellow",
            "message": f"{count} line(s) exceed {max_width} chars (max: {max_line_width})"
        })

    # --- Box character balance ---
    top_left = sum(line.count("┌") for line in lines)
    top_right = sum(line.count("┐") for line in lines)
    bot_left = sum(line.count("└") for line in lines)
    bot_right = sum(line.count("┘") for line in lines)

    box_opens = top_left
    box_closes = bot_right

    if top_left != bot_right:
        fid += 1
        findings.append({
            "id": f"DV-{fid}", "severity": "yellow",
            "message": f"Unbalanced box corners: ┌={top_left} vs ┘={bot_right}"
        })
    if top_right != bot_left:
        fid += 1
        findings.append({
            "id": f"DV-{fid}", "severity": "yellow",
            "message": f"Unbalanced box corners: ┐={top_right} vs └={bot_left}"
        })
    if top_left != top_right:
        fid += 1
        findings.append({
            "id": f"DV-{fid}", "severity": "yellow",
            "message": f"Unbalanced top corners: ┌={top_left} vs ┐={top_right}"
        })

    # --- Item name coverage ---
    if expected_items:
        diagram_lower = diagram.lower()
        missing = [name for name in expected_items
                   if name.lower() not in diagram_lower]
        if missing:
            fid += 1
            findings.append({
                "id": f"DV-{fid}", "severity": "red",
                "message": f"Missing items in diagram: {', '.join(missing)}"
            })

    valid = all(f["severity"] != "red" for f in findings)
    return {
        "valid": valid,
        "findings": findings,
        "stats": {
            "lines": len(lines),
            "max_line_width": max_line_width,
            "box_opens": box_opens,
            "box_closes": box_closes,
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Validate ASCII architecture diagram")
    parser.add_argument("--diagram", help="Diagram text (or - for stdin)")
    parser.add_argument("--file", help="Read diagram from file (extracts first ``` block)")
    parser.add_argument("--items", help="Comma-separated expected item names")
    parser.add_argument("--max-width", type=int, default=120)
    args = parser.parse_args()

    diagram = ""
    if args.file:
        import re
        with open(args.file, encoding="utf-8") as f:
            content = f.read()
        # Extract first code block after "## Architecture Diagram"
        section = re.split(r"##\s+Architecture Diagram", content, maxsplit=1)
        if len(section) > 1:
            match = re.search(r"```\s*\n(.*?)```", section[1], re.DOTALL)
            if match:
                diagram = match.group(1)
    elif args.diagram == "-":
        diagram = sys.stdin.read()
    elif args.diagram:
        diagram = args.diagram

    items = [i.strip() for i in args.items.split(",")] if args.items else None

    result = validate_diagram(diagram, expected_items=items, max_width=args.max_width)

    for f in result["findings"]:
        severity = f["severity"].upper()
        print(f"  [{severity}] {f['id']}: {f['message']}")

    if result["valid"]:
        print(f"\n  ✅ Diagram valid ({result['stats']['lines']} lines, "
              f"max width {result['stats']['max_line_width']}, "
              f"{result['stats']['box_opens']} boxes)")
    else:
        print("\n  ❌ Diagram has issues")

    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
