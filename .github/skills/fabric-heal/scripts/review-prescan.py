#!/usr/bin/env python3
"""Deterministic pre-scan for architecture handoff review."""
from __future__ import annotations
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "_shared" / "lib"))
from registry_loader import build_deploy_method_map, build_phase_map, build_test_method_map
from yaml_utils import extract_and_parse_yaml_blocks, extract_frontmatter, find_block
DEPLOY_METHODS: dict[str, dict] = build_deploy_method_map()
TEST_METHODS: dict[str, dict] = build_test_method_map()
PHASE_MAP: dict[str, tuple[str, int]] = build_phase_map()
KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
def _extract_frontmatter(content: str) -> dict[str, Any]:
    return extract_frontmatter(content)
def _extract_yaml_blocks(content: str) -> list[dict[str, Any]]:
    return extract_and_parse_yaml_blocks(content)
def _find_block(blocks: list[dict[str, Any]], key: str) -> Any:
    block = find_block(blocks, key)
    return block[key] if block is not None else None
def _finding(area: str, severity: str, finding: str, suggestion: str = "") -> dict[str, str]:
    return {
        "area": area,
        "severity": severity,
        "finding": finding,
        "suggestion": suggestion,
    }
def _green(area: str, finding: str) -> dict[str, str]:
    return _finding(area, "green", finding)
def _truncate(text: str, max_words: int = 15) -> str:
    words = text.split()
    return text if len(words) <= max_words else " ".join(words[:max_words])
def _deps(item: dict[str, Any]) -> list[str]:
    return [str(dep) for dep in (item.get("dependencies", item.get("depends_on", [])) or [])]
def _registry_entry(mapping: dict[str, Any], key: str) -> Any:
    return mapping.get(key) or mapping.get(str(key).title())
def _header_value(content: str, label: str) -> str | None:
    match = re.search(rf"\*\*{re.escape(label)}:\*\*\s*(.+)", content)
    return match.group(1).strip() if match else None
def _block_value(blocks: list[dict[str, Any]], *keys: str) -> Any:
    for key in keys:
        value = _find_block(blocks, key)
        if value:
            return value
    return []
def _normalize_items(items: list[Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for idx, item in enumerate(items):
        if isinstance(item, str):
            normalized.append({"name": item, "id": idx + 1})
            continue
        if not isinstance(item, dict):
            continue
        current = dict(item)
        if "item_name" in current and "name" not in current:
            current["name"] = current["item_name"]
        if "item_type" in current and "type" not in current:
            current["type"] = current["item_type"]
        current.setdefault("id", idx + 1)
        normalized.append(current)
    return normalized
def _normalize_waves(waves: list[Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for wave in waves:
        if not isinstance(wave, dict):
            continue
        current = dict(wave)
        if "wave_number" in current and "id" not in current:
            current["id"] = current["wave_number"]
        normalized.append(current)
    return normalized
def _parse_handoff(content: str) -> dict[str, Any]:
    frontmatter = _extract_frontmatter(content)
    blocks = _extract_yaml_blocks(content)
    project = frontmatter.get("project", "unknown")
    task_flow = frontmatter.get("task_flow", "unknown")
    if project == "unknown":
        project = _header_value(content, "Project") or project
    if task_flow == "unknown":
        task_flow = _header_value(content, "Task Flow") or task_flow
    items = _normalize_items(_block_value(blocks, "items", "items_to_deploy"))
    waves = _normalize_waves(_block_value(blocks, "waves", "deployment_waves"))
    acs = _find_block(blocks, "acceptance_criteria") or []
    if acs and not isinstance(acs[0], dict):
        acs = [ac for ac in acs if isinstance(ac, dict)]
    warnings: list[str] = []
    if not items:
        warnings.append("No items_to_deploy block found")
    if not waves:
        warnings.append("No deployment_waves block found")
    if not acs:
        warnings.append("No acceptance_criteria block found")
    return {
        "project": project,
        "task_flow": task_flow,
        "items": items,
        "waves": waves,
        "acs": acs,
        "warnings": warnings,
    }
def _wave_lookup(waves: list[dict[str, Any]]) -> dict[str, int]:
    item_wave: dict[str, int] = {}
    for wave in waves:
        wave_id = int(wave.get("id", 0))
        for item in wave.get("items", []):
            item_wave[str(item)] = wave_id
    return item_wave
def _has_cycle(graph: dict[str, list[str]]) -> bool:
    white, gray, black = 0, 1, 2
    color = {node: white for node in graph}
    def dfs(node: str) -> bool:
        color[node] = gray
        for neighbor in graph.get(node, []):
            if neighbor not in color:
                continue
            if color[neighbor] == gray:
                return True
            if color[neighbor] == white and dfs(neighbor):
                return True
        color[node] = black
        return False
    return any(dfs(node) for node, shade in list(color.items()) if shade == white)
def _check_wave_dependencies(items: list[dict], waves: list[dict]) -> list[dict]:
    findings: list[dict] = []
    item_wave = _wave_lookup(waves)
    graph_nodes = {item.get("name", str(item.get("id", ""))) for item in items}
    errors: list[str] = []
    warnings: list[str] = []
    for item in items:
        name = item.get("name", str(item.get("id", "?")))
        my_wave = item_wave.get(name) or item_wave.get(str(item.get("id", "")))
        if my_wave is None:
            warnings.append(f"{name} not assigned to any wave")
            continue
        for dep in _deps(item):
            dep_wave = item_wave.get(dep) or item_wave.get(str(dep))
            if dep_wave is None:
                continue
            if dep_wave > my_wave:
                errors.append(f"{name} (wave {my_wave}) depends on {dep} (wave {dep_wave})")
            elif dep_wave == my_wave:
                warnings.append(f"{name} and dependency {dep} both in wave {my_wave}")
    graph = {
        item.get("name", str(item.get("id", ""))): [dep for dep in _deps(item) if dep in graph_nodes]
        for item in items
    }
    if _has_cycle(graph):
        errors.append("Circular dependency detected in items_to_deploy")
    if errors:
        findings.extend(
            _finding("Wave structure", "red", _truncate(err), "Fix dependency order before deployment")
            for err in errors
        )
    elif warnings:
        findings.extend(
            _finding("Wave structure", "yellow", _truncate(warn), "Consider separating into different waves")
            for warn in warnings
        )
    else:
        findings.append(_green("Wave structure", "All dependencies satisfied in correct wave order"))
    return findings
def _check_ac_coverage(items: list[dict], acs: list[dict]) -> list[dict]:
    ac_text = " ".join(" ".join(str(v) for v in ac.values()) for ac in acs).lower()
    findings = [
        _finding("AC coverage", "yellow", f"{item.get('name', '')} has no acceptance criteria", f"Add AC for {item.get('name', '')} existence check")
        for item in items
        if item.get("name") and item["name"].lower() not in ac_text
    ]
    return findings or [_green("AC coverage", "All items referenced in acceptance criteria")]
def _check_item_names(items: list[dict]) -> list[dict]:
    findings: list[dict] = []
    seen: dict[str, int] = {}
    for item in items:
        name = item.get("name", "")
        if not name:
            continue
        lowered = name.lower()
        if lowered in seen:
            findings.append(_finding("Item naming", "red", f"Duplicate item name: {name}", "Use unique names for all items"))
        seen[lowered] = seen.get(lowered, 0) + 1
        if not KEBAB_RE.match(name):
            findings.append(_finding("Item naming", "yellow", f"{name} is not kebab-case", "Rename to kebab-case convention"))
    return findings or [_green("Item naming", "All item names valid and unique")]
def _check_wave_count(items: list[dict], waves: list[dict]) -> tuple[list[dict], dict]:
    item_deps = {str(item.get("name", item.get("id", ""))): _deps(item) for item in items}
    merge_opportunities: list[dict] = []
    sorted_waves = sorted(waves, key=lambda wave: int(wave.get("id", 0)))
    for idx, wave in enumerate(sorted_waves):
        wave_id = int(wave.get("id", 0))
        wave_items = [str(item) for item in wave.get("items", [])]
        if len(wave_items) != 1:
            continue
        solo_item = wave_items[0]
        if idx > 0:
            prev_wave = sorted_waves[idx - 1]
            prev_wave_id = int(prev_wave.get("id", 0))
            prev_items = [str(item) for item in prev_wave.get("items", [])]
            if not any(dep in prev_items for dep in item_deps.get(solo_item, [])):
                merge_opportunities.append({
                    "description": f"Merge wave {wave_id} into wave {prev_wave_id}",
                    "reason": f"Single item, no dependency on wave {prev_wave_id} items",
                })
        if idx < len(sorted_waves) - 1 and not merge_opportunities:
            next_wave = sorted_waves[idx + 1]
            next_wave_id = int(next_wave.get("id", 0))
            next_items = [str(item) for item in next_wave.get("items", [])]
            if not any(solo_item in item_deps.get(next_item, []) for next_item in next_items):
                merge_opportunities.append({
                    "description": f"Merge wave {wave_id} into wave {next_wave_id}",
                    "reason": f"Single item, no blockers for wave {next_wave_id}",
                })
    total_waves = len(waves)
    wave_opt = {
        "current_waves": total_waves,
        "proposed_waves": max(total_waves - len(merge_opportunities), 1),
        "changes": merge_opportunities,
    }
    if merge_opportunities:
        return [
            _finding(
                "Wave optimization",
                "yellow",
                f"{len(merge_opportunities)} wave merge opportunity(s) found",
                "Review merge suggestions in wave_optimization",
            )
        ], wave_opt
    return [_green("Wave optimization", f"{total_waves} waves look optimal")], wave_opt
def _check_diagram(content: str, items: list[dict]) -> list[dict]:
    section = re.split(r"##\s+Architecture Diagram", content, maxsplit=1)
    if len(section) < 2:
        return [_finding("Diagram", "yellow", "No Architecture Diagram section found", "Add ## Architecture Diagram with ASCII data flow")]
    match = re.search(r"```\s*\n(.*?)```", section[1], re.DOTALL)
    if not match:
        return [_finding("Diagram", "yellow", "No code block found in Architecture Diagram section", "Wrap diagram in ``` code fences")]
    diagram = match.group(1)
    stripped = diagram.strip()
    if not stripped or "Replace this block" in stripped:
        return [_finding("Diagram", "yellow", "Architecture diagram is empty or placeholder", "Draw project-specific data flow diagram")]
    lines = diagram.split("\n")
    top_left = sum(line.count("┌") for line in lines)
    bot_right = sum(line.count("┘") for line in lines)
    top_right = sum(line.count("┐") for line in lines)
    bot_left = sum(line.count("└") for line in lines)
    findings = [
        _finding(
            "Diagram",
            "yellow",
            f"Unbalanced box corners: ┌={top_left} ┘={bot_right} ┐={top_right} └={bot_left}",
            "Fix box-drawing characters to close all boxes",
        )
        if top_left != bot_right or top_right != bot_left
        else _green("Diagram", f"Diagram box characters balanced ({top_left} boxes)")
    ]
    missing = [item.get("name", "") for item in items if item.get("name") and item["name"].lower() not in diagram.lower()]
    if missing:
        findings.append(
            _finding(
                "Diagram",
                "yellow",
                f"{len(missing)} item(s) missing from diagram: {', '.join(missing[:5])}",
                "Ensure all items appear in the architecture diagram",
            )
        )
    return findings
def _check_phase_ordering(items: list[dict], waves: list[dict]) -> list[dict]:
    item_wave = _wave_lookup(waves)
    violations: list[str] = []
    for item in items:
        name = item.get("name", "")
        item_type = item.get("type", "")
        my_wave = item_wave.get(name)
        phase_info = _registry_entry(PHASE_MAP, item_type)
        if not name or not item_type or my_wave is None or not phase_info:
            continue
        phase_name, phase_order = phase_info
        for other in items:
            other_name = other.get("name", "")
            other_type = other.get("type", "")
            other_wave = item_wave.get(other_name)
            other_phase = _registry_entry(PHASE_MAP, other_type)
            if other_name == name or not other_type or other_wave is None or not other_phase:
                continue
            if other_phase[1] > phase_order and other_wave < my_wave:
                violations.append(
                    f"{other_name} ({other_phase[0]}) in wave {other_wave} "
                    f"before {name} ({phase_name}) in wave {my_wave}"
                )
    return [
        _finding("Phase ordering", "yellow", _truncate(violation), "Align waves with registry deployment phases")
        for violation in list(dict.fromkeys(violations))[:3]
    ] or [_green("Phase ordering", "Wave assignments align with deployment phases")]
def _check_deploy_feasibility(items: list[dict]) -> tuple[list[dict], list[dict]]:
    findings: list[dict] = []
    deploy_entries: list[dict] = []
    for item in items:
        item_type = item.get("type", "")
        item_name = item.get("name", item_type)
        if not item_type:
            continue
        dm = _registry_entry(DEPLOY_METHODS, item_type)
        tm = _registry_entry(TEST_METHODS, item_type) or {}
        if not dm:
            findings.append(_finding("Deploy feasibility", "yellow", f"{item_type} not found in item registry", "Verify item type name matches registry"))
            continue
        deploy_entries.append({
            "item": item_name,
            "type": item_type,
            "deploy_method": dm["method"],
            "strategy": dm.get("strategy"),
            "verified": dm.get("verified", False),
            "availability": dm.get("availability", "ga"),
            "test_method": tm.get("verify_method", "").replace("{item}", item_name),
            "has_definition": dm.get("has_definition", False),
            "phase": tm.get("phase", "Other"),
            "phase_order": tm.get("phase_order", 99),
        })
        if dm["method"] == "portal":
            findings.append(_finding("Deploy feasibility", "yellow", f"{item_type} is portal-only (no REST API)", "Document as manual step in deployment"))
        elif dm.get("strategy") == "unsupported":
            findings.append(_finding("Deploy feasibility", "yellow", f"{item_type} not supported by fabric-cicd", "Use REST API or portal for this item"))
        if dm.get("availability") == "pupr":
            findings.append(_finding("Deploy feasibility", "yellow", f"{item_type} is a public preview feature", "Note preview limitations in deployment plan"))
        if dm.get("creatable") and not dm.get("has_definition"):
            findings.append(_finding("Deploy feasibility", "green", f"{item_type} needs portal config post-creation", "Plan manual configuration after REST API create"))
    return findings or [_green("Deploy feasibility", "All items fully deployable via REST API or fabric-cicd")], deploy_entries
def _check_naming_safety(items: list[dict]) -> list[dict]:
    findings = [
        _finding("Naming safety", "yellow", f"{item['name']} contains hyphens (Fabric may reject)", f"Rename to {item['name'].replace('-', '_')}")
        for item in items
        if item.get("name") and "-" in item["name"]
    ]
    return findings or [_green("Naming safety", "All item names are Fabric-safe (no hyphens)")]
def _check_ac_test_methods(items: list[dict], acs: list[dict]) -> list[dict]:
    findings: list[dict] = []
    for ac in acs:
        verify_text = str(ac.get("verify", "")).lower()
        target = ac.get("target", "")
        ac_id = ac.get("id", "?")
        if not verify_text:
            continue
        detected_type = None
        for item in items:
            item_name = item.get("name", "")
            if item_name and item_name.lower() in verify_text:
                detected_type = item.get("type", "")
                break
            if target and target.lower() == item_name.lower():
                detected_type = item.get("type", "")
                break
        dm = _registry_entry(DEPLOY_METHODS, detected_type) if detected_type else None
        if not dm:
            continue
        if ("rest api" in verify_text or "get /" in verify_text) and not dm.get("creatable", False):
            findings.append(_finding("AC feasibility", "red", f"{ac_id} uses REST API but {detected_type} is portal-only", "Change verify method to portal check"))
        if ("definition" in verify_text or "config" in verify_text) and not dm.get("has_definition", False):
            findings.append(_finding("AC feasibility", "yellow", f"{ac_id} checks definition but {detected_type} has none", "Use existence check instead of definition"))
    return findings or [_green("AC feasibility", "All AC verify methods match registry capabilities")]
def prescan(handoff_path: str) -> dict:
    with open(handoff_path, "r", encoding="utf-8") as handle:
        content = handle.read()
    parsed = _parse_handoff(content)
    items = parsed["items"]
    waves = parsed["waves"]
    acs = parsed["acs"]
    warnings = parsed["warnings"]
    findings: list[dict] = []
    if items and waves:
        findings.extend(_check_wave_dependencies(items, waves))
    else:
        findings.append(_finding("Wave structure", "yellow", "Cannot validate — missing items or waves block", "Ensure handoff has items and waves YAML blocks"))
    deploy_entries: list[dict] = []
    if items:
        deploy_findings, deploy_entries = _check_deploy_feasibility(items)
        findings.extend(deploy_findings)
    cli_entries = [
        {
            "item_type": entry["type"],
            "fab_type": entry["type"],
            "supported": entry["deploy_method"] != "portal",
            "fallback": "portal" if entry["deploy_method"] == "portal" else "",
        }
        for entry in deploy_entries
        if entry["deploy_method"] == "portal"
    ]
    if items and acs:
        findings.extend(_check_ac_coverage(items, acs))
    elif items:
        findings.append(_finding("AC coverage", "yellow", "No acceptance_criteria block — cannot verify coverage", "Add acceptance_criteria YAML block to handoff"))
    if items:
        findings.extend(_check_item_names(items))
    wave_opt: dict[str, Any] = {"current_waves": 0, "proposed_waves": 0, "changes": []}
    if items and waves:
        wave_findings, wave_opt = _check_wave_count(items, waves)
        findings.extend(wave_findings)
    findings.extend(_check_diagram(content, items))
    if items and waves:
        findings.extend(_check_phase_ordering(items, waves))
    if items:
        findings.extend(_check_naming_safety(items))
    if items and acs:
        findings.extend(_check_ac_test_methods(items, acs))
    for idx, finding in enumerate(findings, start=1):
        finding["id"] = f"F-{idx}"
    must_fix = [finding["id"] for finding in findings if finding["severity"] == "red"]
    should_fix = [finding["id"] for finding in findings if finding["severity"] == "yellow"]
    no_change = [finding["id"] for finding in findings if finding["severity"] == "green"]
    for warning in warnings:
        fid = f"F-{len(findings) + 1}"
        warning_finding = _finding("Parse warning", "yellow", warning, "Check handoff file structure")
        warning_finding["id"] = fid
        findings.append(warning_finding)
        should_fix.append(fid)
    return {
        "project": parsed["project"],
        "task_flow": parsed["task_flow"],
        "review_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "architecture_version": "draft",
        "scan_type": "automated",
        "findings": findings,
        "wave_optimization": wave_opt,
        "cli_verification": cli_entries,
        "item_deployment_matrix": sorted(deploy_entries, key=lambda entry: entry.get("phase_order", 99)),
        "prerequisites": [],
        "assessment": "needs-changes" if must_fix else "ready",
        "must_fix": must_fix,
        "should_fix": should_fix,
        "no_change": no_change,
    }
def _yaml_str(value: str) -> str:
    if not value:
        return '""'
    if any(char in value for char in (":", "#", "'", '"', "\n", "[", "]", "{", "}")):
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'
    return f'"{value}"'
def _to_yaml(data: dict) -> str:
    lines = [
        f"project: {_yaml_str(data['project'])}",
        f"task_flow: {_yaml_str(data['task_flow'])}",
        f"review_date: {_yaml_str(data['review_date'])}",
        f"architecture_version: {data['architecture_version']}",
        f"scan_type: {data['scan_type']}",
        "",
        "findings:",
    ]
    for finding in data["findings"]:
        lines.extend([
            f"  - id: {finding['id']}",
            f"    area: {_yaml_str(finding['area'])}",
            f"    severity: {finding['severity']}",
            f"    finding: {_yaml_str(finding['finding'])}",
            f"    suggestion: {_yaml_str(finding.get('suggestion', ''))}",
        ])
    wave_opt = data["wave_optimization"]
    lines.extend([
        "",
        "wave_optimization:",
        f"  current_waves: {wave_opt['current_waves']}",
        f"  proposed_waves: {wave_opt['proposed_waves']}",
    ])
    if wave_opt["changes"]:
        lines.append("  changes:")
        for change in wave_opt["changes"]:
            lines.extend([
                f"    - description: {_yaml_str(change['description'])}",
                f"      reason: {_yaml_str(change['reason'])}",
            ])
    else:
        lines.append("  changes: []")
    lines.extend(["", "cli_verification:"])
    if data["cli_verification"]:
        for entry in data["cli_verification"]:
            lines.extend([
                f"  - item_type: {_yaml_str(entry['item_type'])}",
                f"    fab_type: {entry['fab_type']}",
                f"    supported: {'true' if entry['supported'] else 'false'}",
                f"    fallback: {entry.get('fallback', '')}",
            ])
    else:
        lines.append("  []")
    lines.extend([
        "",
        "prerequisites: []",
        "",
        f"assessment: {data['assessment']}",
        f"must_fix: {json.dumps(data['must_fix'])}",
        f"should_fix: {json.dumps(data['should_fix'])}",
        f"no_change: {json.dumps(data['no_change'])}",
    ])
    return "\n".join(lines) + "\n"
def _to_json(data: dict) -> str:
    return json.dumps(data, indent=2) + "\n"
def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministic pre-scan of architecture handoff for review")
    parser.add_argument("--handoff", required=True, help="Path to architecture-handoff.md")
    parser.add_argument("--output", default=None, help="Output file path (default: stdout)")
    parser.add_argument("--format", choices=["yaml", "json"], default="json", help="Output format (default: json)")
    args = parser.parse_args()
    text = _to_yaml(prescan(args.handoff)) if args.format == "yaml" else _to_json(prescan(args.handoff))
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text)
    else:
        sys.stdout.write(text)
if __name__ == "__main__":
    main()
