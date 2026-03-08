#!/usr/bin/env python3
"""
Pre-fill a test plan by mapping architecture handoff ACs to validation phases.

Reads an architecture-handoff.md (YAML code fences with acceptance_criteria
and items_to_deploy), reads the matching validation checklist from
validation/[task-flow].md, and outputs a pre-filled test-plan.md with
criteria_mapping already populated.

Usage:
    python scripts/test-plan-prefill.py --handoff projects/my-project/prd/architecture-handoff.md
    python scripts/test-plan-prefill.py --handoff projects/my-project/prd/architecture-handoff.md --output test-plan-draft.md

Importable:
    from test_plan_prefill import prefill
    result = prefill("projects/my-project/prd/architecture-handoff.md")
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent

# ---------------------------------------------------------------------------
# Item type → validation phase mapping
# ---------------------------------------------------------------------------

# Phase mapping — loaded from _shared/item-type-registry.json
# Do NOT maintain this dict manually. See CONTRIBUTING.md.
sys.path.insert(0, str(REPO_ROOT / "_shared"))
from registry_loader import build_phase_map

PHASE_MAP: dict[str, tuple[str, int]] = build_phase_map()

# ---------------------------------------------------------------------------
# Item type → fab CLI type for verification commands
# ---------------------------------------------------------------------------

# Item type → fab CLI type — loaded from registry
from registry_loader import build_fab_type_map as _build_fab_types
FAB_TYPES: dict[str, str] = _build_fab_types()


# ---------------------------------------------------------------------------
# YAML extraction from markdown code fences
# ---------------------------------------------------------------------------

_YAML_FENCE_RE = re.compile(
    r"```ya?ml\s*\n(.*?)```", re.DOTALL
)


def _extract_yaml_blocks(text: str) -> list[str]:
    return [m.group(1) for m in _YAML_FENCE_RE.finditer(text)]


def _parse_yaml_list(block: str, key: str) -> list[dict[str, str]]:
    """Parse a simple YAML list under *key* without a YAML library.

    Handles blocks like:
        acceptance_criteria:
          - id: AC-1
            type: structural
            criterion: "Bronze Lakehouse exists"
            verify: "fab exists ws/bronze.Lakehouse"
            target: "bronze-lakehouse"
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
        # Stop when we hit a new top-level key
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


def _parse_yaml_scalar(block: str, key: str) -> str | None:
    match = re.search(rf"^{key}:\s*(.+)$", block, re.MULTILINE)
    if match:
        return match.group(1).strip().strip('"').strip("'")
    return None


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def _parse_frontmatter(text: str) -> dict[str, str]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    fm: dict[str, str] = {}
    for line in match.group(1).splitlines():
        kv = re.match(r"^(\w[\w_]*):\s*(.*)", line)
        if kv:
            fm[kv.group(1)] = kv.group(2).strip().strip('"').strip("'")
    return fm


# ---------------------------------------------------------------------------
# Validation checklist phase parsing
# ---------------------------------------------------------------------------

_PHASE_HEADING_RE = re.compile(r"^###\s+Phase\s+(\d+):\s*(.+)", re.MULTILINE)


def _parse_checklist_phases(checklist_text: str) -> dict[int, str]:
    """Return {phase_number: phase_name} from validation checklist."""
    phases: dict[int, str] = {}
    for m in _PHASE_HEADING_RE.finditer(checklist_text):
        phases[int(m.group(1))] = m.group(2).strip()
    return phases


# ---------------------------------------------------------------------------
# Handoff parsing
# ---------------------------------------------------------------------------

def _parse_handoff(handoff_text: str) -> dict:
    fm = _parse_frontmatter(handoff_text)
    yaml_blocks = _extract_yaml_blocks(handoff_text)

    project = fm.get("project", "")
    task_flow = fm.get("task_flow", "")
    created = fm.get("created", "")

    acceptance_criteria: list[dict[str, str]] = []
    items_to_deploy: list[dict[str, str]] = []

    for block in yaml_blocks:
        acs = _parse_yaml_list(block, "acceptance_criteria")
        if acs:
            acceptance_criteria = acs
        items = _parse_yaml_list(block, "items") or _parse_yaml_list(block, "items_to_deploy")
        if items:
            items_to_deploy = items

    # Normalize key variants (scaffolder uses item_name/item_type)
    for item in items_to_deploy:
        if "item_name" in item and "name" not in item:
            item["name"] = item["item_name"]
        if "item_type" in item and "type" not in item:
            item["type"] = item["item_type"]

    if not project:
        for block in yaml_blocks:
            val = _parse_yaml_scalar(block, "project")
            if val:
                project = val
                break
        if not project:
            m = re.search(r"\*\*Project:\*\*\s*(.+)", handoff_text)
            if m:
                project = m.group(1).strip()

    if not task_flow:
        for block in yaml_blocks:
            val = _parse_yaml_scalar(block, "task_flow")
            if val:
                task_flow = val
                break
        if not task_flow:
            m = re.search(r"\*\*Task Flow:\*\*\s*(.+)", handoff_text)
            if m:
                task_flow = m.group(1).strip()

    return {
        "project": project,
        "task_flow": task_flow,
        "created": created,
        "acceptance_criteria": acceptance_criteria,
        "items_to_deploy": items_to_deploy,
    }


# ---------------------------------------------------------------------------
# AC → phase + test method mapping
# ---------------------------------------------------------------------------

def _item_type_from_items(target: str, items: list[dict[str, str]]) -> str | None:
    """Find the item type for a given target name/id from items_to_deploy."""
    target_lower = target.lower()
    for item in items:
        name = item.get("name", "").lower()
        item_id = str(item.get("id", "")).lower()
        if target_lower in (name, item_id):
            return item.get("type")
    return None


def _detect_item_type(ac: dict[str, str], items: list[dict[str, str]]) -> str | None:
    """Detect the Fabric item type referenced by an AC."""
    # First try matching via the target field against items_to_deploy
    target = ac.get("target", "")
    if target:
        found = _item_type_from_items(target, items)
        if found:
            return found

    # Scan AC text fields for known item type names (longest match first)
    text_fields = " ".join(
        ac.get(k, "") for k in ("criterion", "verify", "target", "type")
    )
    sorted_types = sorted(PHASE_MAP.keys(), key=len, reverse=True)
    for item_type in sorted_types:
        if re.search(re.escape(item_type), text_fields, re.IGNORECASE):
            return item_type

    return None


def _slugify_phase(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _build_checklist_ref(task_flow: str, phase_num: int, phase_name: str) -> str:
    slug = _slugify_phase(f"phase-{phase_num}-{phase_name}")
    return f"validation/{task_flow}.md#{slug}"


def _build_test_method(
    ac: dict[str, str],
    item_type: str | None,
    items: list[dict[str, str]],
) -> tuple[str, str]:
    """Return (ac_type, test_method) for an AC."""
    ac_type = ac.get("type", "structural")

    if ac_type == "data-flow":
        return "data-flow", "verify after connections configured"

    if item_type is None:
        return ac_type, ac.get("verify", "manual verification required")

    fab_type = FAB_TYPES.get(item_type)
    target = ac.get("target", "")

    # Find item name from items_to_deploy if target is numeric or empty
    item_name = target
    if not item_name or item_name.isdigit():
        for it in items:
            if it.get("type") == item_type or str(it.get("id")) == target:
                item_name = it.get("name", target)
                break

    if not fab_type:
        return ac_type, ac.get("verify", "manual verification required")

    # Structural ACs → fab exists; config ACs → fab get
    criterion_lower = ac.get("criterion", "").lower()
    verify_lower = ac.get("verify", "").lower()
    combined = criterion_lower + " " + verify_lower

    is_config = any(
        kw in combined
        for kw in ("config", "setting", "bound", "attached", "mode", "connection", "publish")
    )

    if is_config:
        return ac_type, f"fab get <ws>/{item_name}.{fab_type} | check config"

    return ac_type, f"fab exists <ws>/{item_name}.{fab_type}"


# ---------------------------------------------------------------------------
# Core prefill function
# ---------------------------------------------------------------------------

def prefill(handoff_path: str) -> dict:
    """Parse handoff and return a pre-filled test plan dict.

    Args:
        handoff_path: Path to the architecture-handoff.md file.

    Returns:
        Dict matching the test-plan schema with criteria_mapping populated.
    """
    handoff_file = Path(handoff_path)
    if not handoff_file.is_absolute():
        handoff_file = REPO_ROOT / handoff_file

    if not handoff_file.exists():
        print(f"Error: handoff not found: {handoff_file}", file=sys.stderr)
        sys.exit(1)

    handoff_text = handoff_file.read_text(encoding="utf-8")
    parsed = _parse_handoff(handoff_text)

    task_flow = parsed["task_flow"]
    project = parsed["project"]
    acs = parsed["acceptance_criteria"]
    items = parsed["items_to_deploy"]
    arch_date = parsed["created"] or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Load validation checklist
    checklist_phases: dict[int, str] = {}
    if task_flow and task_flow != "TBD":
        checklist_path = REPO_ROOT / "validation" / f"{task_flow}.md"
        if checklist_path.exists():
            checklist_text = checklist_path.read_text(encoding="utf-8")
            checklist_phases = _parse_checklist_phases(checklist_text)
        else:
            print(
                f"Warning: validation checklist not found: {checklist_path}",
                file=sys.stderr,
            )

    # Map ACs
    criteria_mapping: list[dict[str, str]] = []
    if not acs:
        print("Warning: no acceptance_criteria found in handoff", file=sys.stderr)

    for ac in acs:
        # Normalize key variants (scaffolder uses ac_id/verification_method)
        if "ac_id" in ac and "id" not in ac:
            ac["id"] = ac["ac_id"]
        if "verification_method" in ac and "verify" not in ac:
            ac["verify"] = ac["verification_method"]
        ac_id = ac.get("id", "")
        item_type = _detect_item_type(ac, items)

        phase_info = PHASE_MAP.get(item_type, None) if item_type else None
        if phase_info:
            phase_name, phase_num = phase_info
            # Use actual checklist phase name if available
            actual_name = checklist_phases.get(phase_num, phase_name)
            checklist_ref = _build_checklist_ref(task_flow, phase_num, actual_name)
        else:
            checklist_ref = ""

        ac_type, test_method = _build_test_method(ac, item_type, items)

        criteria_mapping.append({
            "ac_id": ac_id,
            "type": ac_type,
            "checklist_ref": checklist_ref,
            "test_method": test_method,
        })

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    return {
        "project": project,
        "task_flow": task_flow,
        "architecture_date": arch_date,
        "test_plan_date": today,
        "scan_type": "automated",
        "criteria_mapping": criteria_mapping,
        "critical_verification": ["LLM: Add 3-5 critical verification points"],
        "edge_cases": ["LLM: Add failure scenarios"],
        "blockers": {
            "architecture": [],
            "deployment": [],
        },
    }


# ---------------------------------------------------------------------------
# YAML output (hand-rolled — no external deps)
# ---------------------------------------------------------------------------

def _emit_yaml(data: dict) -> str:
    lines: list[str] = []

    lines.append(f'project: "{data["project"]}"')
    lines.append(f'task_flow: "{data["task_flow"]}"')
    lines.append(f'architecture_date: "{data["architecture_date"]}"')
    lines.append(f'test_plan_date: "{data["test_plan_date"]}"')
    lines.append(f'scan_type: {data["scan_type"]}')
    lines.append("")

    lines.append("criteria_mapping:")
    if data["criteria_mapping"]:
        for entry in data["criteria_mapping"]:
            lines.append(f'  - ac_id: {entry["ac_id"]}')
            lines.append(f'    type: {entry["type"]}')
            lines.append(f'    checklist_ref: "{entry["checklist_ref"]}"')
            lines.append(f'    test_method: "{entry["test_method"]}"')
    else:
        lines.append("  []")

    lines.append("")
    lines.append("critical_verification:")
    for item in data["critical_verification"]:
        lines.append(f'  - "{item}"')

    lines.append("")
    lines.append("edge_cases:")
    for item in data["edge_cases"]:
        lines.append(f'  - "{item}"')

    lines.append("")
    lines.append("blockers:")
    lines.append("  architecture: []")
    lines.append("  deployment: []")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pre-fill test plan from architecture handoff and validation checklist",
    )
    parser.add_argument(
        "--handoff", required=True,
        help="Path to architecture-handoff.md",
    )
    parser.add_argument(
        "--output", default=None,
        help="Output file path (default: stdout)",
    )
    args = parser.parse_args()

    result = prefill(args.handoff)
    yaml_out = _emit_yaml(result)

    if args.output:
        Path(args.output).write_text(yaml_out, encoding="utf-8")
        print(f"✅ Test plan written to {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(yaml_out)


if __name__ == "__main__":
    main()
