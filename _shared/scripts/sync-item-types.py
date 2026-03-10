#!/usr/bin/env python3
"""
Sync item type registry against the installed Fabric CLI.

Optional maintenance script — requires ms-fabric-cli to be installed
separately (it is NOT a project dependency). Use this periodically to
check if Microsoft has added new Fabric item types.

Compares registry/item-type-registry.json against the ItemType enum in the
installed ms-fabric-cli package. Reports new types, missing types, and
naming mismatches.

Usage:
    pip install ms-fabric-cli  # install separately for this script only
    python scripts/sync-item-types.py --check     # exit 1 if drift detected
    python scripts/sync-item-types.py --diff      # Show differences
    python scripts/sync-item-types.py --update    # Add stubs for new types

Exit codes:
    0 — registry is in sync with CLI
    1 — drift detected (new types in CLI not in registry)
    2 — CLI package not installed
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY_PATH = REPO_ROOT / "_shared" / "registry" / "item-type-registry.json"


def _load_registry() -> dict:
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save_registry(data: dict) -> None:
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _get_cli_types() -> dict[str, str]:
    """Import ItemType enum from installed fabric_cli. Returns {name: value}."""
    try:
        from fabric_cli.core.fab_types import ItemType
    except ImportError:
        print("ERROR: ms-fabric-cli not installed. Run: pip install ms-fabric-cli")
        sys.exit(2)

    return {member.name: member.value for member in ItemType}


def _get_cli_format_mapping() -> dict[str, str]:
    """Import format_mapping from installed fabric_cli. Returns {type_value: api_path}."""
    try:
        from fabric_cli.core.fab_types import format_mapping
        return dict(format_mapping)
    except (ImportError, AttributeError):
        return {}


def diff(registry: dict, cli_types: dict[str, str], format_map: dict[str, str]) -> dict:
    """Compare registry against CLI. Returns diff report."""
    reg_types = registry.get("types", {})

    # Registry fab_type values
    reg_fab_types = {data["fab_type"] for data in reg_types.values()}

    # CLI type values
    cli_values = set(cli_types.values())

    in_cli_not_registry = cli_values - reg_fab_types
    in_registry_not_cli = reg_fab_types - cli_values

    # Check for types where we say cli_supported=true but CLI doesn't have them
    # (Removed — cli_supported field deprecated)

    return {
        "in_cli_not_registry": sorted(in_cli_not_registry),
        "in_registry_not_cli": sorted(in_registry_not_cli),
        "cli_version": registry.get("$cli_version", "unknown"),
        "registry_type_count": len(reg_types),
        "cli_type_count": len(cli_types),
    }


def print_diff(report: dict) -> None:
    """Print a human-readable diff report."""
    print(f"Registry types: {report['registry_type_count']}")
    print(f"CLI types:      {report['cli_type_count']}")
    print(f"Registry CLI version: {report['cli_version']}")
    print()

    if report["in_cli_not_registry"]:
        print("⚠️  Types in CLI but NOT in registry (need to add):")
        for t in report["in_cli_not_registry"]:
            print(f"  + {t}")
        print()

    if report["in_registry_not_cli"]:
        print("ℹ️  Types in registry but NOT in CLI enum (portal-only or custom):")
        for t in report["in_registry_not_cli"]:
            print(f"  - {t}")
        print()

    if not report["in_cli_not_registry"]:
        print("✅ Registry is in sync with CLI")


def update_registry(registry: dict, cli_types: dict[str, str],
                    format_map: dict[str, str]) -> int:
    """Add stub entries for types in CLI but not in registry. Returns count added."""
    reg_types = registry.get("types", {})
    reg_fab_types = {data["fab_type"]: name for name, data in reg_types.items()}
    added = 0

    for enum_name, fab_type in cli_types.items():
        if fab_type in reg_fab_types:
            continue

        api_path = format_map.get(fab_type, "items")
        stub = {
            "fab_type": fab_type,
            "api_path": api_path,
            "display_name": fab_type,
            "phase": "TBD",
            "phase_order": 0,
            "task_type": "TBD",
            "aliases": [fab_type.lower()],
            "rest_api": {
                "creatable": False,
                "definition": False
            },
            "availability": "preview",
            "notes": "Auto-added by sync-item-types.py — needs manual metadata review"
        }
        reg_types[fab_type] = stub
        added += 1
        print(f"  + Added stub: {fab_type} (phase=TBD, task_type=TBD)")

    return added


def main():
    parser = argparse.ArgumentParser(description="Sync item type registry against Fabric CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="CI mode: exit 1 if drift detected")
    group.add_argument("--diff", action="store_true", help="Show differences")
    group.add_argument("--update", action="store_true", help="Add stubs for new types")
    args = parser.parse_args()

    registry = _load_registry()
    cli_types = _get_cli_types()
    format_map = _get_cli_format_mapping()
    report = diff(registry, cli_types, format_map)

    if args.diff:
        print_diff(report)

    elif args.check:
        print_diff(report)
        has_drift = bool(report["in_cli_not_registry"])
        sys.exit(1 if has_drift else 0)

    elif args.update:
        count = update_registry(registry, cli_types, format_map)
        if count > 0:
            _save_registry(registry)
            print(f"\n✅ Added {count} stub(s) to registry. Review and fill in phase/task_type metadata.")
        else:
            print("✅ Registry already up to date — no stubs needed.")


if __name__ == "__main__":
    main()
