#!/usr/bin/env python3
"""
Fabric Task Flows — Validation Checklist Generator

Parses a deployment-handoff.md and generates a manual configuration checklist.
Trusts that deployment succeeded (fabric-cicd is deterministic) — no redundant
REST API existence checks.

Usage:
    python validate-items.py <deployment-handoff.md>
    python validate-items.py <deployment-handoff.md> > validation-checklist.yaml

No external dependencies required.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Load registries
# ---------------------------------------------------------------------------

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / "_shared" / "lib"))
from paths import REPO_ROOT
from registry_loader import load_registry

REGISTRY_DIR = REPO_ROOT / "_shared" / "registry"


def _load_validation_checklists() -> dict:
    """Load task-flow-specific validation checklists."""
    path = REGISTRY_DIR / "validation-checklists.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _get_manual_steps(task_flow: str, checklists: dict) -> list[dict]:
    """Get manual steps for a task flow from the checklist."""
    tf_data = checklists.get("task_flows", {}).get(task_flow, {})
    return tf_data.get("manual_steps", [])


# ---------------------------------------------------------------------------
# Handoff parser
# ---------------------------------------------------------------------------

def _parse_handoff(path: str) -> tuple[str, str, str, list[dict]]:
    """Parse deployment-handoff.md → (project, task_flow, workspace, items)."""
    text = Path(path).read_text(encoding="utf-8")
    items: list[dict] = []

    # Extract metadata from YAML block
    project = ""
    task_flow = ""
    workspace = ""

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("project:"):
            project = stripped.split(":", 1)[1].strip().strip('"').strip("'")
        elif stripped.startswith("task_flow:"):
            task_flow = stripped.split(":", 1)[1].strip().strip('"').strip("'")
        elif stripped.startswith("workspace:"):
            workspace = stripped.split(":", 1)[1].strip().strip('"').strip("'")

    # Parse items block
    in_items = False
    current: dict | None = None

    for line in text.splitlines():
        stripped = line.strip()

        if stripped in ("items_deployed:", "items:"):
            in_items = True
            continue

        if in_items and stripped.startswith("- "):
            if current:
                items.append(current)
            current = {"name": "", "type": "", "wave": "", "status": "deployed"}

            # Inline format: - { name: ..., type: ... }
            if "{" in stripped:
                mapping = stripped[stripped.index("{"):].strip("{}")
                for part in re.split(r",\s*(?=\w+\s*:)", mapping):
                    m = re.match(r"(\w+)\s*:\s*(.*)", part.strip())
                    if m:
                        key, val = m.group(1), m.group(2).strip().strip('"').strip("'")
                        if key in ("name", "item_name"):
                            current["name"] = val
                        elif key in ("type", "item_type"):
                            current["type"] = val
                        elif key == "wave":
                            current["wave"] = val
                        elif key == "status":
                            current["status"] = val
                continue

            # Multi-line: - name: value
            rest = stripped[2:].strip()
            m = re.match(r"(\w+)\s*:\s*(.*)", rest)
            if m:
                key, val = m.group(1), m.group(2).strip().strip('"').strip("'")
                if key in ("name", "item_name"):
                    current["name"] = val
                elif key in ("type", "item_type"):
                    current["type"] = val
                elif key == "wave":
                    current["wave"] = val
                elif key == "status":
                    current["status"] = val
            continue

        if in_items and current and ":" in stripped and not stripped.startswith("#"):
            m = re.match(r"(\w+)\s*:\s*(.*)", stripped)
            if m:
                key, val = m.group(1), m.group(2).strip().strip('"').strip("'")
                if key in ("name", "item_name"):
                    current["name"] = val
                elif key in ("type", "item_type"):
                    current["type"] = val
                elif key == "wave":
                    current["wave"] = val
                elif key == "status":
                    current["status"] = val

        # End of items block
        if in_items and stripped and not stripped.startswith("-") and not stripped.startswith("#") and ":" in stripped:
            if stripped.split(":")[0].strip() not in ("name", "item_name", "type", "item_type", "wave", "status", "command", "notes", "deployment_time"):
                in_items = False

    if current:
        items.append(current)

    return project, task_flow, workspace, items


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

sys.path.insert(0, str(REPO_ROOT / "_shared" / "lib"))
from banner import print_banner


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate post-deployment configuration checklist (no API calls)"
    )
    parser.add_argument("handoff", help="Path to deployment-handoff.md")
    args = parser.parse_args()

    if not Path(args.handoff).exists():
        print(f"Error: File not found: {args.handoff}", file=sys.stderr)
        sys.exit(2)

    # Load registries
    checklists = _load_validation_checklists()

    # Parse handoff
    project, task_flow, workspace, items = _parse_handoff(args.handoff)

    if not items:
        print("Error: No items found in the deployment handoff.", file=sys.stderr)
        sys.exit(2)

    # Show banner
    print_banner(project=project, task_flow=task_flow, mode="Config Checklist")
    print(f"  Handoff:   {args.handoff}", file=sys.stderr)
    print(f"  Workspace: {workspace}", file=sys.stderr)
    print(f"  Items:     {len(items)}", file=sys.stderr)
    print("  Method:    Trust deploy, check config only", file=sys.stderr)
    print("", file=sys.stderr)

    # Get manual steps for this task flow
    manual_steps = _get_manual_steps(task_flow, checklists)
    
    # Match deployed items to manual steps
    config_tasks: list[dict] = []
    deployed_types = {item["type"] for item in items}
    
    for step in manual_steps:
        item_type = step.get("item_type", "")
        action = step.get("action", "")
        # Check if this item type was deployed
        if any(t in deployed_types or item_type.lower() in t.lower() 
               for t in deployed_types):
            # Find the matching deployed item(s)
            for item in items:
                if item_type.lower() in item["type"].lower() or item["type"].lower() in item_type.lower():
                    config_tasks.append({
                        "item_name": item["name"],
                        "item_type": item["type"],
                        "action": action,
                        "confirmed": False
                    })

    # Summary
    print("", file=sys.stderr)
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", file=sys.stderr)
    print(f"  {len(items)} items deployed, {len(config_tasks)} manual config steps", file=sys.stderr)
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", file=sys.stderr)
    print("", file=sys.stderr)

    # Output YAML to stdout
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print("# Validation Report")
    print(f"# Generated: {today}")
    print("# Deployment trusted (fabric-cicd deterministic) — config checks only")
    print()
    print(f'project: "{project}"')
    print(f'task_flow: "{task_flow}"')
    print(f'workspace: "{workspace}"')
    print(f'date: "{today}"')
    print(f"status: pending  # pending | passed | failed")
    print()
    print(f"items_deployed: {len(items)}")
    print()
    print("config_checklist:")

    if config_tasks:
        for i, task in enumerate(config_tasks, 1):
            print(f"  - id: CFG-{i:02d}")
            print(f'    item: "{task["item_name"]}"')
            print(f'    type: "{task["item_type"]}"')
            print(f'    action: "{task["action"]}"')
            print(f"    confirmed: false")
    else:
        print("  []  # No manual config steps — all items are fully automated")

    print()
    print("smoke_tests:")
    print("  - test: Query returns data")
    print("    passed: false")
    print("  - test: Pipeline executes successfully")
    print("    passed: false")
    print("  - test: Report renders correctly")
    print("    passed: false")
    print()
    print("next_steps:")
    if config_tasks:
        print(f'  - "Complete {len(config_tasks)} manual configuration step(s)"')
    print('  - "Run smoke tests to verify data flow"')
    print('  - "Mark status as passed when all checks complete"')

    sys.exit(0)


if __name__ == "__main__":
    main()
