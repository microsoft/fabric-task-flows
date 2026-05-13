#!/usr/bin/env python3
"""Pipeline runner CLI and compatibility re-exports."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from banner import print_banner
from new_project import sanitize_name, scaffold
from paths import REPO_ROOT
from pipeline_precompute import (
    _extract_task_flow,
    _extract_top_task_flow,
    _fast_forward_to_signoff,
    _generate_architecture_summary,
    _generate_complete_handoff,
    _generate_deploy_artifacts,
    _generate_deployment_handoff,
    _generate_project_brief,
    _generate_test_plan,
    _generate_validation_report,
    _run_precompute,
)
from pipeline_prompts import (
    _extract_decisions_from_handoff,
    _extract_diagram,
    _project_path,
    _prompt_for_phase,
    get_next_prompt,
)
from pipeline_state import (
    MIN_CONTENT_SIZE,
    _PLACEHOLDER_NAMES,
    _get_registry,
    _is_auto,
    _load_skills_registry,
    _load_state,
    _next_phase,
    _phase_is_gate,
    _phase_mode,
    _phase_order,
    _phase_output_files,
    _phase_skill,
    _save_state,
    _state_path,
    _verify_output,
    advance,
    get_status,
    reconcile,
    reset_phase,
    start_pipeline,
)
from registry_loader import build_layer_map, build_type_to_decision_map

SKILLS_DIR = REPO_ROOT / ".github" / "skills"
VERSION = "1.0.0"
_REGISTRY = None


def _term_width() -> int:
    return shutil.get_terminal_size(fallback=(100, 24)).columns


def _separator(label: str = "") -> str:
    width = _term_width()
    if label:
        return f"\n{'─' * width}\n  {label}\n{'─' * width}\n"
    return f"{'─' * width}"


def _print_status(state: dict) -> None:
    project = state["project"]
    task_flow = state.get("task_flow", "TBD") or "TBD"

    project_dir = REPO_ROOT / "_projects" / project
    handoff = project_dir / "docs" / "architecture-handoff.md"
    item_count = 0
    wave_count = 0
    if handoff.exists():
        import re as _re

        content = handoff.read_text(encoding="utf-8", errors="ignore")
        item_count = len(_re.findall(r"^\|\s*\d", content, _re.MULTILINE))
        waves = _re.findall(r"wave[_\s]*(\d+)", content, _re.IGNORECASE)
        if waves:
            wave_count = max(int(wave) for wave in waves)

    deploy_dir = project_dir / "deploy"
    deploy_scripts = list(deploy_dir.glob("deploy-*.py")) if deploy_dir.exists() else []

    width = 58
    print()
    print(f"  {'=' * width}")
    print(f"  {project}  ·  {task_flow}")
    print(f"  {'=' * width}")

    labels = {
        "0a-discovery": "Discover",
        "1-design": "Design",
        "2a-test-plan": "Test Plan",
        "2b-sign-off": "Sign-Off",
        "2c-deploy": "Deploy",
        "3-validate": "Validate",
        "4-document": "Document",
    }
    status_icons = {"complete": "[done]", "in_progress": "[....]", "pending": "[    ]"}

    for phase_id in _phase_order():
        phase = state["phases"][phase_id]
        status = phase["status"]
        agent = _phase_skill(phase_id) or "you"
        output = phase.get("output", "")

        suffix = ""
        if status == "complete" and output:
            out_path = project_dir / output
            if out_path.exists() and out_path.stat().st_size > 50:
                suffix = f" -> {output}"
        elif status == "in_progress":
            suffix = f" ({agent})"

        gate = " (human gate)" if _phase_is_gate(phase_id) else ""
        line = f"  {status_icons.get(status, '[  ? ]')} {labels.get(phase_id, phase_id):<12}{suffix}{gate}"
        print(line)

    print(f"  {'=' * width}")

    parts = []
    if item_count:
        parts.append(f"Items: {item_count}")
    if wave_count:
        parts.append(f"Waves: {wave_count}")
    if deploy_scripts:
        parts.append(f"Deploy: {deploy_scripts[0].name}")
    if parts:
        print(f"  {' | '.join(parts)}")
        print(f"  {'=' * width}")
    print()


def _print_phase_output(project: str, completed_phase: str) -> None:
    expected = _phase_output_files(completed_phase)
    if not expected:
        return

    project_dir = REPO_ROOT / "_projects" / project
    for rel_path in expected:
        full_path = project_dir / rel_path
        if not full_path.exists():
            continue
        content = full_path.read_text(encoding="utf-8", errors="ignore")
        if full_path.stat().st_size < MIN_CONTENT_SIZE:
            continue
        label = rel_path.upper().replace("/", " › ")
        print(_separator(label))
        print(content.rstrip())
        print()


_LAYER_LABELS: dict[str, tuple[str, str]] = build_layer_map()
_CONFIDENCE_RANK: dict[str, int] = {"high": 3, "medium": 2, "low": 1}


def _print_discovery_summary(project: str) -> None:
    docs_dir = REPO_ROOT / "_projects" / project / "docs"
    signal_cache_path = docs_dir / ".signal-mapper-cache.json"
    intake_path = docs_dir / ".discovery-intake.json"

    state: dict = {}
    try:
        state = _load_state(project)
    except FileNotFoundError:
        pass

    signal_cache: dict = {}
    if signal_cache_path.exists():
        try:
            signal_cache = json.loads(signal_cache_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    intake: dict = {}
    if intake_path.exists():
        try:
            intake = json.loads(intake_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    display_name = state.get("display_name", project)
    problem = (state.get("problem_statement") or "").strip()

    print(_separator(f"DISCOVERY REVIEW — {display_name}"))
    print(f"  Problem: {problem if problem else '— not captured —'}")
    print()

    print(_separator("4 V's ASSESSMENT"))
    for key, label in [
        ("volume", "📦 Volume     "),
        ("velocity", "⏱️  Velocity   "),
        ("variety", "🔀 Variety    "),
        ("versatility", "🛠️  Versatility"),
    ]:
        entry = intake.get(key) if isinstance(intake.get(key), dict) else None
        if entry and entry.get("value"):
            print(f"  {label}  {entry['value']}  ({entry.get('source', 'inferred')})")
        else:
            print(f"  {label}  — not yet captured —  (unknown)")
    print()

    signals = list(signal_cache.get("signals", []) or [])
    print(_separator("INFERRED SIGNALS"))
    if signals:
        signals_sorted = sorted(
            signals,
            key=lambda signal: _CONFIDENCE_RANK.get(signal.get("confidence", "low"), 0),
            reverse=True,
        )[:5]
        for signal in signals_sorted:
            keywords = signal.get("source_keywords") or []
            kw_str = ", ".join(keywords[:3]) if keywords else "(inferred)"
            print(
                f"  • {signal.get('signal', 'unknown')} — {signal.get('value', '')}  "
                f"(confidence: {signal.get('confidence', 'low')}, keywords: {kw_str})"
            )
    else:
        print("  — signal mapper cache not available —")
    print()

    candidates = list(signal_cache.get("task_flow_candidates", []) or [])
    print(_separator("CANDIDATE TASK FLOWS"))
    if candidates:
        for idx, candidate in enumerate(candidates[:3], 1):
            tf_id = candidate.get("id") or candidate.get("name") or candidate.get("task_flow") or "unknown"
            score = candidate.get("score", 0)
            signals_str = ", ".join(candidate.get("signals", []) or []) or "—"
            print(f"  {idx}. {tf_id}   score {score}   signals: {signals_str}")
    else:
        print("  — no candidates yet (signal mapper may not have run) —")
    print()


def _print_signoff_summary(project: str) -> None:
    handoff_path = REPO_ROOT / "_projects" / project / "docs" / "architecture-handoff.md"
    summary_path = REPO_ROOT / "_projects" / project / "docs" / ".architecture-cache.json"

    summary: dict = {}
    if summary_path.exists():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    decisions_path = REPO_ROOT / "_projects" / project / "docs" / "decisions.json"
    decisions_data: dict = {}
    if decisions_path.exists():
        try:
            raw = json.loads(decisions_path.read_text(encoding="utf-8"))
            decisions_data = raw.get("decisions", raw)
        except (json.JSONDecodeError, OSError):
            pass
    if not decisions_data and handoff_path.exists():
        try:
            decisions_data = _extract_decisions_from_handoff(handoff_path.read_text(encoding="utf-8"))
        except OSError:
            pass

    state: dict = {}
    try:
        state = _load_state(project)
    except FileNotFoundError:
        pass

    display_name = state.get("display_name", project)
    task_flow = summary.get("task_flow") or state.get("task_flow") or "TBD"
    items = summary.get("items", [])
    decisions = decisions_data or summary.get("decisions", {})
    item_count = summary.get("item_count", len(items))
    wave_count = summary.get("wave_count", 0)

    print(_separator(f"ARCHITECTURE REVIEW — {display_name}"))
    print(f"  Pattern: {task_flow}")
    print(f"  Scope:   {item_count} Fabric items in {wave_count} deployment waves")
    print()

    diagram = _extract_diagram(handoff_path)
    if diagram and diagram.strip():
        print(diagram)
        print()

    if items:
        print(_separator("WHAT WE'RE BUILDING"))
        seen_layers: dict[str, list[dict]] = {}
        for item in items:
            layer_label, _ = _LAYER_LABELS.get(item.get("type", ""), ("Other", "📦"))
            seen_layers.setdefault(layer_label, []).append(item)

        for layer_label, layer_items in seen_layers.items():
            emoji = _LAYER_LABELS.get(layer_items[0].get("type", ""), ("", "📦"))[1]
            names = []
            for item in layer_items:
                name = item.get("name", "unknown")
                purpose = item.get("purpose", "")
                names.append(f"{name} — {purpose}" if purpose else f"{name} ({item.get('type', '')})")
            if len(names) == 1:
                print(f"  {emoji} {layer_label:<10} {names[0]}")
            else:
                print(f"  {emoji} {layer_label}")
                for name in names:
                    print(f"     {'':10} {name}")
        print()

    user_facing_decisions = {
        "storage": "Storage",
        "ingestion": "Ingestion",
        "processing": "Processing",
        "visualization": "Visualization",
    }
    rationale_lines = []
    for dec_key, label in user_facing_decisions.items():
        decision = decisions.get(dec_key, {})
        choice = decision.get("choice")
        rationale = decision.get("rationale", "")
        if choice and choice not in ("N/A", "Not yet determined"):
            rationale_lines.append(f"  • {label}: {choice} — {rationale}")
    if rationale_lines:
        print(_separator("WHY THIS ARCHITECTURE"))
        for line in rationale_lines:
            print(line)
        print()

    tradeoff_resolved: set[str] = set()
    handoff_text = ""
    if handoff_path.exists():
        try:
            handoff_text = handoff_path.read_text(encoding="utf-8")
        except OSError:
            pass
    type_to_decision = build_type_to_decision_map()
    for line in handoff_text.splitlines():
        lower = line.lower()
        if any(phrase in lower for phrase in (
            "chosen over", "selected over", "picked over", "decided on",
            "rejected because", "rejected —", "rejected -", "decision:", "choice:",
        )):
            for type_name, dec_cat in type_to_decision.items():
                if type_name in lower:
                    tradeoff_resolved.add(dec_cat)

    warnings = []
    for dec_key, label in user_facing_decisions.items():
        choice = decisions.get(dec_key, {}).get("choice")
        if (not choice or choice == "Not yet determined") and dec_key not in tradeoff_resolved:
            warnings.append(f"  ⚠️  {label} decision is unresolved — needs input before deployment")
    if warnings:
        print(_separator("NEEDS ATTENTION"))
        for warning in warnings:
            print(warning)
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline runner — orchestrate Fabric agent phases")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    start_p = sub.add_parser("start", help="Start a new pipeline")
    start_p.add_argument("name", help="Project display name")
    start_p.add_argument("--problem", help="Problem statement text")

    next_p = sub.add_parser("next", help="Get prompt for next phase")
    next_p.add_argument("--project", required=True, help="Project folder name (kebab-case)")

    status_p = sub.add_parser("status", help="Show pipeline status")
    status_p.add_argument("--project", required=True, help="Project folder name")

    adv_p = sub.add_parser("advance", help="Mark current phase complete")
    adv_p.add_argument("--project", required=True, help="Project folder name")
    adv_p.add_argument("--approve", action="store_true",
                       help="Explicitly approve a human gate (required for sign-off phases)")
    adv_p.add_argument("--revise", action="store_true",
                       help="Request revisions at sign-off (resets to architect for feedback incorporation, max 3 cycles)")
    adv_p.add_argument("--feedback", type=str, default=None,
                       help="Feedback text for --revise (saved to docs/sign-off-feedback.md)")
    adv_p.add_argument("--reconcile", action="store_true",
                       help="Run reconcile before advancing to heal any state drift")
    adv_p.add_argument("--deploy-mode", choices=["live", "artifacts_only"], default=None,
                       help="Deployment mode to record when approving sign-off "
                            "(default: artifacts_only if state has no deploy_mode set)")
    adv_p.add_argument("-q", "--quiet", action="store_true",
                       help="Suppress printing completed phase output files and diagrams (use for agent/CI mode)")

    reset_p = sub.add_parser("reset", help="Reset a phase")
    reset_p.add_argument("--project", required=True, help="Project folder name")
    reset_p.add_argument("--phase", required=True, choices=_phase_order(), help="Phase to reset to")

    recon_p = sub.add_parser("reconcile", help="Rebuild state from file evidence (heals drift)")
    recon_p.add_argument("--project", required=True, help="Project folder name")

    batch_p = sub.add_parser("batch", help="Start pipeline and fast-forward to sign-off (single command)")
    batch_p.add_argument("name", help="Project display name")
    batch_p.add_argument("--problem", required=True, help="Problem statement text")
    batch_p.add_argument("--through", default="2b-sign-off",
                         help="Phase to fast-forward through (default: 2b-sign-off)")

    disc_p = sub.add_parser(
        "discovery-summary",
        help="Render a deterministic 4V's + signals recap for user confirmation",
    )
    disc_p.add_argument("--project", required=True, help="Project folder name")

    args = parser.parse_args()

    if args.command == "start":
        print_banner()
        state = start_pipeline(args.name, args.problem)
        _print_status(state)
        prompt, agent, phase, is_gate = get_next_prompt(state["project"])
        print(f"\n  Next agent: {agent}")
        print(f"  Phase: {phase}")
        if is_gate:
            print("  ⚠️  This phase is a human gate — review deliverables before advancing")
        print(f"\n{'─' * _term_width()}")
        print("  AGENT PROMPT (copy to Copilot CLI):")
        print(f"{'─' * _term_width()}\n")
        print(prompt)

    elif args.command == "next":
        prompt, agent, phase, is_gate = get_next_prompt(args.project)
        if agent is None and phase == "complete":
            print("✅ Pipeline complete.")
            return
        print(f"\n  Next agent: {agent or '(human gate)'}")
        print(f"  Phase: {phase}")
        print(f"  Auto-chain: {'🛑 No (human gate — use --approve)' if is_gate else '🟢 Yes'}")
        print(f"\n{'─' * _term_width()}")
        print("  AGENT PROMPT:")
        print(f"{'─' * _term_width()}\n")
        print(prompt)

    elif args.command == "status":
        state = _load_state(args.project)
        print_banner(
            project=state.get("display_name", args.project),
            task_flow=state.get("task_flow") or "TBD",
        )
        _print_status(state)

    elif args.command == "discovery-summary":
        _print_discovery_summary(args.project)

    elif args.command == "advance":
        if args.reconcile:
            _, recon_report = reconcile(args.project)
            print("\n  Reconcile report:")
            for line in recon_report:
                print(line)
            print()
        prev_state = _load_state(args.project)
        prev_phase = prev_state["current_phase"]

        if prev_phase == "2b-sign-off" and args.approve and getattr(args, "deploy_mode", None) is not None:
            prev_state["deploy_mode"] = args.deploy_mode
            _save_state(args.project, prev_state)

        state = advance(args.project, approved=args.approve, revise=args.revise, feedback=args.feedback)
        _print_status(state)

        if not args.quiet and state["current_phase"] != prev_phase:
            _print_phase_output(args.project, prev_phase)

        if state["current_phase"] == "2b-sign-off":
            _print_signoff_summary(args.project)
            print(_separator("PRESENTATION RULES"))
            print("  Show the user: diagram + 1-3 sentence summary + blockers.")
            print("  Do NOT show: decision tables, wave tables, trade-offs, or raw pipeline output.")
            print("  The user is a business stakeholder — speak in plain language.")
            print()
            prompt, agent, phase, is_gate = get_next_prompt(args.project)
            if prompt:
                print(_separator("AGENT PROMPT (copy to Copilot CLI):"))
                print(prompt)

        if state["current_phase"] == "2c-deploy":
            print(_separator("DEPLOYMENT ARTIFACTS GENERATED"))
            print(f"  📦 Deploy script:  deploy/deploy-{args.project}.py")
            print("  📦 Config:         deploy/config.yml")
            print("  📦 Workspace:      deploy/workspace/ (.platform files)")
            print()
            print(_separator("DEPLOYMENT MODE"))
            print('  Ask the user: "Would you like to deploy to a live Fabric workspace,')
            print('  or review the generated artifacts only?"')
            print()
            print("  • LIVE:           User runs deploy script → items created in Fabric")
            print("  • ARTIFACTS ONLY: Review generated files → no workspace needed")
            print()
            print("  Default: artifacts_only (set in pipeline-state.json)")
            print()

        prompt, agent, phase, is_gate = get_next_prompt(args.project)
        if agent:
            chain_label = "🛑 HUMAN GATE — use --approve" if is_gate else "🟢 AUTO-CHAIN"
            print(f"  {chain_label} → {agent or '(user)'} ({phase})")
            if not is_gate and prompt:
                print(f"\n{'─' * _term_width()}")
                print("  AGENT PROMPT (auto-chained):")
                print(f"{'─' * _term_width()}\n")
                print(prompt)

    elif args.command == "reconcile":
        state, recon_report = reconcile(args.project)
        print(f"\n  Reconcile report for '{args.project}':")
        for line in recon_report:
            print(line)
        print()
        _print_status(state)

    elif args.command == "reset":
        state = reset_phase(args.project, args.phase)
        _print_status(state)
        print(f"  Reset to {args.phase}. Run 'next' for the agent prompt.")

    elif args.command == "batch":
        import time as _time

        t0 = _time.monotonic()
        print_banner()
        print(f"⚡ BATCH MODE: {args.name} → {args.through}")
        print()

        state = start_pipeline(args.name, args.problem)
        project = state["project"]
        print(f"  ✅ Project scaffolded: {project}")

        prompt, agent, phase, is_gate = get_next_prompt(project)
        print("  ✅ Signal mapper executed")
        print("  📋 Discovery phase requires agent (signal interpretation + user confirmation)")
        print()

        elapsed = _time.monotonic() - t0
        print(f"  ⏱️  Scaffold + precompute completed in {elapsed:.1f}s")
        print()

        print(_separator("DISCOVERY AGENT PROMPT"))
        print(prompt)
        print()
        print(_separator(""))
        print("  After the agent writes the discovery brief, run:")
        print(f"    python _shared/scripts/run-pipeline.py advance --project {project} -q")
        print("  This will auto-generate ALL files and fast-forward to sign-off.")


if __name__ == "__main__":
    main()
