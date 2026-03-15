#!/usr/bin/env python3
"""
Deterministic architecture diagram generator.

Reads architecture-handoff.md, parses items/waves YAML, and generates a clean
ASCII diagram with validated box-drawing characters. Items are grouped by
architectural layer and connected by arrows based on depends_on relationships.

Usage:
    python .github/skills/fabric-design/scripts/diagram-gen.py --handoff projects/my-project/docs/architecture-handoff.md
    python .github/skills/fabric-design/scripts/diagram-gen.py --handoff handoff.md --output diagram.txt

Importable:
    from diagram_gen import generate_diagram
    text = generate_diagram("projects/my-project/docs/architecture-handoff.md")
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
# Item type → architectural layer mapping (loaded from shared config)
# ---------------------------------------------------------------------------

import json as _json

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_SCRIPT_CONFIG_PATH = _REPO_ROOT / "_shared" / "registry" / "script-config.json"
with open(_SCRIPT_CONFIG_PATH, encoding="utf-8") as _f:
    _script_config = _json.load(_f)
LAYER_MAP: dict[str, str] = _script_config["layer_map"]["values"]

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

    # --- Build layer-based layout ---
    max_content_width = 116  # 120 - 4 for "║ " and " ║"

    output_lines: list[str] = []

    # Title bar
    title = f"ARCHITECTURE: {project} ({task_flow})"
    border = "═" * max_content_width
    output_lines.append(f"╔═{border}═╗")
    output_lines.append(f"║ {title.center(max_content_width)} ║")
    output_lines.append(f"╠═{border}═╣")

    # Group items by architectural layer
    layer_items: dict[str, list[dict]] = {}
    for item in items_raw:
        layer_items.setdefault(item["_layer"], []).append(item)

    active_layers = [l for l in LAYER_ORDER if l in layer_items]

    for layer_idx, layer in enumerate(active_layers):
        items = layer_items[layer]
        label = LAYER_LABELS.get(layer, layer)

        # Collect wave numbers in this layer for the header subtitle
        wave_nums = sorted(set(i["_wave"] for i in items if i["_wave"] is not None))
        wave_annotation = ", ".join(f"Wave {w}" for w in wave_nums)

        # Layer header: ░░ LABEL (Wave N) ░░░░░░░░░
        header_core = f"░░ {label}"
        if wave_annotation:
            header_core += f" ({wave_annotation})"
        header_core += " "
        fill = max(max_content_width - 4 - len(header_core), 0)
        header_line = "  " + header_core + "░" * fill

        output_lines.append(f"║ {' ' * max_content_width} ║")
        output_lines.append(f"║ {header_line.ljust(max_content_width)} ║")

        # Lay out items horizontally within the layer
        items_per_row = max(1, max_content_width // (box_width + 4))
        rows = [items[i:i + items_per_row]
                for i in range(0, len(items), items_per_row)]

        for row_items in rows:
            boxes: list[list[str]] = []
            for item in row_items:
                box = _make_box(
                    item.get("name", "?"),
                    item.get("type", "?"),
                    item.get("_wave"),
                    box_width,
                )
                boxes.append(box)

            max_h = max(len(b) for b in boxes)
            for line_idx in range(max_h):
                row_line = "  "
                for col_idx, box in enumerate(boxes):
                    cell = box[line_idx] if line_idx < len(box) else " " * box_width
                    if col_idx < len(boxes) - 1:
                        next_item = row_items[col_idx + 1]
                        curr_item = row_items[col_idx]
                        note = next_item.get("note", "")
                        curr_name = curr_item.get("name", "")
                        is_alt = isinstance(note, str) and "Alternative to" in note and curr_name in note
                        if is_alt:
                            connector = "  ◄OR►  " if line_idx == 1 else "        "
                        else:
                            connector = " ── " if line_idx == 1 else "    "
                        row_line += cell + connector
                    else:
                        row_line += cell
                output_lines.append(f"║ {row_line.ljust(max_content_width)} ║")

        # Data-flow arrow between layers
        if layer_idx < len(active_layers) - 1:
            arrow_pos = box_width // 2 + 2
            output_lines.append(f"║ {(' ' * arrow_pos + '│').ljust(max_content_width)} ║")
            output_lines.append(f"║ {(' ' * arrow_pos + '▼').ljust(max_content_width)} ║")

    output_lines.append(f"║ {' ' * max_content_width} ║")

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

    diagram = "\n".join(output_lines)

    # Warn if unresolved OR branches remain — architecture should be decisive
    if "◄OR►" in diagram:
        import sys
        print("  ⚠ Diagram contains unresolved ◄OR► branches — decisions should eliminate alternatives",
              file=sys.stderr)

    return diagram


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
