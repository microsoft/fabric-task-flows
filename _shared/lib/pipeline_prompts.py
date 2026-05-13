from __future__ import annotations

import re
from pathlib import Path

from pipeline_state import (
    _is_auto,
    _load_state,
    _next_phase,
    _phase_is_gate,
    _phase_skill,
    _repo_root,
    _runtime_callable,
)



def _project_path(project: str) -> str:
    return f"projects/{project}"



def _prompt_for_phase(phase: str, project: str, state: dict) -> str:
    pp = _project_path(project)
    task_flow = state.get("task_flow") or "TBD"
    display_name = state.get("display_name", project)

    prompts = {
        "0a-discovery": (
            f"Use the /fabric-discover skill.\n\n"
            f"Project: {display_name} (folder: {pp})\n"
            f"Problem statement from user: {state.get('problem_statement', '(see conversation history)')}\n\n"
            f"The project is already scaffolded at {pp}/. Edit the pre-existing files — do NOT create new ones.\n\n"
            f"1. Infer architectural signals from the problem statement\n"
            f"2. Present inferences to confirm (the user has already described the problem — infer what you can)\n"
            f"3. Write the Discovery Brief to {pp}/docs/discovery-brief.md\n\n"
            f"⚠️ Do NOT modify {pp}/pipeline-state.json — the pipeline runner manages state transitions."
        ),
        "1-design": (
            f"Use the /fabric-design skill.\n\n"
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
            f"   - Include `task-flow: <id>` in the YAML frontmatter so the pipeline runner can extract it\n"
        ),
        "2a-test-plan": (
            f"Use the /fabric-test skill (Mode 1: Architecture Review + Test Plan).\n\n"
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
            f"Do NOT present a sign-off summary or wait for user approval — the pipeline auto-advances to Phase 2b (Sign-Off) where the user reviews both the architecture handoff and test plan."
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
            f"Use the /fabric-deploy skill.\n\n"
            f"Project: {display_name} (folder: {pp})\n"
            f"Task flow: {task_flow}\n"
            f"Deploy mode: {state.get('deploy_mode', 'artifacts_only')}\n\n"
            + (
                f"The user chose LIVE deployment. Present the deploy script and guide them:\n\n"
                f"1. The deploy script is at {pp}/deploy/deploy-{pp.split('/')[-1]}.py\n"
                f"2. It handles workspace creation, capacity assignment, and fabric-cicd deployment\n"
                f"3. The user must run it — it requires Azure credentials (az login)\n"
                f"4. After the user confirms deployment is complete, write:\n"
                f"   - {pp}/docs/deployment-handoff.md (items with status: deployed)\n"
                f"   - {pp}/docs/phase-progress.md (all waves completed)\n"
                if state.get("deploy_mode") == "live" else
                f"Deploy mode is ARTIFACTS ONLY — no live workspace deployment.\n\n"
                f"1. Review the generated artifacts in {pp}/deploy/:\n"
                f"   - deploy script, config.yml, workspace/.platform files, taskflow JSON\n"
                f"2. Present a summary of what would be deployed (items, waves, script location)\n"
                f"3. Write {pp}/docs/deployment-handoff.md with:\n"
                f"   - deployment_mode: artifacts_only\n"
                f"   - All items with status: planned (not deployed)\n"
                f"4. Write {pp}/docs/phase-progress.md with all items status: planned\n"
            )
        ),
        "3-validate": (
            f"Use the /fabric-test skill (Mode 2: Validate).\n\n"
            f"Project: {display_name} (folder: {pp})\n"
            f"Task flow: {task_flow}\n"
            f"Deploy mode: {state.get('deploy_mode', 'artifacts_only')}\n\n"
            + (
                f"Items were deployed to a live workspace. Validate:\n\n"
                f"1. Run validate-items.py to generate config checklist:\n"
                f"   python .github/skills/fabric-test/scripts/validate-items.py {pp}/docs/deployment-handoff.md\n"
                f"2. For each config step, verify in Fabric Portal and mark confirmed\n"
                f"3. Run smoke tests (query data, trigger pipeline, render report)\n"
                f"4. Write the Validation Report to {pp}/docs/validation-report.md\n"
                f"   - status: passed (all config confirmed + smoke tests pass)\n"
                f"   - status: failed (critical config issues)\n"
                if state.get("deploy_mode") == "live" else
                f"No live workspace — structural validation only.\n\n"
                f"1. Verify all deployment artifacts exist in {pp}/deploy/\n"
                f"2. Verify deployment-handoff.md lists all architecture items\n"
                f"3. Write the Validation Report to {pp}/docs/validation-report.md with:\n"
                f"   - status: passed (structural — all artifacts verified)\n"
                f"   - validation_mode: structural\n"
                f"   - Note: live validation deferred until workspace deployment\n"
            )
        ),
        "4-document": (
            f"Use the /fabric-document skill.\n\n"
            f"Project: {display_name} (folder: {pp})\n"
            f"Task flow: {task_flow}\n"
            f"Deploy mode: {state.get('deploy_mode', 'artifacts_only')}\n\n"
            f"1. Read all pipeline handoffs from {pp}/docs/:\n"
            f"   - discovery-brief.md, architecture-handoff.md, deployment-handoff.md, test-plan.md, validation-report.md\n"
            f"2. Synthesize into ONE file: {pp}/docs/project-brief.md\n"
            f"3. Do NOT create separate README.md, architecture.md, deployment-log.md, or decisions/*.md files"
            + (f"\n4. In the 'How to Deploy' section, note that artifacts are ready but deployment is pending"
               if state.get("deploy_mode") != "live" else "")
        ),
    }

    return prompts.get(phase, f"Unknown phase: {phase}")



def _extract_diagram(handoff_path: Path) -> str | None:
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
            if line.strip().startswith("```") and in_code_block:
                return "\n".join(code_lines)
            if in_code_block:
                code_lines.append(line)
    return None



def _extract_decisions_from_handoff(text: str) -> dict:
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
        cells = [cell.strip() for cell in stripped.split("|")[1:-1]]
        if len(cells) < 2:
            continue
        if all(cell.replace("-", "").replace(":", "") == "" for cell in cells):
            in_table = True
            continue
        if not in_table:
            lower_cells = [cell.lower().replace("*", "") for cell in cells]
            for idx, header in enumerate(lower_cells):
                if header in ("decision", "aspect"):
                    decision_col = idx
                elif header in ("choice", "value", "selected"):
                    choice_col = idx
                elif header in ("rationale", "reason", "why"):
                    rationale_col = idx
            if decision_col >= 0 and choice_col >= 0:
                continue
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



def get_next_prompt(project: str) -> tuple[str, str | None, str, bool]:
    state = _load_state(project)
    current = state["current_phase"]
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

    precompute_output = _runtime_callable("_run_precompute", "pipeline_precompute")(phase, project, state)
    if precompute_output:
        prompt += "\n\n## Pre-computed Data\n\n" + "\n\n".join(precompute_output)

    if phase == "2b-sign-off" and "{{DIAGRAM_PLACEHOLDER}}" in prompt:
        handoff_path = _repo_root() / "_projects" / project / "docs" / "architecture-handoff.md"
        if handoff_path.exists():
            diagram = _extract_diagram(handoff_path)
            if diagram and diagram.strip():
                prompt = prompt.replace("{{DIAGRAM_PLACEHOLDER}}", diagram.strip())
            else:
                tf = _runtime_callable("_extract_task_flow", "pipeline_precompute")(project)
                ref_diagram = ""
                if tf:
                    ref_path = _repo_root() / "diagrams" / f"{tf}.md"
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
                    prompt = prompt.replace(
                        "{{DIAGRAM_PLACEHOLDER}}",
                        "(Diagram unavailable — review handoff directly)",
                    )
        else:
            prompt = prompt.replace("{{DIAGRAM_PLACEHOLDER}}", "(Architecture handoff not found)")

    return (prompt, agent, phase, is_gate)
