from __future__ import annotations

import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from new_project import sanitize_name, scaffold
from paths import REPO_ROOT as DEFAULT_REPO_ROOT

MIN_CONTENT_SIZE = 200

_PLACEHOLDER_NAMES: frozenset[str] = frozenset(
    {"tbd", "placeholder", "project", "test", "unnamed", "untitled", "new",
     "demo", "sample", "example", "temp", "tmp", "n/a", "none"}
)

_REGISTRY = None


def _runtime_module():
    return sys.modules.get("run_pipeline")



def _runtime_attr(name: str, default):
    module = _runtime_module()
    return getattr(module, name, default) if module is not None else default



def _repo_root() -> Path:
    return Path(_runtime_attr("REPO_ROOT", DEFAULT_REPO_ROOT))



def _runtime_callable(name: str, module_name: str):
    runtime_value = _runtime_attr(name, None)
    if callable(runtime_value):
        return runtime_value
    return getattr(importlib.import_module(module_name), name)



def _load_skills_registry() -> dict:
    registry_path = _repo_root() / "_shared" / "registry" / "skills-registry.json"
    with open(registry_path, encoding="utf-8") as handle:
        return json.load(handle)



def _get_registry() -> dict:
    global _REGISTRY
    module = _runtime_module()
    runtime_registry = _runtime_attr("_REGISTRY", None)
    if runtime_registry is not None:
        _REGISTRY = runtime_registry
        return runtime_registry
    if module is not None and getattr(module, "_REGISTRY", None) is None:
        _REGISTRY = None
    if _REGISTRY is None:
        _REGISTRY = _load_skills_registry()
        if module is not None:
            setattr(module, "_REGISTRY", _REGISTRY)
    return _REGISTRY



def _phase_order() -> list[str]:
    return _get_registry()["phase_order"]



def _phase_skill(phase: str) -> str | None:
    return _get_registry()["phases"].get(phase, {}).get("skill")



def _phase_mode(phase: str) -> int | None:
    return _get_registry()["phases"].get(phase, {}).get("mode")



def _phase_output_files(phase: str) -> list[str]:
    return _get_registry()["phases"].get(phase, {}).get("output", [])



def _phase_is_gate(phase: str) -> bool:
    return _get_registry()["phases"].get(phase, {}).get("gate") == "human"



def _state_path(project: str) -> Path:
    return _repo_root() / "_projects" / project / "pipeline-state.json"



def _load_state(project: str) -> dict:
    path = _state_path(project)
    if not path.exists():
        raise FileNotFoundError(
            f"No pipeline-state.json found for project '{project}'. Run 'start' first."
        )
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)



def _save_state(project: str, state: dict) -> None:
    path = _state_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(state, handle, indent=2)



def _next_phase(current: str) -> str | None:
    order = _phase_order()
    idx = order.index(current)
    if idx + 1 < len(order):
        return order[idx + 1]
    return None



def _is_auto(state: dict, from_phase: str) -> bool:
    for transition in state.get("transitions", []):
        if transition["from"] == from_phase:
            return transition.get("auto", True)
    return True



def _verify_output(phase: str, project: str) -> tuple[bool, str]:
    expected = _phase_output_files(phase)
    if not expected:
        return True, "No output files required"

    project_dir = _repo_root() / "_projects" / project
    missing: list[str] = []
    unfilled: list[str] = []
    template_markers = [
        "task_flow: TBD",
        "items: []",
        "<!-- AGENT: FILL -->",
        "<!-- AGENT: FILL",
    ]

    for rel_path in expected:
        full_path = project_dir / rel_path
        if not full_path.exists():
            missing.append(rel_path)
            continue
        content = full_path.read_text(encoding="utf-8", errors="ignore")
        if full_path.stat().st_size < MIN_CONTENT_SIZE:
            unfilled.append(rel_path)
        elif any(marker in content for marker in template_markers):
            unfilled.append(rel_path)

    if missing:
        return False, f"Missing output files: {', '.join(missing)}"
    if unfilled:
        return False, f"Output files still contain template placeholders: {', '.join(unfilled)}"
    return True, "All output files verified"



def get_status(project: str) -> dict:
    return _load_state(project)



def advance(project: str, approved: bool = False, revise: bool = False,
            feedback: str | None = None) -> dict:
    state = _load_state(project)
    current = state["current_phase"]

    if revise:
        if current != "2b-sign-off":
            print("⚠️  --revise is only valid at Phase 2b (Sign-Off).")
            return state

        revision_count = state.get("sign_off_revisions", 0)
        if revision_count >= 3:
            print("🛑  Maximum revision cycles (3) reached.")
            print("   You must either --approve or reset the pipeline.")
            return state

        if feedback:
            fb_path = _repo_root() / "_projects" / project / "docs" / "sign-off-feedback.md"
            fb_content = (
                f"# Sign-Off Feedback (Revision {revision_count + 1})\n\n"
                f"**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
                f"## User Feedback\n\n{feedback}\n"
            )
            fb_path.write_text(fb_content, encoding="utf-8", newline="\n")
            print(f"  📝 Feedback saved to {fb_path.relative_to(_repo_root())}")

        state["sign_off_revisions"] = revision_count + 1
        for phase in ["1-design", "2a-test-plan", "2b-sign-off"]:
            state["phases"][phase]["status"] = "pending"
        state["current_phase"] = "1-design"
        state["phases"]["1-design"]["status"] = "in_progress"

        _save_state(project, state)
        print(f"🔄  Revision {revision_count + 1}/3 — Pipeline reset to Phase 1 (Design).")
        print("   The architect will incorporate your feedback and revise.")
        print("   Run 'next' to get the architect prompt.")
        return state

    ok, msg = _verify_output(current, project)
    if not ok:
        print(f"⚠️  Cannot advance — {msg}")
        print(f"   Phase '{current}' has not produced its expected output.")
        print("   Run the agent for this phase first, then try advance again.")
        return state

    if not _is_auto(state, current) and not approved:
        print(f"🛑  Cannot advance — Phase '{current}' is a human gate.")
        print("   Review the deliverables, then run:")
        print(f"   python _shared/scripts/run-pipeline.py advance --project {project} --approve")
        return state

    state["phases"][current]["status"] = "complete"

    if current == "0a-discovery":
        _save_state(project, state)
        ok, ff_report = _runtime_callable("_fast_forward_to_signoff", "pipeline_precompute")(project)
        for line in ff_report:
            print(line)
        if ok:
            return _load_state(project)
        state = _load_state(project)

    if current == "1-design" and not state.get("task_flow"):
        tf = _runtime_callable("_extract_task_flow", "pipeline_precompute")(project)
        if tf:
            state["task_flow"] = tf
            print(f"  📋 Extracted task_flow: {tf}")

    if current == "1-design":
        _runtime_callable("_generate_architecture_summary", "pipeline_precompute")(project)

    if current == "2b-sign-off":
        _save_state(project, state)
        ok, deploy_report = _runtime_callable("_generate_deploy_artifacts", "pipeline_precompute")(project)
        for line in deploy_report:
            print(line)
        if not ok:
            print("⚠️  Deploy artifact generation failed — skill must generate manually")
        state = _load_state(project)
        if "deploy_mode" not in state:
            state["deploy_mode"] = "artifacts_only"
        ok_dh, dh_report = _runtime_callable("_generate_deployment_handoff", "pipeline_precompute")(project)
        for line in dh_report:
            print(line)
        if state.get("deploy_mode") == "artifacts_only":
            ok_vr, vr_report = _runtime_callable("_generate_validation_report", "pipeline_precompute")(project)
            for line in vr_report:
                print(line)
            if ok_dh and ok_vr:
                ok_pb, pb_report = _runtime_callable("_generate_project_brief", "pipeline_precompute")(project)
                for line in pb_report:
                    print(line)
                state["phases"]["2c-deploy"]["status"] = "complete"
                state["phases"]["3-validate"]["status"] = "complete"
                state["phases"]["4-document"]["status"] = "complete"
                state["current_phase"] = "4-document"
                _save_state(project, state)
                print("⚡ Artifacts-only: full pipeline completed deterministically")
                return state

    next_phase = _next_phase(current)
    if next_phase:
        state["current_phase"] = next_phase
        state["phases"][next_phase]["status"] = "in_progress"

    _save_state(project, state)
    return state



def reset_phase(project: str, phase: str) -> dict:
    state = _load_state(project)
    order = _phase_order()
    idx = order.index(phase)
    for phase_id in order[idx:]:
        state["phases"][phase_id]["status"] = "pending"
    state["current_phase"] = phase
    _save_state(project, state)
    return state



def reconcile(project: str) -> tuple[dict, list[str]]:
    state = _load_state(project)
    report: list[str] = []

    for phase_id in _phase_order():
        expected = _phase_output_files(phase_id)
        if not expected:
            continue

        ok, msg = _verify_output(phase_id, project)
        current_status = state["phases"][phase_id]["status"]

        if ok and current_status != "complete":
            report.append(
                f"  FIXED: {phase_id} has output files but was '{current_status}' → set to 'complete'"
            )
            state["phases"][phase_id]["status"] = "complete"
        elif not ok and current_status == "complete":
            report.append(f"  WARNING: {phase_id} marked complete but {msg}")

    if not state.get("task_flow"):
        tf = _runtime_callable("_extract_task_flow", "pipeline_precompute")(project)
        if tf:
            state["task_flow"] = tf
            report.append(f"  FIXED: Extracted task_flow '{tf}' from architecture-handoff.md")

    last_complete = None
    for phase_id in _phase_order():
        if state["phases"][phase_id]["status"] == "complete":
            last_complete = phase_id
        else:
            break

    if last_complete:
        expected_current = _next_phase(last_complete) or last_complete
        if state["current_phase"] != expected_current:
            report.append(
                f"  FIXED: current_phase was '{state['current_phase']}' → set to '{expected_current}'"
            )
            state["current_phase"] = expected_current
            if (expected_current in state["phases"]
                    and state["phases"][expected_current]["status"] == "pending"):
                state["phases"][expected_current]["status"] = "in_progress"

    if not report:
        report.append("  No drift detected — state is consistent with file evidence.")

    _save_state(project, state)
    return state, report



def start_pipeline(display_name: str, problem: str | None = None) -> dict:
    stripped = (display_name or "").strip()
    if not stripped:
        raise ValueError(
            "Project name is required and cannot be empty. "
            "Ask the user to provide a short, descriptive project name "
            "(e.g., 'Farm Fleet', 'Energy Analytics')."
        )
    if stripped.lower() in _PLACEHOLDER_NAMES:
        raise ValueError(
            f"Project name '{stripped}' looks like a placeholder. "
            "Ask the user to provide a specific, descriptive project name "
            "(e.g., 'Shop Floor Monitor', 'Machine Health')."
        )

    sanitize = _runtime_attr("sanitize_name", sanitize_name)
    scaffold_fn = _runtime_attr("scaffold", scaffold)

    project = sanitize(display_name)
    state_path = _state_path(project)
    if state_path.exists():
        print(f"⚠️  Pipeline state already exists for '{project}'. Use 'next' to advance.")
        return _load_state(project)

    scaffold_fn(str(_repo_root()), display_name)

    state = _load_state(project)
    state["display_name"] = display_name
    if problem:
        state["problem_statement"] = problem
    state["phases"]["0a-discovery"]["status"] = "in_progress"
    _save_state(project, state)
    return state
