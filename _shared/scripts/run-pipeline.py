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
    python _shared/scripts/run-pipeline.py reset --project my-project --phase 1b-review

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
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = REPO_ROOT / ".github" / "skills"
VERSION = "1.0.0"

sys.path.insert(0, str(REPO_ROOT / "_shared" / "lib"))
from banner import print_banner

# Phase ordering (linear)
PHASE_ORDER = [
    "0a-discovery",
    "1a-design",
    "1b-review",
    "1c-finalize",
    "2a-test-plan",
    "2b-sign-off",
    "2c-deploy",
    "3-validate",
    "4-document",
]

# Skill mapping — each phase delegates to a skill (except human gate)
PHASE_SKILLS = {
    "0a-discovery":  "fabric-discover",
    "1a-design":     "fabric-design",
    "1b-review":     "fabric-design",      # Architect reviews their own DRAFT
    "1c-finalize":   "fabric-design",      # Architect finalizes after review
    "2a-test-plan":  "fabric-test",
    "2b-sign-off":   None,                 # human gate
    "2c-deploy":     "fabric-deploy",
    "3-validate":    "fabric-test",        # QA validates after deployment
    "4-document":    "fabric-document",
}

# Pre-compute scripts to run before each agent phase
PHASE_PRECOMPUTE: dict[str, list[list[str]]] = {
    "0a-discovery": [
        # signal-mapper pre-processes user text → draft signal table
        # Args filled dynamically: ["python", ".github/skills/fabric-discover/scripts/signal-mapper.py", "--text", problem_text]
    ],
    "1a-design": [
        # decision-resolver + handoff-scaffolder run after architect selects task flow
        # These are invoked dynamically when task_flow is known
        # Located in .github/skills/fabric-design/scripts/
    ],
    "1b-review": [
        # review-prescan does mechanical checks before LLM review
        # ["python", ".github/skills/fabric-design/scripts/review-prescan.py", "--handoff", handoff_path]
    ],
    "2a-test-plan": [
        # test-plan-prefill maps ACs to validation phases
        # ["python", ".github/skills/fabric-test/scripts/test-plan-prefill.py", "--handoff", handoff_path]
    ],
    "2c-deploy": [
        # deploy-script-gen produces the deploy script
        # ["python", ".github/skills/fabric-deploy/scripts/deploy-script-gen.py", "--handoff", handoff_path, ...]
    ],
}


# Expected output files per phase (for verification guards)
PHASE_OUTPUT_FILES: dict[str, list[str]] = {
    "0a-discovery":  ["prd/discovery-brief.md"],
    "1a-design":     ["prd/architecture-handoff.md", "docs/decisions/001-task-flow.md"],
    "1b-review":     ["prd/engineer-review.md", "prd/tester-review.md"],
    "1c-finalize":   ["prd/architecture-handoff.md"],  # updated in-place
    "2a-test-plan":  ["prd/test-plan.md"],
    "2b-sign-off":   [],  # human gate — no file output
    "2c-deploy":     ["prd/deployment-handoff.md", "prd/phase-progress.md"],
    "3-validate":    ["prd/validation-report.md"],
    "4-document":    ["docs/README.md"],
}

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
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def _next_phase(current: str) -> str | None:
    idx = PHASE_ORDER.index(current)
    if idx + 1 < len(PHASE_ORDER):
        return PHASE_ORDER[idx + 1]
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
            f"3. Write the Discovery Brief to {pp}/prd/discovery-brief.md\n\n"
            f"⚠️ Do NOT modify {pp}/pipeline-state.json — the pipeline runner manages state transitions."
        ),

        "1a-design": (
            f"Use the /fabric-design skill. Read the skill at .github/skills/fabric-design/SKILL.md for instructions.\n\n"
            f"Project: {display_name} (folder: {pp})\n"
            f"Read the Discovery Brief from {pp}/prd/discovery-brief.md.\n\n"
            f"1. Read decisions/_index.md to find decision guides\n"
            f"2. Read diagrams/_index.md to find the matching diagram\n"
            f"3. Select the best-fit task flow and walk through decisions\n"
            f"4. Write the DRAFT Architecture Handoff to {pp}/prd/architecture-handoff.md\n"
            f"   - Include `task-flow: <id>` in the YAML frontmatter so the pipeline runner can extract it\n\n"
            f"⚠️ Do NOT modify {pp}/pipeline-state.json — the pipeline runner manages state transitions."
        ),

        "1b-review": (
            f"Use the /fabric-design skill (Mode 2: Review). Read the skill at .github/skills/fabric-design/SKILL.md for instructions.\n\n"
            f"Project: {display_name} (folder: {pp})\n"
            f"Task flow: {task_flow}\n\n"
            f"1. Read the DRAFT Architecture Handoff from {pp}/prd/architecture-handoff.md\n"
            f"2. Read the matching diagram from diagrams/{task_flow}.md\n"
            f"3. Read registry/item-type-registry.json for REST API creation support\n"
            f"4. Read the validation checklist from _shared/registry/validation-checklists.json (task flow: {task_flow})\n"
            f"5. Produce BOTH reviews:\n"
            f"   - Engineer review → edit {pp}/prd/engineer-review.md\n"
            f"   - Tester review → edit {pp}/prd/tester-review.md\n"
            f"6. Set review_outcome in each review:\n"
            f"   - If red-severity findings exist → review_outcome: revise\n"
            f"   - If no red findings → review_outcome: approved\n"
            f"   - Track review_iteration (check existing file for previous iteration)\n\n"
            f"⚠️ Do NOT modify {pp}/pipeline-state.json — the pipeline runner manages state transitions."
        ),

        "1c-finalize": (
            f"Use the /fabric-design skill (Mode 3: Finalize). Read the skill at .github/skills/fabric-design/SKILL.md for instructions.\n\n"
            f"Project: {display_name} (folder: {pp})\n"
            f"Task flow: {task_flow}\n\n"
            + (
                f"🔄 **SIGN-OFF REVISION {state.get('sign_off_revisions', 0)}/3** — The user requested changes at sign-off.\n"
                f"Read their feedback from {pp}/prd/sign-off-feedback.md before revising.\n\n"
                if state.get("sign_off_revisions", 0) > 0 else ""
            )
            + f"1. Read the engineer review from {pp}/prd/engineer-review.md\n"
            f"2. Read the tester review from {pp}/prd/tester-review.md\n"
            f"3. Incorporate feedback into the Architecture Handoff at {pp}/prd/architecture-handoff.md\n"
            f"4. Change status from DRAFT to FINAL. Populate the Design Review table.\n\n"
            f"⚠️ Do NOT modify {pp}/pipeline-state.json — the pipeline runner manages state transitions."
        ),

        "2a-test-plan": (
            f"Use the /fabric-test skill (Mode 1: Test Plan). Read the skill at .github/skills/fabric-test/SKILL.md for instructions.\n\n"
            f"Project: {display_name} (folder: {pp})\n"
            f"Task flow: {task_flow}\n\n"
            f"1. Read the FINAL Architecture Handoff from {pp}/prd/architecture-handoff.md\n"
            f"2. Read the validation checklist from _shared/registry/validation-checklists.json (task flow: {task_flow})\n"
            f"3. Map each acceptance criterion to a concrete validation check\n"
            f"4. Write the Test Plan to {pp}/prd/test-plan.md\n"
            f"5. 🛑 HUMAN GATE: Present a consolidated sign-off summary and WAIT for user approval. This is the ONLY stop in the pipeline.\n\n"
            f"⚠️ Do NOT modify {pp}/pipeline-state.json — the pipeline runner manages state transitions."
        ),

        "2b-sign-off": (
            f"🛑 HUMAN GATE — Phase 2b Sign-Off"
            + (f" (Revision {state.get('sign_off_revisions', 0)}/3)" if state.get('sign_off_revisions', 0) > 0 else "")
            + f"\n\n"
            f"Review both documents before approving:\n"
            f"  - FINAL Architecture Handoff: {pp}/prd/architecture-handoff.md\n"
            f"  - Test Plan: {pp}/prd/test-plan.md\n\n"
            f"Options:\n"
            f"  • Say 'approved' or 'go ahead' to continue to deployment\n"
            f"  • Say 'revise' with your feedback to send back to the architect (max 3 cycles)\n\n"
            f"## Architecture Diagram\n\n"
            f"{{{{DIAGRAM_PLACEHOLDER}}}}"
        ),

        "2c-deploy": (
            f"Use the /fabric-deploy skill. Read the skill at .github/skills/fabric-deploy/SKILL.md for instructions.\n\n"
            f"Project: {display_name} (folder: {pp})\n"
            f"Task flow: {task_flow}\n\n"
            f"1. Read {pp}/prd/architecture-summary.json for compact items/waves/ACs (faster than full handoff)\n"
            f"   - If not present, fall back to {pp}/prd/architecture-handoff.md\n"
            f"2. Read the Test Plan from {pp}/prd/test-plan.md\n"
            f"3. Read _shared/learnings.md for known Fabric CLI gotchas\n"
            f"4. Check {pp}/prd/phase-progress.md — if resume_from is set, continue from there\n"
            f"5. Deploy items by dependency wave following the handoff's deployment order\n"
            f"6. Update {pp}/prd/phase-progress.md after each item (status: completed or failed)\n"
            f"7. Write the Deployment Handoff to {pp}/prd/deployment-handoff.md\n"
            f"8. Append any new operational learnings to _shared/learnings.md\n\n"
            f"⚠️ Do NOT modify {pp}/pipeline-state.json — the pipeline runner manages state transitions."
        ),

        "3-validate": (
            f"Use the /fabric-test skill (Mode 2: Validate). Read the skill at .github/skills/fabric-test/SKILL.md for instructions.\n\n"
            f"Project: {display_name} (folder: {pp})\n"
            f"Task flow: {task_flow}\n\n"
            f"1. Read the Deployment Handoff from {pp}/prd/deployment-handoff.md\n"
            f"2. Read {pp}/prd/architecture-summary.json for item/AC reference (faster than full handoff)\n"
            f"3. Read the validation checklist from _shared/registry/validation-checklists.json (task flow: {task_flow})\n"
            f"4. Read _shared/learnings.md for known validation gotchas\n"
            f"5. Check {pp}/prd/remediation-log.md — if it exists and has resolved items, only re-validate those\n"
            f"6. Validate deployment against the checklist and test plan\n"
            f"7. Write the Validation Report to {pp}/prd/validation-report.md\n"
            f"8. If issues found: categorize and write to {pp}/prd/remediation-log.md\n"
            f"   - deployment/configuration/transient issues → route to engineer (use /fabric-deploy skill Mode 2: Remediate)\n"
            f"   - design issues → escalate (pipeline pauses)\n"
            f"   - Max 3 remediation iterations before escalating to user\n"
            f"9. Append any new operational learnings to _shared/learnings.md\n\n"
            f"⚠️ Do NOT modify {pp}/pipeline-state.json — the pipeline runner manages state transitions."
        ),

        "4-document": (
            f"Use the /fabric-document skill. Read the skill at .github/skills/fabric-document/SKILL.md for instructions.\n\n"
            f"Project: {display_name} (folder: {pp})\n"
            f"Task flow: {task_flow}\n\n"
            f"1. Read {pp}/prd/architecture-summary.json for compact item/wave/AC data\n"
            f"2. Read remaining handoffs: discovery-brief, deployment-handoff, validation-report\n"
            f"   - Only read the full architecture-handoff.md if the summary lacks needed detail (decisions, diagram)\n"
            f"3. Generate wiki documentation in {pp}/docs/\n"
            f"4. Write ADRs for each major decision\n"
            f"5. Update PROJECTS.md — Phase = 'Complete'\n\n"
            f"⚠️ Do NOT modify {pp}/pipeline-state.json — the pipeline runner manages state transitions."
        ),
    }

    return prompts.get(phase, f"Unknown phase: {phase}")


# ---------------------------------------------------------------------------
# Pre-compute execution
# ---------------------------------------------------------------------------

def _run_precompute(phase: str, project: str, state: dict) -> list[str]:
    """Run deterministic pre-compute scripts for a phase. Returns output lines."""
    pp = _project_path(project)
    handoff_path = str(REPO_ROOT / pp / "prd" / "architecture-handoff.md")
    task_flow = state.get("task_flow")
    outputs: list[str] = []

    if phase == "0a-discovery" and state.get("problem_statement"):
        # Run signal mapper
        cmd = [sys.executable, str(SKILLS_DIR / "fabric-discover" / "scripts" / "signal-mapper.py"),
               "--text", state["problem_statement"], "--format", "json"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                outputs.append(f"Signal mapper output:\n{result.stdout}")
            else:
                outputs.append(f"Signal mapper warning: {result.stderr.strip()}")
        except Exception as e:
            outputs.append(f"Signal mapper skipped: {e}")

    elif phase == "1b-review" and os.path.exists(handoff_path):
        # Run review prescan
        cmd = [sys.executable, str(SKILLS_DIR / "fabric-design" / "scripts" / "review-prescan.py"),
               "--handoff", handoff_path]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                outputs.append(f"Review prescan output:\n{result.stdout}")
        except Exception as e:
            outputs.append(f"Review prescan skipped: {e}")

    elif phase == "2a-test-plan" and os.path.exists(handoff_path):
        # Run test plan prefill
        cmd = [sys.executable, str(SKILLS_DIR / "fabric-test" / "scripts" / "test-plan-prefill.py"),
               "--handoff", handoff_path]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                outputs.append(f"Test plan prefill output:\n{result.stdout}")
        except Exception as e:
            outputs.append(f"Test plan prefill skipped: {e}")

    return outputs


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
    current_idx = PHASE_ORDER.index(current)
    current_status = state["phases"][current]["status"]

    if current_status == "complete":
        next_phase = _next_phase(current)
        if next_phase is None:
            return ("Pipeline complete.", None, "complete", False)
        phase = next_phase
    else:
        phase = current

    agent = PHASE_SKILLS.get(phase)
    prompt = _prompt_for_phase(phase, project, state)
    is_gate = not _is_auto(state, phase)

    # Include precompute output if available
    precompute_output = _run_precompute(phase, project, state)
    if precompute_output:
        prompt += "\n\n## Pre-computed Data\n\n" + "\n\n".join(precompute_output)

    # Generate architecture diagram for sign-off phase
    if phase == "2b-sign-off" and "{{DIAGRAM_PLACEHOLDER}}" in prompt:
        pp = _project_path(project)
        handoff_path = str(REPO_ROOT / pp / "prd" / "architecture-handoff.md")
        if os.path.exists(handoff_path):
            try:
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                cmd = [sys.executable, str(SKILLS_DIR / "fabric-design" / "scripts" / "diagram-gen.py"),
                       "--handoff", handoff_path]
                result = subprocess.run(cmd, capture_output=True, text=True,
                                        timeout=30, encoding="utf-8", env=env)
                if result.returncode == 0 and result.stdout.strip():
                    prompt = prompt.replace("{{DIAGRAM_PLACEHOLDER}}", result.stdout.strip())
                else:
                    prompt = prompt.replace("{{DIAGRAM_PLACEHOLDER}}",
                                            "(Diagram generation failed — review handoff directly)")
            except Exception:
                prompt = prompt.replace("{{DIAGRAM_PLACEHOLDER}}",
                                        "(Diagram generation unavailable — review handoff directly)")
        else:
            prompt = prompt.replace("{{DIAGRAM_PLACEHOLDER}}",
                                    "(Architecture handoff not found)")

    return (prompt, agent, phase, is_gate)


def _extract_task_flow(project: str) -> str | None:
    """Extract task_flow from architecture-handoff.md YAML frontmatter or content."""
    handoff = REPO_ROOT / "_projects" / project / "prd" / "architecture-handoff.md"
    if not handoff.exists():
        return None
    content = handoff.read_text(encoding="utf-8")
    # Try YAML frontmatter: task-flow: medallion or task_flow: medallion
    match = re.search(r'(?:task[-_]flow|taskflow)\s*:\s*(\S+)', content, re.IGNORECASE)
    if match:
        return match.group(1).strip().strip('"').strip("'")
    # Fallback: look for "Task Flow: medallion" in body
    match = re.search(r'Task\s+Flow\s*:\s*`?(\S+?)`?(?:\s|$)', content)
    if match:
        return match.group(1).strip()
    return None


def _generate_architecture_summary(project: str) -> None:
    """Extract a compact architecture-summary.json from the FINAL handoff.

    Downstream phases (deploy, test, validate, document) can load this ~30-line
    JSON instead of parsing the 300+ line markdown handoff. Saves significant
    agent context when the handoff is read multiple times across phases.

    Output: _projects/{project}/prd/architecture-summary.json
    """
    handoff_path = REPO_ROOT / "_projects" / project / "prd" / "architecture-handoff.md"
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
        sys.path.insert(0, str(REPO_ROOT / "_shared" / "lib"))
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
    except Exception:
        pass  # Fall back to empty — summary is a convenience, not a blocker

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

    out_path = REPO_ROOT / "_projects" / project / "prd" / "architecture-summary.json"
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  📋 Generated architecture-summary.json ({len(items)} items, {len(waves)} waves, {len(acs)} ACs)")


def _verify_output(phase: str, project: str) -> tuple[bool, str]:
    """Verify that a phase produced its expected output files with content.
    Returns (ok, message).

    Checks two things:
    1. Files exist
    2. Files have been filled in (not still scaffolded templates)
       Template detection: files containing 'task_flow: TBD' or 'items: []'
       are considered unfilled templates.
    """
    expected = PHASE_OUTPUT_FILES.get(phase, [])
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
            fb_path = REPO_ROOT / "_projects" / project / "prd" / "sign-off-feedback.md"
            fb_content = (
                f"# Sign-Off Feedback (Revision {revision_count + 1})\n\n"
                f"**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
                f"## User Feedback\n\n{feedback}\n"
            )
            fb_path.write_text(fb_content, encoding="utf-8")
            print(f"  📝 Feedback saved to {fb_path.relative_to(REPO_ROOT)}")

        state["sign_off_revisions"] = revision_count + 1
        # Reset phases 1c through 2b for re-run
        for phase in ["1c-finalize", "2a-test-plan", "2b-sign-off"]:
            state["phases"][phase]["status"] = "pending"
        state["current_phase"] = "1c-finalize"
        state["phases"]["1c-finalize"]["status"] = "in_progress"

        _save_state(project, state)
        print(f"🔄  Revision {revision_count + 1}/3 — Pipeline reset to Phase 1c (Finalize).")
        print(f"   The architect will incorporate your feedback and re-finalize.")
        print(f"   Run 'next' to get the architect prompt.")
        return state

    # Verify output before marking complete
    ok, msg = _verify_output(current, project)
    if not ok:
        print(f"⚠️  Cannot advance — {msg}")
        print(f"   Phase '{current}' has not produced its expected output.")
        print(f"   Run the agent for this phase first, then try advance again.")
        return state

    # Check human gate enforcement
    if not _is_auto(state, current) and not approved:
        print(f"🛑  Cannot advance — Phase '{current}' is a human gate.")
        print(f"   Review the deliverables, then run:")
        print(f"   python _shared/scripts/run-pipeline.py advance --project {project} --approve")
        return state

    state["phases"][current]["status"] = "complete"

    # Extract task_flow after architecture phase
    if current == "1a-design" and not state.get("task_flow"):
        tf = _extract_task_flow(project)
        if tf:
            state["task_flow"] = tf
            print(f"  📋 Extracted task_flow: {tf}")

    # Generate compact architecture summary after finalize
    if current == "1c-finalize":
        _generate_architecture_summary(project)

    next_phase = _next_phase(current)
    if next_phase:
        state["current_phase"] = next_phase
        state["phases"][next_phase]["status"] = "in_progress"

    _save_state(project, state)
    return state


def reset_phase(project: str, phase: str) -> dict:
    """Reset a phase and all subsequent phases to pending."""
    state = _load_state(project)
    idx = PHASE_ORDER.index(phase)
    for p in PHASE_ORDER[idx:]:
        state["phases"][p]["status"] = "pending"
    state["current_phase"] = phase
    _save_state(project, state)
    return state


def reconcile(project: str) -> dict:
    """Rebuild pipeline state from file evidence. Heals drift from degraded-mode edits.

    Scans prd/ output files against PHASE_OUTPUT_FILES to determine which phases
    are actually complete. Extracts task_flow if missing. Idempotent — safe to
    run multiple times.

    Returns updated state with a 'reconcile_report' key listing changes made.
    """
    state = _load_state(project)
    report: list[str] = []

    # Scan each phase's expected output files
    for phase_id in PHASE_ORDER:
        expected = PHASE_OUTPUT_FILES.get(phase_id, [])
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
    for phase_id in PHASE_ORDER:
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


def start_pipeline(display_name: str, problem: str | None = None) -> dict:
    """Scaffold a new project and initialize the pipeline."""
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
    """Print a human-readable pipeline status."""
    print(f"\n  Pipeline Status: {state['project']}")
    print(f"  Task Flow: {state.get('task_flow', 'TBD')}")
    print(f"  Current Phase: {state['current_phase']}")
    print()

    for phase_id in PHASE_ORDER:
        phase = state["phases"][phase_id]
        status = phase["status"]
        agent = PHASE_SKILLS.get(phase_id, "—")
        is_current = "→" if phase_id == state["current_phase"] else " "
        gate = " 🛑" if phase.get("gate") == "human" else ""

        icon = {"pending": "⬜", "in_progress": "🔄", "complete": "✅"}.get(status, "❓")
        print(f"  {is_current} {icon} {phase_id:<16} {agent or '(user)':<20} {status}{gate}")

    print()


def _print_phase_output(project: str, completed_phase: str) -> None:
    """Print the output file(s) produced by a completed phase."""
    expected = PHASE_OUTPUT_FILES.get(completed_phase, [])
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
        print(f"\n{'─' * 68}")
        print(f"  {label}")
        print(f"{'─' * 68}\n")
        print(content.rstrip())
        print()


def _print_signoff_diagram(project: str) -> None:
    """Extract and display the architecture diagram from the handoff at sign-off."""
    handoff_path = REPO_ROOT / "_projects" / project / "prd" / "architecture-handoff.md"
    if not handoff_path.exists():
        return

    content = handoff_path.read_text(encoding="utf-8")

    # Extract the ## Architecture Diagram section from the handoff markdown
    diagram_text = None
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
                diagram_text = "\n".join(code_lines)
                break
            elif in_code_block:
                code_lines.append(line)

    if diagram_text and diagram_text.strip():
        print(f"\n{'─' * 68}")
        print(f"  ARCHITECTURE DIAGRAM")
        print(f"{'─' * 68}\n")
        print(diagram_text)
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
                       help="Feedback text for --revise (saved to prd/sign-off-feedback.md)")
    adv_p.add_argument("--reconcile", action="store_true",
                       help="Run reconcile before advancing to heal any state drift")
    adv_p.add_argument("-q", "--quiet", action="store_true",
                       help="Suppress printing completed phase output files and diagrams (use for agent/CI mode)")

    # reset
    reset_p = sub.add_parser("reset", help="Reset a phase")
    reset_p.add_argument("--project", required=True, help="Project folder name")
    reset_p.add_argument("--phase", required=True, choices=PHASE_ORDER, help="Phase to reset to")

    # reconcile
    recon_p = sub.add_parser("reconcile", help="Rebuild state from file evidence (heals drift)")
    recon_p.add_argument("--project", required=True, help="Project folder name")

    args = parser.parse_args()

    if args.command == "start":
        print_banner()
        state = start_pipeline(args.name, args.problem)
        _print_status(state)
        prompt, agent, phase, is_gate = get_next_prompt(state["project"])
        print(f"\n  Next agent: {agent}")
        print(f"  Phase: {phase}")
        if is_gate:
            print(f"  ⚠️  This phase is a human gate — review deliverables before advancing")
        print(f"\n{'─' * 68}")
        print(f"  AGENT PROMPT (copy to Copilot CLI):")
        print(f"{'─' * 68}\n")
        print(prompt)

    elif args.command == "next":
        prompt, agent, phase, is_gate = get_next_prompt(args.project)
        if agent is None and phase == "complete":
            print("✅ Pipeline complete.")
            return
        print(f"\n  Next agent: {agent or '(human gate)'}")
        print(f"  Phase: {phase}")
        print(f"  Auto-chain: {'🛑 No (human gate — use --approve)' if is_gate else '🟢 Yes'}")
        print(f"\n{'─' * 68}")
        print(f"  AGENT PROMPT:")
        print(f"{'─' * 68}\n")
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

        # Show architecture diagram when entering sign-off phase
        if not args.quiet and state["current_phase"] == "2b-sign-off":
            _print_signoff_diagram(args.project)

        prompt, agent, phase, is_gate = get_next_prompt(args.project)
        if agent:
            chain_label = "🛑 HUMAN GATE — use --approve" if is_gate else "🟢 AUTO-CHAIN"
            print(f"  {chain_label} → {agent or '(user)'} ({phase})")

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


if __name__ == "__main__":
    main()
