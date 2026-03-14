#!/usr/bin/env python3
"""
Pre-fill a test plan by mapping architecture handoff ACs to validation phases.

Reads an architecture-handoff.md (YAML code fences with acceptance_criteria
and items_to_deploy), maps items to phases from item-type-registry.json,
and outputs a pre-filled test-plan.md with criteria_mapping already populated.

Usage:
    python .github/skills/fabric-test/scripts/test-plan-prefill.py --handoff _projects/my-project/prd/architecture-handoff.md
    python .github/skills/fabric-test/scripts/test-plan-prefill.py --handoff _projects/my-project/prd/architecture-handoff.md --output test-plan-draft.md

Importable:
    from test_plan_prefill import prefill
    result = prefill("_projects/my-project/prd/architecture-handoff.md")
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Item type → validation phase mapping
# ---------------------------------------------------------------------------

# Phase mapping — loaded from _shared/registry/item-type-registry.json
# Do NOT maintain this dict manually. See CONTRIBUTING.md.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / "_shared" / "lib"))
from paths import REPO_ROOT
from registry_loader import (
    build_phase_map,
    build_fab_type_map as _build_fab_types,
    load_registry as _load_reg,
    build_deploy_method_map,
    build_test_method_map,
)
from yaml_utils import extract_yaml_blocks, parse_yaml_list, parse_yaml_scalar
from text_utils import slugify_phase

PHASE_MAP: dict[str, tuple[str, int]] = build_phase_map()

# ---------------------------------------------------------------------------
# Item type → Fabric type for REST API verification
# ---------------------------------------------------------------------------

FAB_TYPES: dict[str, str] = _build_fab_types()
_REG = _load_reg()
API_PATHS: dict[str, str] = {
    name: data.get("api_path", "items") for name, data in _REG.items()
}
DEPLOY_METHODS: dict[str, dict] = build_deploy_method_map()
TEST_METHOD_MAP: dict[str, dict] = build_test_method_map()


# ---------------------------------------------------------------------------
# YAML extraction — delegated to _shared/yaml_utils.py
# ---------------------------------------------------------------------------

_extract_yaml_blocks = extract_yaml_blocks
_parse_yaml_list = parse_yaml_list
_parse_yaml_scalar = parse_yaml_scalar


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

_CHECKLIST_JSON = REPO_ROOT / "_shared" / "registry" / "validation-checklists.json"


def _load_checklist_phases(task_flow: str) -> dict[int, str]:
    """Return {phase_number: phase_name} from validation-checklists.json."""
    import json

    if not _CHECKLIST_JSON.exists():
        return {}
    data = json.loads(_CHECKLIST_JSON.read_text(encoding="utf-8"))
    tf_data = data.get("task_flows", {}).get(task_flow, {})
    phases = tf_data.get("phases", {})
    # phases is {name: {...}} — assign sequential numbers
    return {i + 1: name for i, name in enumerate(phases)}


def _parse_checklist_phases(checklist_text: str) -> dict[int, str]:
    """Return {phase_number: phase_name} from validation checklist markdown (legacy)."""
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


_slugify_phase = slugify_phase


def _build_phase_ref(phase_num: int, phase_name: str) -> str:
    """Return a phase reference string (just the phase name, since JSON is source of truth)."""
    return f"Phase {phase_num}: {phase_name}"


def _build_test_method(
    ac: dict[str, str],
    item_type: str | None,
    items: list[dict[str, str]],
) -> tuple[str, str, str]:
    """Return (ac_type, test_method, deploy_note) for an AC.

    Uses registry data to generate correct test methods:
    - Portal-only items → manual portal verification
    - Items with definition support → definition check
    - Items without definition → existence check only
    - Preview items → noted in deploy_note
    """
    ac_type = ac.get("type", "structural")

    if ac_type == "data-flow":
        return "data-flow", "verify after connections configured", ""

    if item_type is None:
        return ac_type, ac.get("verify", "manual verification required"), ""

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
        return ac_type, ac.get("verify", "manual verification required"), ""

    # Registry-driven test method generation
    dm = DEPLOY_METHODS.get(item_type) or DEPLOY_METHODS.get(fab_type) or {}
    _tm = TEST_METHOD_MAP.get(item_type) or TEST_METHOD_MAP.get(fab_type) or {}

    deploy_note = ""
    if dm.get("availability") == "preview":
        deploy_note = "Preview feature — may have limited API support"
    if dm.get("method") == "cicd" and dm.get("verified"):
        cicd_note = f"fabric-cicd ({dm.get('strategy')}, verified)"
        deploy_note = f"{deploy_note}; {cicd_note}" if deploy_note else cicd_note
    elif dm.get("strategy") == "unsupported":
        deploy_note = "No fabric-cicd support — REST API or portal only"

    # Portal-only items → manual verification
    if not dm.get("creatable", True):
        return ac_type, f"Verify {item_name} exists in Fabric portal (portal-only)", deploy_note

    api_path = API_PATHS.get(fab_type, API_PATHS.get(item_type, "items"))

    # Determine if this is a config check vs existence check
    criterion_lower = ac.get("criterion", "").lower()
    verify_lower = ac.get("verify", "").lower()
    combined = criterion_lower + " " + verify_lower

    is_config = any(
        kw in combined
        for kw in ("config", "setting", "bound", "attached", "mode", "connection", "publish")
    )

    if is_config and dm.get("has_definition"):
        return ac_type, f"GET /workspaces/{{id}}/{api_path}/{item_name} | check definition", deploy_note
    elif is_config:
        return ac_type, f"GET /workspaces/{{id}}/{api_path} | verify {item_name} exists (no definition API — check config in portal)", deploy_note

    return ac_type, f"GET /workspaces/{{id}}/{api_path} | verify {item_name} exists", deploy_note


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

    # Load validation checklist (JSON registry preferred, legacy markdown fallback)
    checklist_phases: dict[int, str] = {}
    if task_flow and task_flow != "TBD":
        checklist_phases = _load_checklist_phases(task_flow)
        if not checklist_phases:
            # Legacy fallback to markdown files
            checklist_path = REPO_ROOT / "validation" / f"{task_flow}.md"
            if checklist_path.exists():
                checklist_text = checklist_path.read_text(encoding="utf-8")
                checklist_phases = _parse_checklist_phases(checklist_text)
            else:
                print(
                    f"Warning: validation checklist not found for task flow: {task_flow}",
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
            phase_ref = _build_phase_ref(phase_num, actual_name)
        else:
            phase_ref = ""

        ac_type, test_method, deploy_note = _build_test_method(ac, item_type, items)

        entry = {
            "ac_id": ac_id,
            "type": ac_type,
            "phase": phase_ref,
            "test_method": test_method,
        }
        if deploy_note:
            entry["deploy_note"] = deploy_note
        if phase_info:
            entry["_phase_order"] = phase_info[1]
        else:
            entry["_phase_order"] = 99

        criteria_mapping.append(entry)

    # Sort by deployment phase order so test plan follows deployment sequence
    criteria_mapping.sort(key=lambda e: e.get("_phase_order", 99))
    # Remove internal sort key from output
    for entry in criteria_mapping:
        entry.pop("_phase_order", None)

    # Pre-fill critical verification stubs per detected phase
    detected_phases: list[str] = []
    seen_phases: set[str] = set()
    for item in items:
        it = item.get("type", "")
        pi = PHASE_MAP.get(it) or PHASE_MAP.get(it.title()) if it else None
        if pi and pi[0] not in seen_phases:
            seen_phases.add(pi[0])
            detected_phases.append(pi[0])

    phase_cvp_stubs = {
        "Foundation": "All storage items exist and are accessible via REST API",
        "Environment": "Spark environment published and ready for notebook binding",
        "Ingestion": "Data pipeline/eventstream connected to sources and producing data",
        "Transformation": "Notebooks/queries execute successfully against ingested data",
        "Visualization": "Semantic Model bound to storage; Reports render with data",
        "ML": "ML experiment registered and model endpoint responds",
        "IQ": "Data Agent responds to natural language queries",
        "Monitoring": "Alerts configured and triggering on test conditions",
    }
    critical_verification = [
        phase_cvp_stubs[p] for p in detected_phases if p in phase_cvp_stubs
    ]
    if not critical_verification:
        critical_verification = ["LLM: Add 3-5 critical verification points"]

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    return {
        "project": project,
        "task_flow": task_flow,
        "architecture_date": arch_date,
        "test_plan_date": today,
        "scan_type": "automated",
        "criteria_mapping": criteria_mapping,
        "critical_verification": critical_verification,
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
            lines.append(f'    phase: "{entry["phase"]}"')
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
