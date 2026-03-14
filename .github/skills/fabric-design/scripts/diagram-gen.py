#!/usr/bin/env python3
"""
Deterministic architecture diagram generator.

Reads architecture-handoff.md, parses items/waves YAML, and generates a clean
ASCII diagram with validated box-drawing characters. Items are grouped by
architectural layer and connected by arrows based on depends_on relationships.

Usage:
    python .github/skills/fabric-design/scripts/diagram-gen.py --handoff projects/my-project/prd/architecture-handoff.md
    python .github/skills/fabric-design/scripts/diagram-gen.py --handoff handoff.md --output diagram.txt

Importable:
    from diagram_gen import generate_diagram
    text = generate_diagram("projects/my-project/prd/architecture-handoff.md")
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Use shared YAML utilities — never import via another script's wrappers.
_shared_lib = str(Path(__file__).resolve().parent.parent.parent.parent.parent / "_shared" / "lib")
if _shared_lib not in sys.path:
    sys.path.insert(0, _shared_lib)
from yaml_utils import (
    extract_and_parse_yaml_blocks as _extract_yaml_blocks_raw,
    extract_frontmatter as _extract_frontmatter,
    find_block as _find_block_raw,
)


def _extract_yaml_blocks(content: str) -> list[dict]:
    return _extract_yaml_blocks_raw(content)


def _find_block(blocks: list[dict], key: str):
    block = _find_block_raw(blocks, key)
    return block[key] if block is not None else None


# ---------------------------------------------------------------------------
# Item type → architectural layer mapping
# ---------------------------------------------------------------------------

LAYER_MAP: dict[str, str] = {
    # Storage
    "Lakehouse":            "STORAGE",
    "Warehouse":            "STORAGE",
    "Eventhouse":           "STORAGE",
    "SQL Database":         "STORAGE",
    "KQL Database":         "STORAGE",
    "Cosmos DB":            "STORAGE",
    # Ingestion
    "Pipeline":             "INGESTION",
    "Dataflow Gen2":        "INGESTION",
    "Eventstream":          "INGESTION",
    "Copy Job":             "INGESTION",
    # Processing
    "Notebook":             "PROCESSING",
    "KQL Queryset":         "PROCESSING",
    "Spark Job Definition": "PROCESSING",
    "Stored Procedure":     "PROCESSING",
    # Serving
    "Semantic Model":       "SERVING",
    "Real-Time Dashboard":  "SERVING",
    "Report":               "SERVING",
    "Paginated Report":     "SERVING",
    "Dashboard":            "SERVING",
    "Metrics Scorecard":    "SERVING",
    # Compute / Environment
    "Environment":          "COMPUTE",
    # AI / ML
    "Experiment":           "AI_ML",
    "ML Model":             "AI_ML",
    # Alerting
    "Activator":            "ALERTING",
    # API
    "GraphQL API":          "SERVING",
    "User Data Functions":  "SERVING",
}

LAYER_ORDER = ["INGESTION", "STORAGE", "COMPUTE", "PROCESSING", "SERVING", "AI_ML", "ALERTING"]
LAYER_LABELS = {
    "INGESTION":  "INGESTION",
    "STORAGE":    "STORAGE",
    "COMPUTE":    "COMPUTE",
    "PROCESSING": "PROCESSING",
    "SERVING":    "SERVING",
    "AI_ML":      "AI / ML",
    "ALERTING":   "ALERTING",
}


# ---------------------------------------------------------------------------
# Box drawing helpers
# ---------------------------------------------------------------------------

def _make_box(name: str, item_type: str, wave: int | None, width: int) -> list[str]:
    """Create a box with proper box-drawing characters."""
    label = name
    type_line = f"({item_type})"
    wave_line = f"[W{wave}]" if wave is not None else ""

    inner = width - 4  # 2 for "│ " + 2 for " │"
    lines = [
        "┌" + "─" * (width - 2) + "┐",
        "│ " + label.ljust(inner) + " │",
        "│ " + type_line.ljust(inner) + " │",
    ]
    if wave_line:
        lines.append("│ " + wave_line.ljust(inner) + " │")
    lines.append("└" + "─" * (width - 2) + "┘")
    return lines


def _compute_box_width(items: list[dict]) -> int:
    """Compute uniform box width based on longest item name/type."""
    max_len = 0
    for item in items:
        max_len = max(max_len, len(item.get("name", "")))
        max_len = max(max_len, len(f"({item.get('type', '')})"))
    return max(max_len + 6, 20)  # minimum 20 chars wide


# ---------------------------------------------------------------------------
# Diagram generation
# ---------------------------------------------------------------------------

def generate_diagram(handoff_path: str) -> str:
    """Generate an ASCII architecture diagram from a handoff file.

    Returns the diagram text string.
    """
    with open(handoff_path, encoding="utf-8") as f:
        content = f.read()

    frontmatter = _extract_frontmatter(content)
    blocks = _extract_yaml_blocks(content)

    items_raw = _find_block(blocks, "items") or []
    waves_raw = _find_block(blocks, "waves") or []

    if not items_raw:
        return "(No items found in architecture handoff)"

    project = frontmatter.get("project", "unknown")
    task_flow = frontmatter.get("task_flow", "unknown")

    # Build item → wave mapping
    item_wave: dict[str, int] = {}
    wave_names: dict[int, str] = {}
    for wave in waves_raw:
        wid = int(wave.get("id", 0))
        wave_names[wid] = wave.get("name", f"Wave {wid}")
        for witem in wave.get("items", []):
            item_wave[str(witem)] = wid

    # Assign wave to each item
    for item in items_raw:
        item["_wave"] = item_wave.get(item.get("name", ""), None)
        item["_layer"] = LAYER_MAP.get(item.get("type", ""), "PROCESSING")

    # Compute box width — fit within 120 char total
    max_name = max((len(i.get("name", "")) for i in items_raw), default=10)
    max_type = max((len(f"({i.get('type', '')})") for i in items_raw), default=10)
    box_inner = max(max_name, max_type, 14)
    box_width = box_inner + 4  # "│ " + content + " │"

    # --- Build wave-based layout ---
    # Group items by wave, display wave by wave
    waves_sorted = sorted(set(item_wave.values()))
    max_content_width = 116  # 120 - 4 for "║ " and " ║"

    output_lines: list[str] = []

    # Title bar
    title = f"ARCHITECTURE: {project} ({task_flow})"
    border = "═" * max_content_width
    output_lines.append(f"╔═{border}═╗")
    output_lines.append(f"║ {title.center(max_content_width)} ║")
    output_lines.append(f"╠═{border}═╣")

    for wave_id in waves_sorted:
        wave_name = wave_names.get(wave_id, f"Wave {wave_id}")
        wave_items = [i for i in items_raw if i.get("_wave") == wave_id]

        # Wave header
        wave_header = f"  Wave {wave_id}: {wave_name}"
        output_lines.append(f"║ {wave_header.ljust(max_content_width)} ║")
        output_lines.append(f"║ {'─' * len(wave_header) + ' ' * (max_content_width - len(wave_header))} ║")

        # Lay out items in rows of N (fit within width)
        items_per_row = max(1, max_content_width // (box_width + 4))
        rows = [wave_items[i:i + items_per_row]
                for i in range(0, len(wave_items), items_per_row)]

        for row_items in rows:
            # Build boxes for this row
            boxes: list[list[str]] = []
            for item in row_items:
                box = _make_box(
                    item.get("name", "?"),
                    item.get("type", "?"),
                    None,  # wave already shown in header
                    box_width,
                )
                boxes.append(box)

            # Render line by line
            max_h = max(len(b) for b in boxes)
            for line_idx in range(max_h):
                row_line = "  "
                for col_idx, box in enumerate(boxes):
                    cell = box[line_idx] if line_idx < len(box) else " " * box_width
                    if col_idx < len(boxes) - 1:
                        connector = " ── " if line_idx == 1 else "    "
                        row_line += cell + connector
                    else:
                        row_line += cell
                output_lines.append(f"║ {row_line.ljust(max_content_width)} ║")

        # Blank line + down arrow between waves
        if wave_id != waves_sorted[-1]:
            arrow_line = " " * (box_width // 2 + 2) + "│"
            output_lines.append(f"║ {arrow_line.ljust(max_content_width)} ║")
            arrow_line2 = " " * (box_width // 2 + 2) + "▼"
            output_lines.append(f"║ {arrow_line2.ljust(max_content_width)} ║")

    # Footer — blockers
    output_lines.append(f"╠═{border}═╣")
    blockers = frontmatter.get("blockers", {})
    if isinstance(blockers, dict):
        all_blockers = []
        for blist in blockers.values():
            if isinstance(blist, list):
                all_blockers.extend(blist)
        if all_blockers:
            for b in all_blockers:
                bline = f"  ⚠ {b[:max_content_width - 4]}"
                output_lines.append(f"║ {bline.ljust(max_content_width)} ║")
        else:
            output_lines.append(f"║ {'  No blockers'.ljust(max_content_width)} ║")
    output_lines.append(f"╚═{border}═╝")

    return "\n".join(output_lines)

    return "\n".join(output_lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate ASCII architecture diagram from handoff file"
    )
    parser.add_argument("--handoff", required=True,
                        help="Path to architecture-handoff.md")
    parser.add_argument("--output", help="Write diagram to file (otherwise stdout)")
    parser.add_argument("--validate", action="store_true",
                        help="Run diagram-validator on the output")
    args = parser.parse_args()

    diagram = generate_diagram(args.handoff)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(diagram)
        print(f"Diagram written to {args.output}")
    else:
        print(diagram)

    if args.validate:
        _dv = importlib.import_module("diagram-validator")
        validate_diagram = _dv.validate_diagram
        # Extract item names for validation
        with open(args.handoff, encoding="utf-8") as f:
            content = f.read()
        blocks = _extract_yaml_blocks(content)
        items = _find_block(blocks, "items") or []
        item_names = [i.get("name", "") for i in items if i.get("name")]

        result = validate_diagram(diagram, expected_items=item_names)
        for finding in result["findings"]:
            sev = finding["severity"].upper()
            print(f"  [{sev}] {finding['id']}: {finding['message']}")
        if result["valid"]:
            print("  ✅ Diagram validated")
        else:
            print("  ❌ Diagram validation failed")
            sys.exit(1)


if __name__ == "__main__":
    main()
