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
from registry_loader import (
    build_portal_only_items,
    build_deploy_method_map,
    build_test_method_map,
    build_phase_map,
    build_item_notes_map,
)
from yaml_utils import (
    parse_yaml as _parse_yaml,
    extract_and_parse_yaml_blocks,
    extract_frontmatter,
    find_block,
)

PORTAL_ONLY_ITEMS: dict[str, str] = build_portal_only_items()
DEPLOY_METHODS: dict[str, dict] = build_deploy_method_map()
TEST_METHODS: dict[str, dict] = build_test_method_map()
PHASE_MAP: dict[str, tuple[str, int]] = build_phase_map()
ITEM_NOTES: dict[str, str] = build_item_notes_map()

KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


# ---------------------------------------------------------------------------
# YAML parser — delegated to _shared/yaml_utils.py
# Backwards-compatible aliases for diagram-gen.py cross-import.
# ---------------------------------------------------------------------------

def _extract_frontmatter(content: str) -> dict[str, Any]:
    return extract_frontmatter(content)


def _extract_yaml_blocks(content: str) -> list[dict[str, Any]]:
    return extract_and_parse_yaml_blocks(content)


def _find_block(blocks: list[dict[str, Any]], key: str) -> Any:
    block = find_block(blocks, key)
    return block[key] if block is not None else None


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


def _check_phase_ordering(items: list[dict], waves: list[dict]) -> list[dict]:
    """Validate that wave assignments respect registry phase ordering."""
    findings: list[dict] = []

    # Map item → wave
    item_wave: dict[str, int] = {}
    for wave in waves:
        wave_id = int(wave.get("id", 0))
        for witem in wave.get("items", []):
            item_wave[str(witem)] = wave_id

    violations: list[str] = []
    for item in items:
        name = item.get("name", "")
        item_type = item.get("type", "")
        if not name or not item_type:
            continue

        my_wave = item_wave.get(name)
        if my_wave is None:
            continue

        phase_info = PHASE_MAP.get(item_type) or PHASE_MAP.get(item_type.title())
        if not phase_info:
            continue

        phase_name, phase_order = phase_info
        # Check if items with lower phase_order are in later waves
        for other in items:
            other_name = other.get("name", "")
            other_type = other.get("type", "")
            if other_name == name or not other_type:
                continue
            other_wave = item_wave.get(other_name)
            if other_wave is None:
                continue
            other_phase = PHASE_MAP.get(other_type) or PHASE_MAP.get(other_type.title())
            if not other_phase:
                continue
            # If other item has a later phase but an earlier wave
            if other_phase[1] > phase_order and other_wave < my_wave:
                violations.append(
                    f"{other_name} ({other_phase[0]}) in wave {other_wave} "
                    f"before {name} ({phase_name}) in wave {my_wave}"
                )

    if violations:
        # Deduplicate
        for v in list(dict.fromkeys(violations))[:3]:
            findings.append({
                "area": "Phase ordering",
                "severity": "yellow",
                "finding": _truncate(v),
                "suggestion": "Align waves with registry deployment phases",
            })
    else:
        findings.append({
            "area": "Phase ordering",
            "severity": "green",
            "finding": "Wave assignments align with deployment phases",
            "suggestion": "",
        })

    return findings


def _check_deploy_feasibility(items: list[dict]) -> tuple[list[dict], list[dict]]:
    """Enhanced deployment feasibility using full registry metadata.

    Checks REST API creatability, fabric-cicd strategy, availability status,
    and definition support for each item.
    """
    findings: list[dict] = []
    deploy_entries: list[dict] = []

    for item in items:
        item_type = item.get("type", "")
        item_name = item.get("name", item_type)
        if not item_type:
            continue

        dm = DEPLOY_METHODS.get(item_type) or DEPLOY_METHODS.get(item_type.title())
        tm = TEST_METHODS.get(item_type) or TEST_METHODS.get(item_type.title())
        notes = ITEM_NOTES.get(item_type) or ITEM_NOTES.get(item_type.title()) or ""

        if not dm:
            findings.append({
                "area": "Deploy feasibility",
                "severity": "yellow",
                "finding": f"{item_type} not found in item registry",
                "suggestion": "Verify item type name matches registry",
            })
            continue

        entry = {
            "item": item_name,
            "type": item_type,
            "deploy_method": dm["method"],
            "strategy": dm.get("strategy"),
            "verified": dm.get("verified", False),
            "availability": dm.get("availability", "ga"),
            "test_method": (tm or {}).get("verify_method", "").replace("{item}", item_name),
            "has_definition": dm.get("has_definition", False),
            "phase": (tm or {}).get("phase", "Other"),
            "phase_order": (tm or {}).get("phase_order", 99),
        }
        if notes:
            entry["notes"] = notes
        deploy_entries.append(entry)

        # Portal-only: cannot be created via REST API
        if dm["method"] == "portal":
            findings.append({
                "area": "Deploy feasibility",
                "severity": "yellow",
                "finding": f"{item_type} is portal-only (no REST API)",
                "suggestion": "Document as manual step in deployment",
            })

        # fabric-cicd unsupported
        elif dm.get("strategy") == "unsupported":
            findings.append({
                "area": "Deploy feasibility",
                "severity": "yellow",
                "finding": f"{item_type} not supported by fabric-cicd",
                "suggestion": "Use REST API or portal for this item",
            })

        # Preview feature
        if dm.get("availability") == "preview":
            findings.append({
                "area": "Deploy feasibility",
                "severity": "yellow",
                "finding": f"{item_type} is a preview feature",
                "suggestion": "Note preview limitations in deployment plan",
            })

        # Creatable but no definition support
        if dm.get("creatable") and not dm.get("has_definition"):
            findings.append({
                "area": "Deploy feasibility",
                "severity": "green",
                "finding": f"{item_type} needs portal config post-creation",
                "suggestion": "Plan manual configuration after REST API create",
            })

    if not findings:
        findings.append({
            "area": "Deploy feasibility",
            "severity": "green",
            "finding": "All items fully deployable via REST API or fabric-cicd",
            "suggestion": "",
        })

    return findings, deploy_entries


def _check_naming_safety(items: list[dict]) -> list[dict]:
    """Check for Fabric naming restrictions (hyphens rejected by multiple types)."""
    findings: list[dict] = []

    for item in items:
        name = item.get("name", "")
        item_type = item.get("type", "")
        if not name or "-" not in name:
            continue

        safe_name = name.replace("-", "_")
        findings.append({
            "area": "Naming safety",
            "severity": "yellow",
            "finding": f"{name} contains hyphens (Fabric may reject)",
            "suggestion": f"Rename to {safe_name}",
        })

    if not findings:
        findings.append({
            "area": "Naming safety",
            "severity": "green",
            "finding": "All item names are Fabric-safe (no hyphens)",
            "suggestion": "",
        })

    return findings


def _check_ac_test_methods(items: list[dict], acs: list[dict]) -> list[dict]:
    """Validate that AC verification methods match registry capabilities."""
    findings: list[dict] = []

    for ac in acs:
        verify_text = str(ac.get("verify", "")).lower()
        target = ac.get("target", "")
        ac_id = ac.get("id", "?")

        if not verify_text:
            continue

        # Detect which item this AC targets
        detected_type = None
        for item in items:
            item_name = item.get("name", "")
            if item_name and item_name.lower() in verify_text:
                detected_type = item.get("type", "")
                break
            if target and target.lower() == item_name.lower():
                detected_type = item.get("type", "")
                break

        if not detected_type:
            continue

        dm = DEPLOY_METHODS.get(detected_type) or DEPLOY_METHODS.get(detected_type.title())
        if not dm:
            continue

        # AC says REST API but item is portal-only
        uses_rest = "rest api" in verify_text or "get /" in verify_text
        if uses_rest and not dm.get("creatable", False):
            findings.append({
                "area": "AC feasibility",
                "severity": "red",
                "finding": f"{ac_id} uses REST API but {detected_type} is portal-only",
                "suggestion": "Change verify method to portal check",
            })

        # AC says "check definition" but item has no definition support
        checks_def = "definition" in verify_text or "config" in verify_text
        if checks_def and not dm.get("has_definition", False):
            findings.append({
                "area": "AC feasibility",
                "severity": "yellow",
                "finding": f"{ac_id} checks definition but {detected_type} has none",
                "suggestion": "Use existence check instead of definition",
            })

    if not findings:
        findings.append({
            "area": "AC feasibility",
            "severity": "green",
            "finding": "All AC verify methods match registry capabilities",
            "suggestion": "",
        })

    return findings

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

    # Normalize: filter to dicts only (strings are not usable as ACs)
    if acs and not isinstance(acs[0], dict):
        acs = [a for a in acs if isinstance(a, dict)]

    # Normalize key variants (scaffolder uses item_name/item_type/wave_number)
    # Items may be dicts or strings — only normalize dicts
    normalized_items: list[dict] = []
    for idx, item in enumerate(items):
        if isinstance(item, str):
            normalized_items.append({"name": item, "id": idx + 1})
            continue
        if not isinstance(item, dict):
            continue
        if "item_name" in item and "name" not in item:
            item["name"] = item["item_name"]
        if "item_type" in item and "type" not in item:
            item["type"] = item["item_type"]
        if "id" not in item:
            item["id"] = idx + 1
        normalized_items.append(item)
    items = normalized_items

    normalized_waves: list[dict] = []
    for wave in waves:
        if isinstance(wave, str):
            continue
        if not isinstance(wave, dict):
            continue
        if "wave_number" in wave and "id" not in wave:
            wave["id"] = wave["wave_number"]
        normalized_waves.append(wave)
    waves = normalized_waves

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

    # 2. Deployment feasibility (enhanced — replaces old CLI-only check)
    deploy_entries: list[dict] = []
    if items:
        deploy_findings, deploy_entries = _check_deploy_feasibility(items)
        all_findings.extend(deploy_findings)

    # Legacy cli_verification for backwards compatibility
    cli_entries: list[dict] = [
        {"item_type": e["type"], "fab_type": e["type"],
         "supported": e["deploy_method"] != "portal",
         "fallback": "portal" if e["deploy_method"] == "portal" else ""}
        for e in deploy_entries if e["deploy_method"] == "portal"
    ]

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

    # 7. Phase ordering validation (registry-driven)
    if items and waves:
        all_findings.extend(_check_phase_ordering(items, waves))

    # 8. Naming safety (Fabric hyphen restrictions)
    if items:
        all_findings.extend(_check_naming_safety(items))

    # 9. AC test method feasibility (registry-driven)
    if items and acs:
        all_findings.extend(_check_ac_test_methods(items, acs))

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
        "item_deployment_matrix": sorted(deploy_entries, key=lambda e: e.get("phase_order", 99)),
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
