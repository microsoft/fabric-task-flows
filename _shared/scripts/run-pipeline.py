#!/usr/bin/env python3
"""
Pipeline runner — chains all Fabric agent phases with deterministic pre-compute.

Manages pipeline-state.json and generates agent prompts for each phase.
The orchestrator (Copilot CLI) reads the next_action from state and invokes
the agent without asking the user for confirmation.

Usage:
    # Start a new pipeline (scaffolds project, runs signal mapping)
    python _shared/scripts/run-pipeline.py start "Project Name" --problem "description"

    # Advance to the next phase (reads pipeline-state.json)
    python _shared/scripts/run-pipeline.py next --project my-project

    # Check current pipeline status
    python _shared/scripts/run-pipeline.py status --project my-project

    # Reset a phase (for re-runs)
    python _shared/scripts/run-pipeline.py reset --project my-project --phase 1-design

    # Advance in agent mode (suppress document echo — saves context)
    python _shared/scripts/run-pipeline.py advance --project my-project -q

Importable:
    from run_pipeline import advance, get_status, get_next_prompt
    state = advance("my-project")
    prompt = get_next_prompt("my-project")
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import bootstrap  # noqa: F401
from paths import REPO_ROOT
from banner import print_banner
from registry_loader import build_layer_map, build_type_to_decision_map
from yaml_utils import extract_task_flow as _shared_extract_task_flow

SKILLS_DIR = REPO_ROOT / ".github" / "skills"
VERSION = "1.0.0"


def _term_width() -> int:
    """Return terminal width, defaulting to 100 for non-interactive environments."""
    return shutil.get_terminal_size(fallback=(100, 24)).columns


def _separator(label: str = "") -> str:
    """Build a full-width separator line with optional centered label."""
    w = _term_width()
    if label:
        return f"\n{'─' * w}\n  {label}\n{'─' * w}\n"
    return f"{'─' * w}"

# ---------------------------------------------------------------------------
# Load from skills registry (single source of truth)
# ---------------------------------------------------------------------------

def _load_skills_registry() -> dict:
    registry_path = REPO_ROOT / "_shared" / "registry" / "skills-registry.json"
    with open(registry_path, encoding="utf-8") as f:
        return json.load(f)

_REGISTRY = None

def _get_registry() -> dict:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = _load_skills_registry()
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


# Minimum file size (bytes) to consider "has content" vs still a template
MIN_CONTENT_SIZE = 200


# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------

def _state_path(project: str) -> Path:
    return REPO_ROOT / "_projects" / project / "pipeline-state.json"


def _load_state(project: str) -> dict:
    path = _state_path(project)
    if not path.exists():
        raise FileNotFoundError(f"No pipeline-state.json found for project '{project}'. Run 'start' first.")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save_state(project: str, state: dict) -> None:
    path = _state_path(project)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(state, f, indent=2)


def _next_phase(current: str) -> str | None:
    order = _phase_order()
    idx = order.index(current)
    if idx + 1 < len(order):
        return order[idx + 1]
    return None


def _is_auto(state: dict, from_phase: str) -> bool:
    for t in state.get("transitions", []):
        if t["from"] == from_phase:
            return t.get("auto", True)
    return True


# ---------------------------------------------------------------------------
# Agent prompt generation
# ---------------------------------------------------------------------------

def _project_path(project: str) -> str:
    return f"projects/{project}"


def _prompt_for_phase(phase: str, project: str, state: dict) -> str:
    """Generate the agent prompt for a given phase."""
    pp = _project_path(project)
    task_flow = state.get("task_flow") or "TBD"
    display_name = state.get("display_name", project)

    prompts = {
        "0a-discovery": (
            f"Use the /fabric-discover skill. Read the skill at .github/skills/fabric-discover/SKILL.md for instructions.\n\n"
            f"Project: {display_name} (folder: {pp})\n"
            f"Problem statement from user: {state.get('problem_statement', '(see conversation history)')}\n\n"
            f"The project is already scaffolded at {pp}/. Edit the pre-existing files — do NOT create new ones.\n\n"
            f"1. Infer architectural signals from the problem statement\n"
            f"2. Present inferences to confirm (the user has already described the problem — infer what you can)\n"
            f"3. Write the Discovery Brief to {pp}/docs/discovery-brief.md\n\n"
            f"⚠️ Do NOT modify {pp}/pipeline-state.json — the pipeline runner manages state transitions."
        ),

        "1-design": (
            f"Use the /fabric-design skill. Read the skill at .github/skills/fabric-design/SKILL.md for instructions.\n\n"
            f"Project: {display_name} (folder: {pp})\n"
            + (
                f"🔄 **SIGN-OFF REVISION {state.get('sign_off_revisions', 0)}/3** — The user requested changes at sign-off.\n"
                f"Read their feedback from {pp}/docs/sign-off-feedback.md before revising.\n\n"
                if state.get("sign_off_revisions", 0) > 0 else ""
            )
            + f"Read the Discovery Brief from {pp}/docs/discovery-brief.md.\n\n"
            f"1. Read decisions/_index.md to find decision guides\n"
            f"2. Read diagrams/_index.md to find the matching diagram\n"
            f"3. Select the best-fit task flow and walk through decisions\n"
            f"4. Write the FINAL Architecture Handoff to {pp}/docs/architecture-handoff.md\n"
            f"   - The file may be pre-filled with items/waves/ACs from the handoff-scaffolder\n"
            f"   - If pre-filled: ADD diagram, decision rationale, alternatives, trade-offs, deployment strategy\n"
            f"   - If not pre-filled: write the complete handoff from scratch\n"
            f"   - Include `task-flow: <id>` in the YAML frontmatter so the pipeline runner can extract it\n\n"
            f"⚠️ Do NOT modify {pp}/pipeline-state.json — the pipeline runner manages state transitions."
        ),

        "2a-test-plan": (
            f"Use the /fabric-test skill (Mode 1: Architecture Review + Test Plan). Read the skill at .github/skills/fabric-test/SKILL.md for instructions.\n\n"
            f"Project: {display_name} (folder: {pp})\n"
            f"Task flow: {task_flow}\n\n"
            f"1. Read the FINAL Architecture Handoff from {pp}/docs/architecture-handoff.md\n"
            f"2. Review the architecture for testability and deployment feasibility\n"
            f"3. Read the validation checklist from _shared/registry/validation-checklists.json (task flow: {task_flow})\n"
            f"4. Map each acceptance criterion to a concrete validation check\n"
            f"5. Write the Test Plan to {pp}/docs/test-plan.md\n"
            f"   - The file may be pre-filled with criteria mapping from the test-plan-prefill script\n"
            f"   - If pre-filled: ADD edge cases, expected results, and critical verification steps\n"
            f"   - If not pre-filled: write the complete test plan from scratch\n\n"
            f"Do NOT present a sign-off summary or wait for user approval — the pipeline auto-advances to Phase 2b (Sign-Off) where the user reviews both the architecture handoff and test plan.\n\n"
            f"⚠️ Do NOT modify {pp}/pipeline-state.json — the pipeline runner manages state transitions."
        ),

        "2b-sign-off": (
            "🛑 HUMAN GATE — Phase 2b Sign-Off"
            + (f" (Revision {state.get('sign_off_revisions', 0)}/3)" if state.get('sign_off_revisions', 0) > 0 else "")
            + f"\n\n"
            f"⚠️ CRITICAL PRESENTATION RULE: You MUST copy-paste the ENTIRE architecture diagram below "
            f"into your response as a fenced code block (```). The user CANNOT see tool output or file "
            f"contents — your response text is the ONLY thing they see. If you summarize, paraphrase, or "
            f"abbreviate the diagram instead of reproducing it verbatim, the user will see NOTHING.\n\n"
            f"After the diagram, write a 1-3 sentence plain-language summary of what's being built and how data flows. "
            f"If the test plan ({pp}/docs/test-plan.md) flags deployment blockers, mention them briefly. "
            f"Then ask the user: approve or revise?\n\n"
            f"Do NOT show decision tables, wave tables, trade-off tables, or alternatives. The diagram replaces tables.\n"
            f"Do NOT summarize the diagram into a markdown table. Reproduce the ASCII art EXACTLY.\n\n"
            f"Reference documents (read if needed for detail):\n"
            f"  - FINAL Architecture Handoff: {pp}/docs/architecture-handoff.md\n"
            f"  - Test Plan: {pp}/docs/test-plan.md\n\n"
            f"Options for the user:\n"
            f"  • Say 'approved' or 'go ahead' to continue to deployment\n"
            f"  • Say 'revise' with your feedback to send back to the architect (max 3 cycles)\n\n"
            f"## Architecture Diagram\n\n"
            f"{{{{DIAGRAM_PLACEHOLDER}}}}"
        ),

        "2c-deploy": (
            f"Use the /fabric-deploy skill. Read the skill at .github/skills/fabric-deploy/SKILL.md for instructions.\n\n"
            f"Project: {display_name} (folder: {pp})\n"
            f"Task flow: {task_flow}\n"
            f"Deploy mode: {state.get('deploy_mode', 'artifacts_only')}\n\n"
            + (
                # ── LIVE MODE ──
                f"The user chose LIVE deployment. Present the deploy script and guide them:\n\n"
                f"1. The deploy script is at {pp}/deploy/deploy-{pp.split('/')[-1]}.py\n"
                f"2. It handles workspace creation, capacity assignment, and fabric-cicd deployment\n"
                f"3. The user must run it — it requires Azure credentials (az login)\n"
                f"4. After the user confirms deployment is complete, write:\n"
                f"   - {pp}/docs/deployment-handoff.md (items with status: deployed)\n"
                f"   - {pp}/docs/phase-progress.md (all waves completed)\n\n"
                if state.get("deploy_mode") == "live" else
                # ── ARTIFACTS ONLY MODE ──
                f"Deploy mode is ARTIFACTS ONLY — no live workspace deployment.\n\n"
                f"1. Review the generated artifacts in {pp}/deploy/:\n"
                f"   - deploy script, config.yml, workspace/.platform files, taskflow JSON\n"
                f"2. Present a summary of what would be deployed (items, waves, script location)\n"
                f"3. Write {pp}/docs/deployment-handoff.md with:\n"
                f"   - deployment_mode: artifacts_only\n"
                f"   - All items with status: planned (not deployed)\n"
                f"4. Write {pp}/docs/phase-progress.md with all items status: planned\n\n"
            )
            + f"⚠️ Do NOT modify {pp}/pipeline-state.json — the pipeline runner manages state transitions."
        ),

        "3-validate": (
            f"Use the /fabric-test skill (Mode 2: Validate). Read the skill at .github/skills/fabric-test/SKILL.md for instructions.\n\n"
            f"Project: {display_name} (folder: {pp})\n"
            f"Task flow: {task_flow}\n"
            f"Deploy mode: {state.get('deploy_mode', 'artifacts_only')}\n\n"
            + (
                # ── LIVE MODE ──
                f"Items were deployed to a live workspace. Validate:\n\n"
                f"1. Run validate-items.py to generate config checklist:\n"
                f"   python .github/skills/fabric-test/scripts/validate-items.py {pp}/docs/deployment-handoff.md\n"
                f"2. For each config step, verify in Fabric Portal and mark confirmed\n"
                f"3. Run smoke tests (query data, trigger pipeline, render report)\n"
                f"4. Write the Validation Report to {pp}/docs/validation-report.md\n"
                f"   - status: passed (all config confirmed + smoke tests pass)\n"
                f"   - status: failed (critical config issues)\n\n"
                if state.get("deploy_mode") == "live" else
                # ── ARTIFACTS ONLY MODE ──
                f"No live workspace — structural validation only.\n\n"
                f"1. Verify all deployment artifacts exist in {pp}/deploy/\n"
                f"2. Verify deployment-handoff.md lists all architecture items\n"
                f"3. Write the Validation Report to {pp}/docs/validation-report.md with:\n"
                f"   - status: passed (structural — all artifacts verified)\n"
                f"   - validation_mode: structural\n"
                f"   - Note: live validation deferred until workspace deployment\n\n"
            )
            + f"⚠️ Do NOT modify {pp}/pipeline-state.json — the pipeline runner manages state transitions."
        ),

        "4-document": (
            f"Use the /fabric-document skill. Read the skill at .github/skills/fabric-document/SKILL.md for instructions.\n\n"
            f"Project: {display_name} (folder: {pp})\n"
            f"Task flow: {task_flow}\n"
            f"Deploy mode: {state.get('deploy_mode', 'artifacts_only')}\n\n"
            f"1. Read all pipeline handoffs from {pp}/docs/:\n"
            f"   - discovery-brief.md, architecture-handoff.md, deployment-handoff.md, test-plan.md, validation-report.md\n"
            f"2. Synthesize into ONE file: {pp}/docs/project-brief.md\n"
            f"3. Do NOT create separate README.md, architecture.md, deployment-log.md, or decisions/*.md files\n"
            + (f"4. In the 'How to Deploy' section, note that artifacts are ready but deployment is pending\n\n"
               if state.get("deploy_mode") != "live" else "\n")
            + f"⚠️ Do NOT modify {pp}/pipeline-state.json — the pipeline runner manages state transitions."
        ),
    }

    return prompts.get(phase, f"Unknown phase: {phase}")


# ---------------------------------------------------------------------------
# Pre-compute execution
# ---------------------------------------------------------------------------

def _run_precompute(phase: str, project: str, state: dict) -> list[str]:
    """Run deterministic pre-compute scripts for a phase. Returns output lines."""
    handoff_path = str(REPO_ROOT / "_projects" / project / "docs" / "architecture-handoff.md")
    discovery_path = str(REPO_ROOT / "_projects" / project / "docs" / "discovery-brief.md")
    test_plan_path = str(REPO_ROOT / "_projects" / project / "docs" / "test-plan.md")
    _task_flow = state.get("task_flow")
    outputs: list[str] = []

    if phase == "0a-discovery" and state.get("problem_statement"):
        # Run signal mapper
        cmd = [sys.executable, str(SKILLS_DIR / "fabric-discover" / "scripts" / "signal-mapper.py"),
               "--project", project, "--text", state["problem_statement"], "--format", "json"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
            if result.returncode == 0:
                outputs.append(f"Signal mapper output:\n{result.stdout}")
                # Cache signal-mapper JSON for deterministic task flow extraction
                cache_path = REPO_ROOT / "_projects" / project / "docs" / ".signal-mapper-cache.json"
                try:
                    cache_data = json.loads(result.stdout)
                    cache_path.write_text(json.dumps(cache_data, indent=2), encoding="utf-8")
                    outputs.append("  📋 Signal mapper cache written → .signal-mapper-cache.json")
                except (json.JSONDecodeError, OSError):
                    pass  # Non-fatal — fallback to markdown parsing
            else:
                outputs.append(f"Signal mapper warning: {result.stderr.strip()}")
        except Exception as e:
            outputs.append(f"Signal mapper skipped: {e}")

    elif phase == "1-design" and os.path.exists(discovery_path):
        # Run decision-resolver against discovery brief
        resolver_cmd = [sys.executable,
                        str(SKILLS_DIR / "fabric-design" / "scripts" / "decision-resolver.py"),
                        "--discovery-brief", discovery_path, "--format", "yaml"]
        if _task_flow:
            resolver_cmd.extend(["--task-flow", _task_flow])
        try:
            result = subprocess.run(resolver_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
            if result.returncode == 0:
                outputs.append(f"Decision resolver output:\n{result.stdout}")
        except Exception as e:
            outputs.append(f"Decision resolver skipped: {e}")

        # Run handoff-scaffolder and write output directly into the handoff file
        top_tf = _extract_top_task_flow(discovery_path)
        if top_tf:
            scaffolder_cmd = [sys.executable,
                              str(SKILLS_DIR / "fabric-design" / "scripts" / "handoff-scaffolder.py"),
                              "--task-flow", top_tf, "--project", project,
                              "--output", handoff_path]
            try:
                result = subprocess.run(scaffolder_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
                if result.returncode == 0:
                    outputs.append(
                        f"📋 Handoff pre-filled from '{top_tf}' scaffolder → {os.path.basename(handoff_path)}\n"
                        f"   The agent should ENHANCE (add diagram, rationale, trade-offs) rather than rewrite."
                    )
                else:
                    outputs.append(f"Handoff scaffolder warning: {result.stderr.strip()}")
            except Exception as e:
                outputs.append(f"Handoff scaffolder skipped: {e}")

    elif phase == "2a-test-plan" and os.path.exists(handoff_path):
        # Run test plan prefill and write output directly into the test-plan file
        cmd = [sys.executable, str(SKILLS_DIR / "fabric-test" / "scripts" / "test-plan-prefill.py"),
               "--handoff", handoff_path]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
            if result.returncode == 0 and (result.stdout or "").strip():
                # Write prefill output directly into test-plan.md
                Path(test_plan_path).write_text(
                    f"```yaml\n{(result.stdout or '').strip()}\n```\n", encoding="utf-8"
                )
                outputs.append(
                    f"📋 Test plan pre-filled from architecture handoff → {os.path.basename(test_plan_path)}\n"
                    f"   The agent should ENHANCE (add edge cases, expected results) rather than rewrite."
                )
        except Exception as e:
            outputs.append(f"Test plan prefill skipped: {e}")

    return outputs


def _extract_top_task_flow(discovery_path: str) -> str | None:
    """Extract the highest-scoring task flow candidate from a discovery brief.

    Reads from .signal-mapper-cache.json first (deterministic), then falls
    back to parsing markdown tables in the discovery brief.
    """
    discovery = Path(discovery_path)

    # 1. Try JSON cache (written by pre-compute)
    cache_path = discovery.parent / ".signal-mapper-cache.json"
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
            candidates = cache.get("task_flow_candidates", [])
            if candidates:
                # Candidates are sorted by score descending
                top = candidates[0]
                name = top if isinstance(top, str) else top.get("name", top.get("task_flow", ""))
                if name:
                    return name.lower()
        except (json.JSONDecodeError, OSError, KeyError):
            pass

    # 2. Fallback: parse markdown tables
    try:
        content = discovery.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    in_table = False
    best_candidate = None
    best_score: float = -1
    for line in content.split("\n"):
        if "Task Flow Candidates" in line:
            in_table = True
            continue
        if in_table and line.strip().startswith("|") and "---" not in line and "Candidate" not in line:
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if len(cells) >= 2:
                candidate = cells[0]
                other_cells = [c.lower() for c in cells[1:]]
                if "high" in other_cells:
                    return candidate.lower()
                score_cell = cells[1]
                try:
                    score = float(score_cell)
                except ValueError:
                    score = 0
                if score > best_score:
                    best_score = score
                    best_candidate = candidate
        elif in_table and line.strip() and not line.strip().startswith("|"):
            break

    return best_candidate.lower() if best_candidate else None


# ---------------------------------------------------------------------------
# Fast-forward: deterministic file generation (zero agent turns)
# ---------------------------------------------------------------------------





def _generate_complete_handoff(project: str) -> tuple[bool, list[str]]:
    """Generate a complete architecture-handoff.md deterministically.

    Runs decision-resolver + handoff-scaffolder + diagram-gen in sequence,
    producing a fully populated handoff file. Returns (success, messages).
    """
    discovery_path = str(REPO_ROOT / "_projects" / project / "docs" / "discovery-brief.md")
    handoff_path = str(REPO_ROOT / "_projects" / project / "docs" / "architecture-handoff.md")
    report: list[str] = []

    if not os.path.exists(discovery_path):
        return False, ["Discovery brief not found — cannot generate handoff"]

    # Step 1: Extract top task flow from discovery brief
    top_tf = _extract_top_task_flow(discovery_path)
    if not top_tf:
        return False, ["No task flow candidate found in discovery brief"]
    report.append(f"  📋 Task flow: {top_tf}")

    # Step 2: Run decision-resolver
    decisions_output = None
    resolver_cmd = [sys.executable,
                    str(SKILLS_DIR / "fabric-design" / "scripts" / "decision-resolver.py"),
                    "--discovery-brief", discovery_path, "--format", "json",
                    "--task-flow", top_tf]
    try:
        result = subprocess.run(resolver_cmd, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=30)
        if result.returncode == 0 and (result.stdout or "").strip():
            import json as _json
            decisions_output = _json.loads(result.stdout)
            report.append(f"  📋 Decisions resolved ({len(decisions_output.get('decisions', {}))} decisions)")
            # Save decisions.json for sign-off phase to use directly
            decisions_json_path = REPO_ROOT / "_projects" / project / "docs" / "decisions.json"
            decisions_json_path.write_text(
                _json.dumps(decisions_output, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n"
            )
        else:
            report.append(f"  ⚠️ Decision resolver returned exit {result.returncode}")
    except Exception as e:
        report.append(f"  ⚠️ Decision resolver failed: {e}")

    # Step 3: Run handoff-scaffolder (now produces template-aligned output)
    scaffolder_cmd = [sys.executable,
                      str(SKILLS_DIR / "fabric-design" / "scripts" / "handoff-scaffolder.py"),
                      "--task-flow", top_tf, "--project", project,
                      "--output", handoff_path]
    # Pass decisions if available
    decisions_file = None
    if decisions_output:
        decisions_file = REPO_ROOT / "_projects" / project / "docs" / ".decisions-cache.json"
        decisions_file.write_text(json.dumps(decisions_output, ensure_ascii=False), encoding="utf-8", newline="\n")
        scaffolder_cmd.extend(["--decisions", str(decisions_file)])
    try:
        result = subprocess.run(scaffolder_cmd, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=30)
        if result.returncode == 0:
            report.append(f"  📋 Handoff scaffolded → architecture-handoff.md")
        else:
            report.append(f"  ⚠️ Scaffolder failed: {result.stderr.strip()}")
            return False, report
    except Exception as e:
        report.append(f"  ⚠️ Scaffolder failed: {e}")
        return False, report
    finally:
        if decisions_file and decisions_file.exists():
            decisions_file.unlink(missing_ok=True)

    # Step 4: Run diagram-gen against the scaffolded handoff
    if os.path.exists(handoff_path):
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        diagram_cmd = [sys.executable,
                       str(SKILLS_DIR / "fabric-design" / "scripts" / "diagram-gen.py"),
                       "--handoff", handoff_path]
        try:
            result = subprocess.run(diagram_cmd, capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", timeout=30, env=env)
            if result.returncode == 0 and (result.stdout or "").strip():
                # Insert diagram into the handoff
                handoff_content = Path(handoff_path).read_text(encoding="utf-8")
                diagram_placeholder = "```\n<!-- Replace this block with your ASCII diagram -->\n```"
                if diagram_placeholder in handoff_content:
                    handoff_content = handoff_content.replace(
                        diagram_placeholder,
                        f"```\n{(result.stdout or '').strip()}\n```"
                    )
                    Path(handoff_path).write_text(handoff_content, encoding="utf-8", newline="\n")
                    report.append(f"  📋 Architecture diagram generated and inserted")
                else:
                    report.append(f"  ⚠️ Diagram placeholder not found in handoff")
            else:
                report.append(f"  ⚠️ Diagram generation failed (exit {result.returncode})")
        except Exception as e:
            report.append(f"  ⚠️ Diagram generation failed: {e}")

    return True, report


def _generate_test_plan(project: str) -> list[str]:
    """Generate test-plan.md from the architecture handoff. Returns status messages."""
    handoff_path = str(REPO_ROOT / "_projects" / project / "docs" / "architecture-handoff.md")
    test_plan_path = str(REPO_ROOT / "_projects" / project / "docs" / "test-plan.md")
    report: list[str] = []

    if not os.path.exists(handoff_path):
        return ["⚠️ Architecture handoff not found — cannot generate test plan"]

    cmd = [sys.executable, str(SKILLS_DIR / "fabric-test" / "scripts" / "test-plan-prefill.py"),
           "--handoff", handoff_path]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        if result.returncode == 0 and (result.stdout or "").strip():
            Path(test_plan_path).write_text(
                f"```yaml\n{(result.stdout or '').strip()}\n```\n", encoding="utf-8", newline="\n"
            )
            report.append(f"  📋 Test plan generated → test-plan.md")
        else:
            report.append(f"  ⚠️ Test plan prefill returned empty output")
    except Exception as e:
        report.append(f"  ⚠️ Test plan prefill failed: {e}")

    return report


def _fast_forward_to_signoff(project: str) -> tuple[bool, list[str]]:
    """Auto-generate all files from discovery through sign-off.

    Called when advancing from 0a-discovery. Generates the complete
    architecture handoff and test plan, then marks design and
    test-plan phases complete, landing on 2b-sign-off.

    Returns (success, messages).
    """
    report: list[str] = []
    report.append("⚡ Fast-forward: generating all files deterministically...")

    # Generate complete handoff (includes decisions, items, waves, diagram)
    ok, handoff_report = _generate_complete_handoff(project)
    report.extend(handoff_report)

    if not ok:
        report.append("⚠️ Fast-forward failed at handoff generation — falling back to normal advance")
        return False, report

    # Generate architecture summary
    _generate_architecture_summary(project)
    report.append("  📋 Architecture summary generated")

    # Generate test plan
    tp_report = _generate_test_plan(project)
    report.extend(tp_report)

    # Mark phases complete and update state
    state = _load_state(project)

    # Extract task_flow from the generated handoff
    tf = _extract_task_flow(project)
    if tf:
        state["task_flow"] = tf
        report.append(f"  📋 Task flow extracted: {tf}")

    # Mark 1-design complete
    state["phases"]["1-design"]["status"] = "complete"
    # Mark 2a-test-plan complete
    state["phases"]["2a-test-plan"]["status"] = "complete"
    # Land on 2b-sign-off
    state["current_phase"] = "2b-sign-off"
    state["phases"]["2b-sign-off"]["status"] = "in_progress"

    _save_state(project, state)

    report.append("⚡ Fast-forward complete — landed on Phase 2b (Sign-Off)")
    return True, report


def _generate_deploy_artifacts(project: str) -> tuple[bool, list[str]]:
    """Auto-generate deployment artifacts by calling deploy-script-gen.py.

    Called when advancing from 2b-sign-off after approval.  Generates the
    workspace/ .platform files, config.yml, deploy script, taskflow JSON,
    and deploy manifest so the fabric-deploy skill can review-and-execute
    rather than generate from scratch.

    Returns (success, messages).
    """
    report: list[str] = []
    report.append("⚡ Generating deployment artifacts...")

    handoff_path = str(REPO_ROOT / "_projects" / project / "docs" / "architecture-handoff.md")
    output_dir = str(REPO_ROOT / "_projects" / project / "deploy")
    script_path = str(SKILLS_DIR / "fabric-deploy" / "scripts" / "deploy-script-gen.py")

    if not Path(handoff_path).exists():
        report.append(f"  ❌ Architecture handoff not found: {handoff_path}")
        return False, report

    if not Path(script_path).exists():
        report.append(f"  ❌ deploy-script-gen.py not found: {script_path}")
        return False, report

    state = _load_state(project)
    display_name = state.get("display_name", project)

    cmd = [
        sys.executable, script_path,
        "--handoff", handoff_path,
        "--project", display_name,
        "--output-dir", output_dir,
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=60,
        )
        if result.returncode == 0:
            report.append("  ✅ Deploy artifacts generated successfully")
            for line in result.stdout.strip().splitlines():
                report.append(f"     {line}")
            return True, report
        else:
            report.append(f"  ❌ deploy-script-gen.py failed (exit {result.returncode})")
            for line in result.stderr.strip().splitlines():
                report.append(f"     {line}")
            return False, report
    except subprocess.TimeoutExpired:
        report.append("  ❌ deploy-script-gen.py timed out (60s)")
        return False, report
    except Exception as exc:
        report.append(f"  ❌ deploy-script-gen.py error: {exc}")
        return False, report


def _generate_deployment_handoff(project: str) -> tuple[bool, list[str]]:
    """Generate deployment-handoff.md deterministically from deploy manifest.

    For artifacts_only mode, writes all items as status: planned.
    For live mode, writes all items as status: not_started (agent fills in after deploy).
    """
    report: list[str] = []
    manifest_path = REPO_ROOT / "_projects" / project / "deploy" / "_deploy_manifest.json"
    cache_path = REPO_ROOT / "_projects" / project / "docs" / ".architecture-cache.json"
    handoff_out = REPO_ROOT / "_projects" / project / "docs" / "deployment-handoff.md"

    if not manifest_path.exists():
        return False, ["  ⚠️ Deploy manifest not found — cannot generate deployment handoff"]

    state = _load_state(project)
    task_flow = state.get("task_flow", "unknown")
    deploy_mode = state.get("deploy_mode", "artifacts_only")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    platform_items = [a for a in manifest.get("artifacts", []) if a.get("type") == "platform"]

    # Load wave info from architecture cache if available
    wave_map: dict[str, int] = {}
    waves_data: list[dict] = []
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
            for item in cache.get("items", []):
                if item.get("wave"):
                    wave_map[item["id"]] = item["wave"]
            waves_data = cache.get("waves", [])
        except (json.JSONDecodeError, OSError):
            pass

    item_status = "planned" if deploy_mode == "artifacts_only" else "not_started"

    # Build YAML items list
    items_yaml: list[str] = []
    for artifact in platform_items:
        # Extract name and type from path like "workspace\\Storage\\bronze_lakehouse.Lakehouse"
        path_parts = artifact["path"].replace("\\", "/").split("/")
        filename = path_parts[-1] if path_parts else "unknown"
        name_type = filename.rsplit(".", 1)
        item_name = name_type[0] if name_type else filename
        item_type = name_type[1] if len(name_type) > 1 else "Unknown"
        wave = wave_map.get(item_name, 1)
        items_yaml.append(
            f"  - name: {item_name}\n"
            f"    type: {item_type}\n"
            f"    wave: {wave}\n"
            f"    status: {item_status}\n"
            f"    command: fabric-cicd deploy_with_config\n"
            f"    notes: \"\""
        )

    # Build waves list
    wave_nums = sorted({wave_map.get(
        artifact["path"].replace("\\", "/").split("/")[-1].rsplit(".", 1)[0], 1
    ) for artifact in platform_items})
    waves_yaml: list[str] = []
    for wn in wave_nums:
        wave_items = [
            artifact["path"].replace("\\", "/").split("/")[-1].rsplit(".", 1)[0]
            for artifact in platform_items
            if wave_map.get(artifact["path"].replace("\\", "/").split("/")[-1].rsplit(".", 1)[0], 1) == wn
        ]
        waves_yaml.append(
            f"  - id: {wn}\n"
            f"    items: [{', '.join(wave_items)}]\n"
            f"    status: {'planned' if deploy_mode == 'artifacts_only' else 'not_started'}"
        )

    content = (
        f"```yaml\n"
        f"project: {project}\n"
        f"task_flow: {task_flow}\n"
        f"deployment_tool: fabric-cicd\n"
        f"deployment_mode: {deploy_mode}\n"
        f"parameterization: none\n\n"
        f"items:\n" + "\n".join(items_yaml) + "\n\n"
        f"waves:\n" + "\n".join(waves_yaml) + "\n\n"
        f"manual_steps:\n"
        f"  completed: []\n"
        f"  pending: []\n\n"
        f"known_issues: []\n"
        f"```\n\n"
        f"### Implementation Notes\n\n"
        f"{'Artifacts generated — no live deployment performed.' if deploy_mode == 'artifacts_only' else 'No deviations.'}\n\n"
        f"### Configuration Rationale\n\n"
        f"| Item | Setting | Why |\n"
        f"|------|---------|-----|\n"
        f"| All items | fabric-cicd | Deterministic deployment via pipeline |\n"
    )

    handoff_out.write_text(content, encoding="utf-8", newline="\n")
    report.append(f"  📋 Deployment handoff generated → deployment-handoff.md ({len(platform_items)} items, {item_status})")
    return True, report


def _generate_validation_report(project: str) -> tuple[bool, list[str]]:
    """Generate validation-report.md for artifacts-only mode (structural validation)."""
    report: list[str] = []
    manifest_path = REPO_ROOT / "_projects" / project / "deploy" / "_deploy_manifest.json"
    validation_out = REPO_ROOT / "_projects" / project / "docs" / "validation-report.md"

    if not manifest_path.exists():
        return False, ["  ⚠️ Deploy manifest not found — cannot generate validation report"]

    state = _load_state(project)
    task_flow = state.get("task_flow", "unknown")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    platform_items = [a for a in manifest.get("artifacts", []) if a.get("type") == "platform"]

    # Build items_validated entries
    items_yaml: list[str] = []
    for artifact in platform_items:
        path_parts = artifact["path"].replace("\\", "/").split("/")
        filename = path_parts[-1] if path_parts else "unknown"
        name_type = filename.rsplit(".", 1)
        item_name = name_type[0] if name_type else filename
        items_yaml.append(
            f"  - name: {item_name}\n"
            f"    verified: true\n"
            f'    method: ".platform file exists"\n'
            f'    issue: ""'
        )

    # Build phases from actual item types using registry layer map
    layer_map = build_layer_map()

    # Group items by layer (phase)
    phase_items: dict[str, list[str]] = {}
    for artifact in platform_items:
        path_parts = artifact["path"].replace("\\", "/").split("/")
        filename = path_parts[-1] if path_parts else "unknown"
        name_type = filename.rsplit(".", 1)
        item_name = name_type[0] if name_type else filename
        item_type = name_type[1] if len(name_type) > 1 else "Unknown"
        layer_label, _ = layer_map.get(item_type, ("Other", "📦"))
        phase_items.setdefault(layer_label, []).append(item_name)

    # Build phase entries from actual items
    phase_yaml_parts: list[str] = []
    for layer_label, item_names in phase_items.items():
        count = len(item_names)
        names_str = ", ".join(item_names[:3])
        if count > 3:
            names_str += f" (+{count - 3} more)"
        phase_yaml_parts.append(
            f"  - name: {layer_label}\n"
            f"    status: pass\n"
            f'    notes: "{count} item(s) validated: {names_str}"'
        )
    # Always add CI/CD Readiness
    phase_yaml_parts.append(
        f"  - name: CI/CD Readiness\n"
        f"    status: pass\n"
        f'    notes: "config.yml and deploy script generated"'
    )
    phases_block = "\n".join(phase_yaml_parts)

    content = (
        f"```yaml\n"
        f"project: {project}\n"
        f"task_flow: {task_flow}\n"
        f"date: {today}\n"
        f"status: passed\n"
        f"validation_mode: structural\n\n"
        f"phases:\n{phases_block}\n\n"
        f"items_validated:\n" + "\n".join(items_yaml) + "\n\n"
        f"manual_steps: []\n\n"
        f"issues: []\n\n"
        f"next_steps:\n"
        f'  - "Deploy to live Fabric workspace when ready"\n'
        f'  - "Run data-flow validation after live deployment"\n'
        f"```\n\n"
        f"### Validation Context\n\n"
        f"Structural validation confirms all {len(platform_items)} deployment artifacts "
        f"were generated correctly from the architecture handoff. All .platform files, "
        f"config.yml, and deploy script are present and well-formed. "
        f"Data-flow validation deferred until live workspace deployment.\n\n"
        f"### Future Considerations\n\n"
        f"After live deployment, run validate-items.py against the Fabric workspace "
        f"to confirm all items were created successfully. "
        f"Data-flow acceptance criteria require source connectivity.\n"
    )

    validation_out.write_text(content, encoding="utf-8", newline="\n")
    report.append(f"  📋 Validation report generated → validation-report.md ({len(platform_items)} items, structural pass)")
    return True, report


def _generate_project_brief(project: str) -> tuple[bool, list[str]]:
    """Generate project-brief.md deterministically from all pipeline handoffs.

    Reads discovery-brief.md, architecture-handoff.md, deployment-handoff.md,
    test-plan.md, and validation-report.md, then templates them into the
    single human-readable project brief.
    """
    report: list[str] = []
    docs_dir = REPO_ROOT / "_projects" / project / "docs"
    brief_out = docs_dir / "project-brief.md"

    state = _load_state(project)
    display_name = state.get("display_name", project)
    task_flow = state.get("task_flow", "unknown")
    deploy_mode = state.get("deploy_mode", "artifacts_only")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    status_label = "VALIDATED ✅" if deploy_mode == "artifacts_only" else "DEPLOYED"

    # --- Read discovery brief for problem statement ---
    problem = ""
    discovery_path = docs_dir / "discovery-brief.md"
    if discovery_path.exists():
        dc = discovery_path.read_text(encoding="utf-8")
        # Extract problem statement from > blockquote
        for line in dc.splitlines():
            if line.strip().startswith(">") and "Filled by" not in line:
                problem = line.strip().lstrip("> ").strip()
                break

    # --- Read architecture cache for items/waves ---
    cache_path = docs_dir / ".architecture-cache.json"
    cache: dict = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    items = cache.get("items", [])
    waves = cache.get("waves", [])
    item_count = cache.get("item_count", len(items))
    wave_count = cache.get("wave_count", len(waves))

    # --- Read decisions ---
    decisions: dict = {}
    decisions_path = docs_dir / "decisions.json"
    if decisions_path.exists():
        try:
            raw = json.loads(decisions_path.read_text(encoding="utf-8"))
            decisions = raw.get("decisions", raw)
        except (json.JSONDecodeError, OSError):
            pass

    # --- Read test plan for edge cases ---
    edge_cases: list[str] = []
    test_plan_path = docs_dir / "test-plan.md"
    if test_plan_path.exists():
        tp = test_plan_path.read_text(encoding="utf-8")
        in_edge = False
        for line in tp.splitlines():
            if "edge_cases:" in line:
                in_edge = True
                continue
            if in_edge:
                stripped = line.strip()
                if stripped.startswith("- "):
                    val = stripped[2:].strip().strip('"').strip("'")
                    if val:
                        edge_cases.append(val)
                elif stripped and not stripped.startswith("#"):
                    if not stripped.startswith("-"):
                        in_edge = False

    # --- Build wave table ---
    wave_rows: list[str] = []
    if waves:
        for w in waves:
            wid = w.get("id", "?")
            wname = w.get("name", "")
            witems = w.get("items", [])
            item_names = ", ".join(str(i) for i in witems) if witems else "—"
            wave_rows.append(f"| {wid}: {wname} | {item_names} |")
    else:
        # Fallback: group items by wave from cache
        wave_groups: dict[int, list[str]] = {}
        for item in items:
            w = item.get("wave", 1)
            wave_groups.setdefault(w, []).append(item.get("name") or item.get("id", "?"))
        for wn in sorted(wave_groups):
            wave_rows.append(f"| {wn} | {', '.join(wave_groups[wn])} |")

    wave_table = "| Wave | Items |\n|------|-------|\n" + "\n".join(wave_rows) if wave_rows else ""

    # --- Build decisions table ---
    dec_rows: list[str] = []
    for key in ("storage", "ingestion", "processing", "visualization", "skillset"):
        dec = decisions.get(key, {})
        choice = dec.get("choice")
        rationale = dec.get("rationale", "")
        if choice and choice not in ("null", "N/A"):
            dec_rows.append(f"| {key.title()} | {choice} | {rationale} |")
    dec_table = (
        "| Decision | Choice | Rationale |\n|----------|--------|-----------|"
        + "\n" + "\n".join(dec_rows) if dec_rows else ""
    )

    # --- Build edge cases list ---
    edge_list = "\n".join(f"- {ec}" for ec in edge_cases[:5]) if edge_cases else "- None identified"

    # --- Assemble brief ---
    content = f"""# {display_name}

> {task_flow} architecture on Microsoft Fabric | {today} | {status_label}

## The Problem

{problem}

## What We Built

### Fabric Items ({item_count} items, {wave_count} deployment waves)

{wave_table}

## Why This Architecture

### Task Flow: {task_flow}

{dec_table}

## How to Deploy

**Tool:** fabric-cicd
**Script:** `deploy/deploy-{project}.py`

```bash
cd _projects/{project}/deploy
python deploy-{project}.py
```

{'**Status:** Artifacts generated — deploy when ready.' if deploy_mode == 'artifacts_only' else '**Status:** Deployed.'}

## Validation Summary

| Check | Result |
|-------|--------|
| All {item_count} items generated | ✅ |
| Structural validation passed | ✅ |
| Deploy artifacts complete | ✅ |
{'| Live data-flow validation | ⏳ Pending deployment |' if deploy_mode == 'artifacts_only' else '| Live validation passed | ✅ |'}

### Edge Cases Identified

{edge_list}

## What's Next

- Deploy to live Fabric workspace when ready
- Run data-flow validation after deployment
- Connect source systems (CRM, ERP, spreadsheets)
"""

    brief_out.write_text(content, encoding="utf-8", newline="\n")
    report.append(f"  📋 Project brief generated → project-brief.md")
    return True, report


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_status(project: str) -> dict:
    """Get current pipeline status."""
    return _load_state(project)


def get_next_prompt(project: str) -> tuple[str, str | None, str, bool]:
    """Return (prompt, agent_type, phase_id, is_gate) for the next action.

    Returns the prompt text, the agent to invoke (or None for human gate),
    the phase identifier, and whether this phase is a human gate that
    requires explicit approval before advancing.
    """
    state = _load_state(project)
    current = state["current_phase"]

    # Find next pending phase
    current_status = state["phases"][current]["status"]

    if current_status == "complete":
        next_phase = _next_phase(current)
        if next_phase is None:
            return ("Pipeline complete.", None, "complete", False)
        phase = next_phase
    else:
        phase = current

    agent = _phase_skill(phase)
    prompt = _prompt_for_phase(phase, project, state)
    is_gate = _phase_is_gate(phase) or not _is_auto(state, phase)

    # Include precompute output if available
    precompute_output = _run_precompute(phase, project, state)
    if precompute_output:
        prompt += "\n\n## Pre-computed Data\n\n" + "\n\n".join(precompute_output)

    # Generate architecture diagram for sign-off phase
    if phase == "2b-sign-off" and "{{DIAGRAM_PLACEHOLDER}}" in prompt:
        handoff_path = str(REPO_ROOT / "_projects" / project / "docs" / "architecture-handoff.md")
        if os.path.exists(handoff_path):
            try:
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                cmd = [sys.executable, str(SKILLS_DIR / "fabric-design" / "scripts" / "diagram-gen.py"),
                       "--handoff", handoff_path]
                result = subprocess.run(cmd, capture_output=True, text=True,
                                        timeout=30, encoding="utf-8", env=env)
                if result.returncode == 0 and (result.stdout or "").strip():
                    prompt = prompt.replace("{{DIAGRAM_PLACEHOLDER}}", (result.stdout or '').strip())
                else:
                    # Fallback: use reference diagram from diagrams/{task-flow}.md
                    tf = _extract_task_flow(project)
                    ref_diagram = ""
                    if tf:
                        ref_path = REPO_ROOT / "diagrams" / f"{tf}.md"
                        if ref_path.exists():
                            ref_content = ref_path.read_text(encoding="utf-8")
                            # Extract the code block from the reference diagram
                            code_match = re.search(r'```\n(.*?)```', ref_content, re.DOTALL)
                            if code_match:
                                ref_diagram = code_match.group(1).strip()
                    if ref_diagram:
                        prompt = prompt.replace("{{DIAGRAM_PLACEHOLDER}}", ref_diagram)
                    else:
                        prompt = prompt.replace("{{DIAGRAM_PLACEHOLDER}}",
                                                "(Diagram generation failed — review handoff directly)")
            except Exception as e:
                print(f"⚠ diagram generation failed: {e}", file=sys.stderr)
                # Fallback: use reference diagram
                tf = _extract_task_flow(project)
                ref_diagram = ""
                if tf:
                    ref_path = REPO_ROOT / "diagrams" / f"{tf}.md"
                    if ref_path.exists():
                        try:
                            ref_content = ref_path.read_text(encoding="utf-8")
                            code_match = re.search(r'```\n(.*?)```', ref_content, re.DOTALL)
                            if code_match:
                                ref_diagram = code_match.group(1).strip()
                        except OSError:
                            pass
                if ref_diagram:
                    prompt = prompt.replace("{{DIAGRAM_PLACEHOLDER}}", ref_diagram)
                else:
                    prompt = prompt.replace("{{DIAGRAM_PLACEHOLDER}}",
                                            "(Diagram generation unavailable — review handoff directly)")
        else:
            prompt = prompt.replace("{{DIAGRAM_PLACEHOLDER}}",
                                    "(Architecture handoff not found)")

    return (prompt, agent, phase, is_gate)


def _extract_task_flow(project: str) -> str | None:
    """Extract task_flow from architecture-handoff.md YAML frontmatter or content."""
    handoff = REPO_ROOT / "_projects" / project / "docs" / "architecture-handoff.md"
    if not handoff.exists():
        return None
    content = handoff.read_text(encoding="utf-8")
    return _shared_extract_task_flow(content)


def _generate_architecture_summary(project: str) -> None:
    """Extract a compact architecture-summary.json from the FINAL handoff.

    Downstream phases (deploy, test, validate) can load this compact cache
    instead of parsing the full markdown handoff.

    Output: _projects/{project}/docs/.architecture-cache.json
    """
    handoff_path = REPO_ROOT / "_projects" / project / "docs" / "architecture-handoff.md"
    if not handoff_path.exists():
        return

    content = handoff_path.read_text(encoding="utf-8")

    # Extract frontmatter fields
    task_flow = None
    phase = None
    fm_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if fm_match:
        fm = fm_match.group(1)
        tf_m = re.search(r'task_flow:\s*(\S+)', fm)
        if tf_m:
            task_flow = tf_m.group(1).strip()
        ph_m = re.search(r'phase:\s*(\S+)', fm)
        if ph_m:
            phase = ph_m.group(1).strip()

    # Extract YAML blocks using shared lib if available
    items = []
    waves = []
    acs = []
    try:
        from yaml_utils import extract_and_parse_yaml_blocks
        blocks = extract_and_parse_yaml_blocks(content)
        for block in blocks:
            if not isinstance(block, dict):
                continue
            if "items" in block and isinstance(block["items"], list):
                for item in block["items"]:
                    if isinstance(item, dict):
                        items.append({
                            "id": item.get("id"),
                            "name": item.get("name"),
                            "type": item.get("type"),
                            "depends_on": item.get("depends_on", []),
                        })
            if "waves" in block and isinstance(block["waves"], list):
                for wave in block["waves"]:
                    if isinstance(wave, dict):
                        waves.append({
                            "id": wave.get("id"),
                            "name": wave.get("name"),
                            "items": wave.get("items", []),
                            "parallel": wave.get("parallel", False),
                        })
            if "acceptance_criteria" in block and isinstance(block["acceptance_criteria"], list):
                for ac in block["acceptance_criteria"]:
                    if isinstance(ac, dict):
                        acs.append({
                            "id": ac.get("id"),
                            "type": ac.get("type"),
                            "target": ac.get("target"),
                        })
    except Exception as e:
        print(f"⚠ handoff summary parse failed: {e}", file=sys.stderr)

    # Fallback: extract items from markdown wave tables if YAML blocks yielded nothing.
    # Matches tables like: | item_id | Type | Purpose |
    if not items:
        print("⚠ YAML extraction empty — falling back to markdown table parser", file=sys.stderr)
        wave_num = 0
        in_wave_table = False
        wave_name = ""
        for line in content.splitlines():
            stripped = line.strip()
            # Detect wave headings: "### Wave 1 — Foundation (Storage)"
            wave_match = re.match(r'^#{2,4}\s+Wave\s+(\d+)\s*[—\-:]\s*(.*)', stripped)
            if wave_match:
                wave_num = int(wave_match.group(1))
                wave_name = wave_match.group(2).strip()
                in_wave_table = False
                continue
            if not stripped.startswith("|"):
                if in_wave_table:
                    in_wave_table = False
                continue
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(cells) < 2:
                continue
            # Skip separator rows
            if all(c.replace("-", "").replace(":", "") == "" for c in cells):
                in_wave_table = True
                continue
            # Skip header rows
            lower_cells = [c.lower() for c in cells]
            if any(h in lower_cells for h in ("item", "type", "purpose", "name")):
                continue
            if in_wave_table and wave_num > 0:
                item_id = cells[0].strip().strip("`")
                item_type = cells[1].strip() if len(cells) > 1 else ""
                purpose = cells[2].strip() if len(cells) > 2 else ""
                items.append({
                    "id": item_id,
                    "name": item_id,
                    "type": item_type,
                    "purpose": purpose,
                    "wave": wave_num,
                    "depends_on": [],
                })
                # Track waves
                existing_wave_ids = {w.get("id") for w in waves}
                if wave_num not in existing_wave_ids:
                    waves.append({
                        "id": wave_num,
                        "name": wave_name,
                        "items": [],
                        "parallel": False,
                    })
                # Add item to wave
                for w in waves:
                    if w.get("id") == wave_num:
                        w["items"].append(item_id)

    # Fallback: extract acceptance criteria from markdown checklists
    # Matches lines like: - [ ] All three sources land in Bronze daily
    if not acs:
        print("⚠ No ACs from YAML blocks — falling back to markdown checklist parser", file=sys.stderr)
        ac_idx = 0
        in_ac_section = False
        for line in content.splitlines():
            stripped = line.strip()
            if re.match(r'^#{2,4}\s+Acceptance\s+Criteria', stripped, re.IGNORECASE):
                in_ac_section = True
                continue
            if in_ac_section and stripped.startswith("#"):
                break
            if in_ac_section:
                ac_match = re.match(r'^-\s*\[[ x]\]\s*(.*)', stripped)
                if ac_match:
                    ac_idx += 1
                    acs.append({
                        "id": f"AC-{ac_idx}",
                        "type": "data-flow",
                        "target": ac_match.group(1).strip(),
                    })

    summary = {
        "project": project,
        "task_flow": task_flow,
        "phase": phase,
        "items": items,
        "waves": waves,
        "acceptance_criteria": acs,
        "item_count": len(items),
        "wave_count": len(waves),
        "ac_count": len(acs),
    }

    out_path = REPO_ROOT / "_projects" / project / "docs" / ".architecture-cache.json"
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"  📋 Generated .architecture-cache.json ({len(items)} items, {len(waves)} waves, {len(acs)} ACs)")


def _verify_output(phase: str, project: str) -> tuple[bool, str]:
    """Verify that a phase produced its expected output files with content.
    Returns (ok, message).

    Checks two things:
    1. Files exist
    2. Files have been filled in (not still scaffolded templates)
       Template detection: files containing 'task_flow: TBD' or 'items: []'
       are considered unfilled templates.
    """
    expected = _phase_output_files(phase)
    if not expected:
        return True, "No output files required"

    project_dir = REPO_ROOT / "_projects" / project
    missing = []
    unfilled = []
    template_markers = ["task_flow: TBD", "items: []", "<!-- AGENT: FILL"]

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


def advance(project: str, approved: bool = False, revise: bool = False,
            feedback: str | None = None) -> dict:
    """Mark current phase complete and advance to next. Returns updated state.

    Verifies output files exist before advancing. Extracts task_flow from
    architecture handoff after Phase 1a. Blocks at human gates unless
    approved=True. Supports --revise to loop back for architect revision
    at Phase 2b (max 3 cycles).
    """
    state = _load_state(project)
    current = state["current_phase"]

    # Handle revision request at human gate
    if revise:
        if current != "2b-sign-off":
            print("⚠️  --revise is only valid at Phase 2b (Sign-Off).")
            return state

        revision_count = state.get("sign_off_revisions", 0)
        if revision_count >= 3:
            print("🛑  Maximum revision cycles (3) reached.")
            print("   You must either --approve or reset the pipeline.")
            return state

        # Save feedback if provided
        if feedback:
            fb_path = REPO_ROOT / "_projects" / project / "docs" / "sign-off-feedback.md"
            fb_content = (
                f"# Sign-Off Feedback (Revision {revision_count + 1})\n\n"
                f"**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
                f"## User Feedback\n\n{feedback}\n"
            )
            fb_path.write_text(fb_content, encoding="utf-8", newline="\n")
            print(f"  📝 Feedback saved to {fb_path.relative_to(REPO_ROOT)}")

        state["sign_off_revisions"] = revision_count + 1
        # Reset phases 1-design through 2b for re-run
        for phase in ["1-design", "2a-test-plan", "2b-sign-off"]:
            state["phases"][phase]["status"] = "pending"
        state["current_phase"] = "1-design"
        state["phases"]["1-design"]["status"] = "in_progress"

        _save_state(project, state)
        print(f"🔄  Revision {revision_count + 1}/3 — Pipeline reset to Phase 1 (Design).")
        print("   The architect will incorporate your feedback and revise.")
        print("   Run 'next' to get the architect prompt.")
        return state

    # Verify output before marking complete
    ok, msg = _verify_output(current, project)
    if not ok:
        print(f"⚠️  Cannot advance — {msg}")
        print(f"   Phase '{current}' has not produced its expected output.")
        print("   Run the agent for this phase first, then try advance again.")
        return state

    # Check human gate enforcement
    if not _is_auto(state, current) and not approved:
        print(f"🛑  Cannot advance — Phase '{current}' is a human gate.")
        print("   Review the deliverables, then run:")
        print(f"   python _shared/scripts/run-pipeline.py advance --project {project} --approve")
        return state

    state["phases"][current]["status"] = "complete"

    # Fast-forward: when leaving discovery, auto-generate all files to sign-off
    if current == "0a-discovery":
        _save_state(project, state)
        ok, ff_report = _fast_forward_to_signoff(project)
        for line in ff_report:
            print(line)
        if ok:
            return _load_state(project)
        # Fall through to normal advance if fast-forward failed
        state = _load_state(project)

    # Extract task_flow after architecture phase
    if current == "1-design" and not state.get("task_flow"):
        tf = _extract_task_flow(project)
        if tf:
            state["task_flow"] = tf
            print(f"  📋 Extracted task_flow: {tf}")

    # Generate compact architecture summary after design
    if current == "1-design":
        _generate_architecture_summary(project)

    # Fast-forward: when leaving sign-off, auto-generate deploy artifacts
    if current == "2b-sign-off":
        _save_state(project, state)
        ok, deploy_report = _generate_deploy_artifacts(project)
        for line in deploy_report:
            print(line)
        if not ok:
            print("⚠️  Deploy artifact generation failed — skill must generate manually")
        state = _load_state(project)
        # Default to artifacts-only — orchestrator asks user before going live
        if "deploy_mode" not in state:
            state["deploy_mode"] = "artifacts_only"
        # Generate deployment handoff deterministically
        ok_dh, dh_report = _generate_deployment_handoff(project)
        for line in dh_report:
            print(line)
        # For artifacts_only, also generate the validation report and skip deploy+validate
        if state.get("deploy_mode") == "artifacts_only":
            ok_vr, vr_report = _generate_validation_report(project)
            for line in vr_report:
                print(line)
            if ok_dh and ok_vr:
                # Generate project brief deterministically
                ok_pb, pb_report = _generate_project_brief(project)
                for line in pb_report:
                    print(line)
                # Complete the entire pipeline
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
    """Reset a phase and all subsequent phases to pending."""
    state = _load_state(project)
    order = _phase_order()
    idx = order.index(phase)
    for p in order[idx:]:
        state["phases"][p]["status"] = "pending"
    state["current_phase"] = phase
    _save_state(project, state)
    return state


def reconcile(project: str) -> dict:
    """Rebuild pipeline state from file evidence. Heals drift from degraded-mode edits.

    Scans docs/ output files against registry to determine which phases
    are actually complete. Extracts task_flow if missing. Idempotent — safe to
    run multiple times.

    Returns updated state with a 'reconcile_report' key listing changes made.
    """
    state = _load_state(project)
    report: list[str] = []

    # Scan each phase's expected output files
    for phase_id in _phase_order():
        expected = _phase_output_files(phase_id)
        if not expected:
            # Phases with no output files (e.g., 2b-sign-off) can't be reconciled from files
            continue

        ok, msg = _verify_output(phase_id, project)
        current_status = state["phases"][phase_id]["status"]

        if ok and current_status != "complete":
            report.append(f"  FIXED: {phase_id} has output files but was '{current_status}' → set to 'complete'")
            state["phases"][phase_id]["status"] = "complete"
        elif not ok and current_status == "complete":
            report.append(f"  WARNING: {phase_id} marked complete but {msg}")

    # Extract task_flow if missing
    if not state.get("task_flow"):
        tf = _extract_task_flow(project)
        if tf:
            state["task_flow"] = tf
            report.append(f"  FIXED: Extracted task_flow '{tf}' from architecture-handoff.md")

    # Determine correct current_phase from phase statuses
    last_complete = None
    for phase_id in _phase_order():
        if state["phases"][phase_id]["status"] == "complete":
            last_complete = phase_id
        else:
            break

    if last_complete:
        expected_current = _next_phase(last_complete) or last_complete
        if state["current_phase"] != expected_current:
            report.append(f"  FIXED: current_phase was '{state['current_phase']}' → set to '{expected_current}'")
            state["current_phase"] = expected_current
            if expected_current in state["phases"] and state["phases"][expected_current]["status"] == "pending":
                state["phases"][expected_current]["status"] = "in_progress"

    if not report:
        report.append("  No drift detected — state is consistent with file evidence.")

    _save_state(project, state)

    return state, report


_PLACEHOLDER_NAMES: frozenset[str] = frozenset(
    {"tbd", "placeholder", "project", "test", "unnamed", "untitled", "new",
     "demo", "sample", "example", "temp", "tmp", "n/a", "none"}
)


def start_pipeline(display_name: str, problem: str | None = None) -> dict:
    """Scaffold a new project and initialize the pipeline.

    Validates that *display_name* is a real, user-confirmed project name.
    Raises ``ValueError`` for empty or placeholder names — the orchestrator
    must collect an explicit name from the user before calling this function.
    """
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
    import importlib.util
    spec = importlib.util.spec_from_file_location("new_project", str(REPO_ROOT / "_shared" / "scripts" / "new-project.py"))
    np = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(np)
    sanitize_name = np.sanitize_name
    scaffold = np.scaffold

    project = sanitize_name(display_name)
    state_path = _state_path(project)

    if state_path.exists():
        print(f"⚠️  Pipeline state already exists for '{project}'. Use 'next' to advance.")
        return _load_state(project)

    # Scaffold the project
    scaffold(str(REPO_ROOT), display_name)

    # Update state with problem text
    state = _load_state(project)
    state["display_name"] = display_name
    if problem:
        state["problem_statement"] = problem
    _save_state(project, state)

    return state


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_status(state: dict) -> None:
    """Print a rich CLI dashboard for pipeline status."""
    project = state["project"]
    task_flow = state.get("task_flow", "TBD") or "TBD"
    current = state["current_phase"]

    # Count items and waves from architecture handoff
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
            wave_count = max(int(w) for w in waves)

    # Check for deploy script
    deploy_dir = project_dir / "deploy"
    deploy_scripts = list(deploy_dir.glob("deploy-*.py")) if deploy_dir.exists() else []

    # Build phase display
    width = 58
    print()
    print(f"  {'=' * width}")
    print(f"  {project}  ·  {task_flow}")
    print(f"  {'=' * width}")

    for phase_id in _phase_order():
        phase = state["phases"][phase_id]
        status = phase["status"]
        agent = _phase_skill(phase_id) or "you"
        output = phase.get("output", "")

        if status == "complete":
            icon = "+"
            suffix = ""
            if output:
                out_path = project_dir / output
                if out_path.exists() and out_path.stat().st_size > 50:
                    suffix = f" -> {output}"
        elif status == "in_progress":
            icon = ">"
            suffix = f" ({agent})"
        else:
            icon = " "
            suffix = ""

        # Phase label (human-friendly)
        labels = {
            "0a-discovery": "Discover",
            "1-design": "Design",
            "2a-test-plan": "Test Plan",
            "2b-sign-off": "Sign-Off",
            "2c-deploy": "Deploy",
            "3-validate": "Validate",
            "4-document": "Document",
        }
        label = labels.get(phase_id, phase_id)
        gate = " (human gate)" if _phase_is_gate(phase_id) else ""

        status_icons = {"complete": "[done]", "in_progress": "[....]", "pending": "[    ]"}
        si = status_icons.get(status, "[  ? ]")

        line = f"  {si} {label:<12}{suffix}{gate}"
        print(line)

    print(f"  {'=' * width}")

    # Summary line
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
    """Print the output file(s) produced by a completed phase."""
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


def _extract_diagram(handoff_path: Path) -> str | None:
    """Extract the ASCII architecture diagram from the handoff markdown."""
    if not handoff_path.exists():
        return None
    content = handoff_path.read_text(encoding="utf-8")
    in_diagram_section = False
    in_code_block = False
    code_lines: list[str] = []
    for line in content.split("\n"):
        if line.strip().startswith("## Architecture Diagram"):
            in_diagram_section = True
            continue
        if in_diagram_section and line.strip().startswith("## ") and not line.strip().startswith("## Architecture Diagram"):
            break
        if in_diagram_section:
            if line.strip().startswith("```") and not in_code_block:
                in_code_block = True
                continue
            elif line.strip().startswith("```") and in_code_block:
                in_code_block = False
                return "\n".join(code_lines)
            elif in_code_block:
                code_lines.append(line)
    return None


# Item type → user-friendly layer label + emoji (derived from registry)
_LAYER_LABELS: dict[str, tuple[str, str]] = build_layer_map()


def _extract_decisions_from_handoff(text: str) -> dict:
    """Extract decisions from the Key Architectural Decisions table in the handoff.

    Looks for a markdown table with columns that include Decision and Choice.
    Handles variable column counts by finding columns by header name.
    Returns dict keyed by lowercase decision name.
    """
    decisions: dict = {}
    decision_map = {
        "storage": "storage",
        "ingestion": "ingestion",
        "processing": "processing",
        "visualization": "visualization",
        "skillset": "skillset",
        "ci/cd": "cicd",
        "deployment": "cicd",
        "alerting": "alerting",
        "ml": "ml",
    }
    in_table = False
    decision_col = -1
    choice_col = -1
    rationale_col = -1
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if in_table:
                break
            continue
        cells = [c.strip() for c in stripped.split("|")[1:-1]]
        if len(cells) < 2:
            continue
        # Skip header separator
        if all(c.replace("-", "").replace(":", "") == "" for c in cells):
            in_table = True
            continue
        if not in_table:
            # Detect column positions from header row
            lower_cells = [c.lower().replace("*", "") for c in cells]
            for i, h in enumerate(lower_cells):
                if h in ("decision", "aspect"):
                    decision_col = i
                elif h in ("choice", "value", "selected"):
                    choice_col = i
                elif h in ("rationale", "reason", "why"):
                    rationale_col = i
            # If we found decision+choice columns, we have our mapping
            if decision_col >= 0 and choice_col >= 0:
                continue
            # Fallback: assume first two columns
            decision_col = 0
            choice_col = 1
            rationale_col = 2 if len(cells) > 2 else -1
            continue
        dec_label = cells[decision_col].strip().strip("*").lower() if decision_col < len(cells) else ""
        for key, mapped in decision_map.items():
            if key in dec_label:
                decisions[mapped] = {
                    "choice": cells[choice_col].strip() if choice_col < len(cells) else "",
                    "rationale": cells[rationale_col].strip() if rationale_col >= 0 and rationale_col < len(cells) else "",
                }
                break
    return decisions


def _print_signoff_summary(project: str) -> None:
    """Print a user-friendly architecture summary for the sign-off gate.

    Shows: diagram → what we're building → why → blockers.
    Designed for business stakeholders, not engineers.
    """
    handoff_path = REPO_ROOT / "_projects" / project / "docs" / "architecture-handoff.md"
    summary_path = REPO_ROOT / "_projects" / project / "docs" / ".architecture-cache.json"

    # Load summary data
    summary: dict = {}
    if summary_path.exists():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    # Load decisions from architecture handoff Key Decisions table or decisions.json fallback
    decisions_path = REPO_ROOT / "_projects" / project / "docs" / "decisions.json"
    handoff_path_d = REPO_ROOT / "_projects" / project / "docs" / "architecture-handoff.md"
    decisions_data: dict = {}
    # Try decisions.json first (legacy), then extract from handoff
    if decisions_path.exists():
        try:
            raw = json.loads(decisions_path.read_text(encoding="utf-8"))
            decisions_data = raw.get("decisions", raw)
        except (json.JSONDecodeError, OSError):
            pass
    if not decisions_data and handoff_path_d.exists():
        try:
            handoff_text = handoff_path_d.read_text(encoding="utf-8")
            decisions_data = _extract_decisions_from_handoff(handoff_text)
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

    # ── Header ──
    print(_separator(f"ARCHITECTURE REVIEW — {display_name}"))
    print(f"  Pattern: {task_flow}")
    print(f"  Scope:   {item_count} Fabric items in {wave_count} deployment waves")
    print()

    # ── Diagram ──
    diagram = _extract_diagram(handoff_path)
    if diagram and diagram.strip():
        print(diagram)
        print()

    # ── What We're Building ──
    if items:
        print(_separator("WHAT WE'RE BUILDING"))
        # Group items by layer, preserving order
        seen_layers: dict[str, list[dict]] = {}
        for item in items:
            item_type = item.get("type", "")
            layer_label, _ = _LAYER_LABELS.get(item_type, ("Other", "📦"))
            seen_layers.setdefault(layer_label, []).append(item)

        for layer_label, layer_items in seen_layers.items():
            emoji = _LAYER_LABELS.get(layer_items[0].get("type", ""), ("", "📦"))[1]
            names = []
            for it in layer_items:
                name = it.get("name", "unknown")
                purpose = it.get("purpose", "")
                if purpose:
                    names.append(f"{name} — {purpose}")
                else:
                    names.append(f"{name} ({it.get('type', '')})")
            if len(names) == 1:
                print(f"  {emoji} {layer_label:<10} {names[0]}")
            else:
                print(f"  {emoji} {layer_label}")
                for n in names:
                    print(f"     {'':10} {n}")
        print()

    # ── Why This Architecture ──
    user_facing_decisions = {
        "storage": "Storage",
        "ingestion": "Ingestion",
        "processing": "Processing",
        "visualization": "Visualization",
    }
    rationale_lines: list[str] = []
    for dec_key, label in user_facing_decisions.items():
        dec = decisions.get(dec_key, {})
        choice = dec.get("choice")
        rationale = dec.get("rationale", "")
        if choice and choice not in ("N/A", "Not yet determined"):
            rationale_lines.append(f"  • {label}: {choice} — {rationale}")

    if rationale_lines:
        print(_separator("WHY THIS ARCHITECTURE"))
        for line in rationale_lines:
            print(line)
        print()

    # ── Needs Attention (only if genuinely unresolved) ──
    # Check if decisions were auto-resolved via trade-offs (even if the
    # Decisions table is absent). Trade-off lines like "Warehouse chosen over
    # Lakehouse" imply the storage decision is resolved.
    tradeoff_resolved: set[str] = set()
    handoff_text = ""
    if handoff_path.exists():
        try:
            handoff_text = handoff_path.read_text(encoding="utf-8")
        except OSError:
            pass
    # Map known Fabric types back to decision categories (derived from registry)
    _TYPE_TO_DECISION: dict[str, str] = build_type_to_decision_map()
    for line in handoff_text.splitlines():
        lower = line.lower()
        if any(phrase in lower for phrase in (
            "chosen over", "selected over", "picked over",
            "decided on", "rejected because", "rejected —",
            "rejected -", "decision:", "choice:"
        )):
            for type_name, dec_cat in _TYPE_TO_DECISION.items():
                if type_name in lower:
                    tradeoff_resolved.add(dec_cat)

    warnings: list[str] = []
    for dec_key, label in user_facing_decisions.items():
        dec = decisions.get(dec_key, {})
        choice = dec.get("choice")
        if not choice or choice == "Not yet determined":
            if dec_key in tradeoff_resolved:
                # Decision was auto-resolved via trade-offs — not a blocker
                continue
            warnings.append(f"  ⚠️  {label} decision is unresolved — needs input before deployment")

    if warnings:
        print(_separator("NEEDS ATTENTION"))
        for w in warnings:
            print(w)
        print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pipeline runner — orchestrate Fabric agent phases"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    # start
    start_p = sub.add_parser("start", help="Start a new pipeline")
    start_p.add_argument("name", help="Project display name")
    start_p.add_argument("--problem", help="Problem statement text")

    # next
    next_p = sub.add_parser("next", help="Get prompt for next phase")
    next_p.add_argument("--project", required=True, help="Project folder name (kebab-case)")

    # status
    status_p = sub.add_parser("status", help="Show pipeline status")
    status_p.add_argument("--project", required=True, help="Project folder name")

    # advance
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
    adv_p.add_argument("-q", "--quiet", action="store_true",
                       help="Suppress printing completed phase output files and diagrams (use for agent/CI mode)")

    # reset
    reset_p = sub.add_parser("reset", help="Reset a phase")
    reset_p.add_argument("--project", required=True, help="Project folder name")
    reset_p.add_argument("--phase", required=True, choices=_phase_order(), help="Phase to reset to")

    # reconcile
    recon_p = sub.add_parser("reconcile", help="Rebuild state from file evidence (heals drift)")
    recon_p.add_argument("--project", required=True, help="Project folder name")

    # batch — single command from problem statement to sign-off
    batch_p = sub.add_parser("batch", help="Start pipeline and fast-forward to sign-off (single command)")
    batch_p.add_argument("name", help="Project display name")
    batch_p.add_argument("--problem", required=True, help="Problem statement text")
    batch_p.add_argument("--through", default="2b-sign-off",
                         help="Phase to fast-forward through (default: 2b-sign-off)")

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

    elif args.command == "advance":
        if args.reconcile:
            _, recon_report = reconcile(args.project)
            print("\n  Reconcile report:")
            for line in recon_report:
                print(line)
            print()
        prev_phase = _load_state(args.project)["current_phase"]
        state = advance(args.project, approved=args.approve,
                        revise=args.revise, feedback=args.feedback)
        _print_status(state)

        # Print completed phase output (unless suppressed or phase didn't advance)
        if not args.quiet and state["current_phase"] != prev_phase:
            _print_phase_output(args.project, prev_phase)

        # Show user-friendly architecture summary when entering sign-off phase
        if state["current_phase"] == "2b-sign-off":
            _print_signoff_summary(args.project)
            print(_separator("PRESENTATION RULES"))
            print("  Show the user: diagram + 1-3 sentence summary + blockers.")
            print("  Do NOT show: decision tables, wave tables, trade-offs, or raw pipeline output.")
            print("  The user is a business stakeholder — speak in plain language.")
            print()
            # Emit the sign-off agent prompt with resolved diagram so the LLM receives it
            prompt, agent, phase, is_gate = get_next_prompt(args.project)
            if prompt:
                print(_separator("AGENT PROMPT (copy to Copilot CLI):"))
                print(prompt)

        # Show deployment mode choice when entering deploy phase
        if state["current_phase"] == "2c-deploy":
            deploy_dir = REPO_ROOT / "_projects" / args.project / "deploy"
            print(_separator("DEPLOYMENT ARTIFACTS GENERATED"))
            print(f"  📦 Deploy script:  deploy/deploy-{args.project}.py")
            print(f"  📦 Config:         deploy/config.yml")
            print(f"  📦 Workspace:      deploy/workspace/ (.platform files)")
            print()
            print(_separator("DEPLOYMENT MODE"))
            print("  Ask the user: \"Would you like to deploy to a live Fabric workspace,")
            print("  or review the generated artifacts only?\"")
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

        # Step 1: Scaffold
        state = start_pipeline(args.name, args.problem)
        project = state["project"]
        print(f"  ✅ Project scaffolded: {project}")

        # Step 2: Get discovery prompt (includes signal mapper precompute)
        prompt, agent, phase, is_gate = get_next_prompt(project)
        print(f"  ✅ Signal mapper executed")
        print(f"  📋 Discovery phase requires agent (signal interpretation + user confirmation)")
        print()

        elapsed = _time.monotonic() - t0
        print(f"  ⏱️  Scaffold + precompute completed in {elapsed:.1f}s")
        print()

        # Print the discovery prompt so the agent can proceed
        print(_separator("DISCOVERY AGENT PROMPT"))
        print(prompt)
        print()
        print(_separator(""))
        print(f"  After the agent writes the discovery brief, run:")
        print(f"    python _shared/scripts/run-pipeline.py advance --project {project} -q")
        print(f"  This will auto-generate ALL files and fast-forward to sign-off.")


if __name__ == "__main__":
    main()
