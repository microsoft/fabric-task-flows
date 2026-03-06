#!/usr/bin/env python3
"""Generate PowerShell item-type constants from _shared/item-type-registry.json.

Usage:
    python scripts/generate-ps1-types.py            # prints to stdout
    python scripts/generate-ps1-types.py -o FILE    # writes to FILE

The output is a PowerShell snippet that replaces the hand-maintained
$FabTypes, $PortalOnly, and Get-Phase blocks in validate-items.ps1.
"""
import argparse
import sys
from pathlib import Path

# Ensure scripts/ is on sys.path for registry_loader
sys.path.insert(0, str(Path(__file__).resolve().parent))
from registry_loader import load_registry


def generate(registry: dict) -> str:
    lines = []
    lines.append("# --- AUTO-GENERATED from _shared/item-type-registry.json ---")
    lines.append("# Regenerate: python scripts/generate-ps1-types.py")
    lines.append("# Do NOT edit manually. See _shared/agent-boundaries.md.")
    lines.append("")

    # $FabTypes — CLI-supported types (used for fab exists/get/ls)
    lines.append("$FabTypes = @{")
    for _key, data in sorted(registry.items()):
        if data.get("cli_supported"):
            fab = data["fab_type"]
            padded = f'"{fab}"'.ljust(25)
            lines.append(f"  {padded}= \"{fab}\"")
            # Add aliases that differ from fab_type
            for alias in data.get("aliases", []):
                canon = alias.title().replace(" ", "").replace("-", "")
                if canon != fab:
                    padded_a = f'"{canon}"'.ljust(25)
                    lines.append(f"  {padded_a}= \"{fab}\"")
    lines.append("}")
    lines.append("")

    # $PortalOnly — items that cannot be created via fab mkdir
    portal = sorted(
        {data["fab_type"] for data in registry.values() if not data.get("mkdir_supported", False)}
    )
    lines.append("$PortalOnly = @(")
    row = "  "
    for i, t in enumerate(portal):
        entry = f'"{t}"'
        if i < len(portal) - 1:
            entry += ", "
        if len(row) + len(entry) > 85:
            lines.append(row.rstrip())
            row = "  " + entry
        else:
            row += entry
    lines.append(row.rstrip())
    lines.append(")")
    lines.append("")

    # Get-Phase function
    phase_groups: dict[str, list[str]] = {}
    for _key, data in registry.items():
        phase = data.get("phase", "Other")
        if phase == "TBD":
            phase = "Other"
        phase_groups.setdefault(phase, set()).add(data["fab_type"])

    lines.append("function Get-Phase {")
    lines.append("  param([string]$ItemType)")
    lines.append("  switch ($ItemType) {")
    for phase in ["Foundation", "Environment", "Ingestion", "Transformation", "Visualization", "ML"]:
        types = sorted(phase_groups.get(phase, []))
        if not types:
            continue
        if len(types) == 1:
            lines.append(f'    "{types[0]}" {{ return "{phase}" }}')
        else:
            items = ", ".join(f'"{t}"' for t in types)
            lines.append(f'    {{ $_ -in @({items}) }} {{ return "{phase}" }}')
    lines.append('    default { return "Other" }')
    lines.append("  }")
    lines.append("}")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Generate PS1 item-type constants from registry")
    parser.add_argument("-o", "--output", help="Write to file instead of stdout")
    args = parser.parse_args()

    registry = load_registry()
    snippet = generate(registry)

    if args.output:
        Path(args.output).write_text(snippet, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(snippet, end="")


if __name__ == "__main__":
    main()
