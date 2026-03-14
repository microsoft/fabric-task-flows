"""Tests for run-pipeline.py — verifies project-name guardrails in start_pipeline()."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SHARED_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SHARED_DIR.parent
SCRIPT_PATH = SHARED_DIR / "scripts" / "run-pipeline.py"


def _load_module():
    """Dynamically load run-pipeline.py (hyphenated name requires importlib)."""
    spec = importlib.util.spec_from_file_location("run_pipeline", str(SCRIPT_PATH))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_pipeline"] = mod
    spec.loader.exec_module(mod)
    return mod


rp = _load_module()


# ── Project-name guardrail tests ─────────────────────────────────────────


class TestStartPipelineNameValidation:
    """Verify start_pipeline() rejects empty and placeholder project names."""

    def test_empty_name_raises(self):
        """Empty string should raise ValueError."""
        with pytest.raises(ValueError, match="required"):
            rp.start_pipeline("")

    def test_whitespace_only_raises(self):
        """Whitespace-only name should raise ValueError."""
        with pytest.raises(ValueError, match="required"):
            rp.start_pipeline("   ")

    def test_placeholder_tbd_raises(self):
        """'TBD' should be rejected as a placeholder."""
        with pytest.raises(ValueError, match="placeholder"):
            rp.start_pipeline("TBD")

    def test_placeholder_project_raises(self):
        """'Project' should be rejected as a placeholder."""
        with pytest.raises(ValueError, match="placeholder"):
            rp.start_pipeline("Project")

    def test_placeholder_unnamed_raises(self):
        """'Unnamed' should be rejected as a placeholder."""
        with pytest.raises(ValueError, match="placeholder"):
            rp.start_pipeline("Unnamed")

    def test_placeholder_case_insensitive(self):
        """Placeholder check should be case-insensitive."""
        with pytest.raises(ValueError, match="placeholder"):
            rp.start_pipeline("tBd")

    def test_valid_name_accepted(self, tmp_path, monkeypatch):
        """A real project name should pass validation (may fail later in scaffold)."""
        # We only test that the name validation passes — scaffold may fail
        # because we're not in a real repo root, but that's fine.
        # Monkeypatch REPO_ROOT so scaffold looks in tmp_path
        monkeypatch.setattr(rp, "REPO_ROOT", tmp_path)
        # Create minimal structure scaffold expects
        (tmp_path / "_projects").mkdir(exist_ok=True)
        # This will pass name validation but may raise in scaffold — that's OK,
        # we're only testing the name gate.
        try:
            rp.start_pipeline("Shop Floor Monitor")
        except (FileNotFoundError, ModuleNotFoundError, Exception) as e:
            # Expected: scaffold infrastructure not available in test env.
            # The important thing is it did NOT raise ValueError.
            assert not isinstance(e, ValueError), f"Valid name rejected: {e}"

    def test_placeholder_list_coverage(self):
        """All known placeholder names should be rejected."""
        for name in ["tbd", "placeholder", "test", "unnamed", "untitled",
                      "new", "demo", "sample", "example", "temp", "tmp",
                      "n/a", "none"]:
            with pytest.raises(ValueError, match="placeholder"):
                rp.start_pipeline(name)


# ── Helpers ──────────────────────────────────────────────────────────────

PHASE_ORDER = [
    "0a-discovery", "1-design", "2a-test-plan",
    "2b-sign-off", "2c-deploy", "3-validate", "4-document",
]

SKILLS_REGISTRY = {
    "phase_order": PHASE_ORDER,
    "phases": {
        "0a-discovery": {"skill": "fabric-discover", "output": ["prd/discovery-brief.md"]},
        "1-design": {"skill": "fabric-design", "output": ["prd/architecture-handoff.md"]},
        "2a-test-plan": {"skill": "fabric-test", "mode": 1, "output": ["prd/test-plan.md"]},
        "2b-sign-off": {"skill": None, "gate": "human", "output": []},
        "2c-deploy": {"skill": "fabric-deploy", "output": ["prd/deployment-handoff.md"]},
        "3-validate": {"skill": "fabric-test", "mode": 2, "output": ["prd/validation-report.md"]},
        "4-document": {"skill": "fabric-document", "output": ["docs/README.md"]},
    },
    "standalone_skills": {},
}


def _make_state(project="test-proj", current="0a-discovery", task_flow=None,
                display_name="Test Project", problem=None, overrides=None):
    """Build a minimal valid pipeline-state.json dict."""
    state = {
        "project": project,
        "display_name": display_name,
        "current_phase": current,
        "task_flow": task_flow,
        "phases": {},
        "transitions": [],
    }
    if problem:
        state["problem_statement"] = problem
    order = PHASE_ORDER
    idx = order.index(current)
    for i, p in enumerate(order):
        if i < idx:
            state["phases"][p] = {"status": "complete"}
        elif i == idx:
            state["phases"][p] = {"status": "in_progress"}
        else:
            state["phases"][p] = {"status": "pending"}
    if overrides:
        state.update(overrides)
    return state


def _write_state(tmp_path, project, state):
    """Write pipeline-state.json into the expected location."""
    proj_dir = tmp_path / "_projects" / project
    proj_dir.mkdir(parents=True, exist_ok=True)
    (proj_dir / "prd").mkdir(exist_ok=True)
    state_file = proj_dir / "pipeline-state.json"
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state_file


def _patch_repo(monkeypatch, tmp_path):
    """Point module globals at tmp_path so file I/O is sandboxed."""
    monkeypatch.setattr(rp, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(rp, "_REGISTRY", SKILLS_REGISTRY)
    # Write registry file so _load_skills_registry works if called
    reg_dir = tmp_path / "_shared" / "registry"
    reg_dir.mkdir(parents=True, exist_ok=True)
    (reg_dir / "skills-registry.json").write_text(
        json.dumps(SKILLS_REGISTRY), encoding="utf-8"
    )


# ── State management tests ──────────────────────────────────────────────


class TestStateManagement:
    """Tests for _load_state, _save_state, and _state_path."""

    def test_load_state_valid_json(self, tmp_path, monkeypatch):
        """_load_state returns parsed dict for valid JSON."""
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state()
        _write_state(tmp_path, "test-proj", state)
        loaded = rp._load_state("test-proj")
        assert loaded["project"] == "test-proj"
        assert loaded["current_phase"] == "0a-discovery"

    def test_load_state_missing_file(self, tmp_path, monkeypatch):
        """_load_state raises FileNotFoundError for missing project."""
        _patch_repo(monkeypatch, tmp_path)
        with pytest.raises(FileNotFoundError, match="No pipeline-state.json"):
            rp._load_state("nonexistent")

    def test_load_state_malformed_json(self, tmp_path, monkeypatch):
        """_load_state raises on corrupted JSON."""
        _patch_repo(monkeypatch, tmp_path)
        proj_dir = tmp_path / "_projects" / "bad-proj"
        proj_dir.mkdir(parents=True)
        (proj_dir / "pipeline-state.json").write_text("{invalid json!!", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            rp._load_state("bad-proj")

    def test_save_state_writes_json(self, tmp_path, monkeypatch):
        """_save_state persists state and it round-trips through _load_state."""
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state()
        # Create the directory first
        (tmp_path / "_projects" / "test-proj").mkdir(parents=True)
        rp._save_state("test-proj", state)
        loaded = rp._load_state("test-proj")
        assert loaded == state

    def test_save_state_overwrites_existing(self, tmp_path, monkeypatch):
        """_save_state overwrites previous state."""
        _patch_repo(monkeypatch, tmp_path)
        state_v1 = _make_state(task_flow=None)
        _write_state(tmp_path, "test-proj", state_v1)
        state_v2 = _make_state(task_flow="medallion")
        rp._save_state("test-proj", state_v2)
        loaded = rp._load_state("test-proj")
        assert loaded["task_flow"] == "medallion"

    def test_state_path_structure(self, tmp_path, monkeypatch):
        """_state_path returns correct path under _projects/<name>/."""
        _patch_repo(monkeypatch, tmp_path)
        path = rp._state_path("my-proj")
        assert path == tmp_path / "_projects" / "my-proj" / "pipeline-state.json"


# ── Phase ordering tests ────────────────────────────────────────────────


class TestPhaseOrdering:
    """Tests for _next_phase and phase progression."""

    def test_next_phase_returns_successor(self, monkeypatch):
        """Each phase returns its correct successor."""
        monkeypatch.setattr(rp, "_REGISTRY", SKILLS_REGISTRY)
        assert rp._next_phase("0a-discovery") == "1-design"
        assert rp._next_phase("1-design") == "2a-test-plan"
        assert rp._next_phase("2a-test-plan") == "2b-sign-off"
        assert rp._next_phase("2b-sign-off") == "2c-deploy"
        assert rp._next_phase("2c-deploy") == "3-validate"
        assert rp._next_phase("3-validate") == "4-document"

    def test_next_phase_returns_none_for_last(self, monkeypatch):
        """Last phase (4-document) returns None."""
        monkeypatch.setattr(rp, "_REGISTRY", SKILLS_REGISTRY)
        assert rp._next_phase("4-document") is None

    def test_next_phase_raises_for_unknown(self, monkeypatch):
        """Unknown phase raises ValueError from list.index()."""
        monkeypatch.setattr(rp, "_REGISTRY", SKILLS_REGISTRY)
        with pytest.raises(ValueError):
            rp._next_phase("unknown-phase")

    def test_phase_order_length(self, monkeypatch):
        """Registry defines exactly 7 phases."""
        monkeypatch.setattr(rp, "_REGISTRY", SKILLS_REGISTRY)
        assert len(rp._phase_order()) == 7


# ── Phase metadata helpers ──────────────────────────────────────────────


class TestPhaseMetadata:
    """Tests for _phase_skill, _phase_mode, _phase_is_gate, _phase_output_files."""

    def test_phase_skill_returns_skill_name(self, monkeypatch):
        monkeypatch.setattr(rp, "_REGISTRY", SKILLS_REGISTRY)
        assert rp._phase_skill("0a-discovery") == "fabric-discover"
        assert rp._phase_skill("2c-deploy") == "fabric-deploy"

    def test_phase_skill_returns_none_for_gate(self, monkeypatch):
        monkeypatch.setattr(rp, "_REGISTRY", SKILLS_REGISTRY)
        assert rp._phase_skill("2b-sign-off") is None

    def test_phase_skill_returns_none_for_unknown(self, monkeypatch):
        monkeypatch.setattr(rp, "_REGISTRY", SKILLS_REGISTRY)
        assert rp._phase_skill("nonexistent") is None

    def test_phase_mode(self, monkeypatch):
        monkeypatch.setattr(rp, "_REGISTRY", SKILLS_REGISTRY)
        assert rp._phase_mode("2a-test-plan") == 1
        assert rp._phase_mode("3-validate") == 2
        assert rp._phase_mode("0a-discovery") is None

    def test_phase_is_gate(self, monkeypatch):
        monkeypatch.setattr(rp, "_REGISTRY", SKILLS_REGISTRY)
        assert rp._phase_is_gate("2b-sign-off") is True
        assert rp._phase_is_gate("0a-discovery") is False
        assert rp._phase_is_gate("1-design") is False

    def test_phase_output_files(self, monkeypatch):
        monkeypatch.setattr(rp, "_REGISTRY", SKILLS_REGISTRY)
        assert rp._phase_output_files("0a-discovery") == ["prd/discovery-brief.md"]
        assert rp._phase_output_files("2b-sign-off") == []


# ── Prompt generation tests ─────────────────────────────────────────────


class TestPromptGeneration:
    """Tests for _prompt_for_phase."""

    def test_prompt_contains_project_name(self, monkeypatch):
        monkeypatch.setattr(rp, "_REGISTRY", SKILLS_REGISTRY)
        state = _make_state(display_name="Farm Fleet")
        prompt = rp._prompt_for_phase("0a-discovery", "farm-fleet", state)
        assert "Farm Fleet" in prompt

    def test_prompt_contains_task_flow_when_set(self, monkeypatch):
        monkeypatch.setattr(rp, "_REGISTRY", SKILLS_REGISTRY)
        state = _make_state(task_flow="medallion", current="2c-deploy")
        prompt = rp._prompt_for_phase("2c-deploy", "test-proj", state)
        assert "medallion" in prompt

    def test_prompt_shows_tbd_when_no_task_flow(self, monkeypatch):
        monkeypatch.setattr(rp, "_REGISTRY", SKILLS_REGISTRY)
        state = _make_state(task_flow=None, current="2c-deploy")
        prompt = rp._prompt_for_phase("2c-deploy", "test-proj", state)
        assert "TBD" in prompt

    def test_prompt_contains_skill_instruction(self, monkeypatch):
        monkeypatch.setattr(rp, "_REGISTRY", SKILLS_REGISTRY)
        state = _make_state()
        prompt = rp._prompt_for_phase("0a-discovery", "test-proj", state)
        assert "/fabric-discover" in prompt

    def test_prompt_contains_project_folder(self, monkeypatch):
        monkeypatch.setattr(rp, "_REGISTRY", SKILLS_REGISTRY)
        state = _make_state()
        prompt = rp._prompt_for_phase("0a-discovery", "test-proj", state)
        assert "projects/test-proj" in prompt

    def test_prompt_includes_problem_statement(self, monkeypatch):
        monkeypatch.setattr(rp, "_REGISTRY", SKILLS_REGISTRY)
        state = _make_state(problem="IoT sensor data from 500 machines")
        prompt = rp._prompt_for_phase("0a-discovery", "test-proj", state)
        assert "IoT sensor data from 500 machines" in prompt

    def test_prompt_sign_off_is_human_gate(self, monkeypatch):
        monkeypatch.setattr(rp, "_REGISTRY", SKILLS_REGISTRY)
        state = _make_state(current="2b-sign-off")
        prompt = rp._prompt_for_phase("2b-sign-off", "test-proj", state)
        assert "HUMAN GATE" in prompt

    def test_prompt_unknown_phase_returns_message(self, monkeypatch):
        monkeypatch.setattr(rp, "_REGISTRY", SKILLS_REGISTRY)
        state = _make_state()
        prompt = rp._prompt_for_phase("nonexistent", "test-proj", state)
        assert "Unknown phase" in prompt

    def test_prompt_design_revision_includes_feedback_note(self, monkeypatch):
        """When sign_off_revisions > 0, design prompt mentions revision."""
        monkeypatch.setattr(rp, "_REGISTRY", SKILLS_REGISTRY)
        state = _make_state(current="1-design")
        state["sign_off_revisions"] = 2
        prompt = rp._prompt_for_phase("1-design", "test-proj", state)
        assert "SIGN-OFF REVISION" in prompt
        assert "sign-off-feedback.md" in prompt


# ── Advance tests ────────────────────────────────────────────────────────


class TestAdvance:
    """Tests for advance() state transitions."""

    def _setup_phase_with_output(self, tmp_path, monkeypatch, project, phase,
                                 task_flow=None):
        """Set up a project at a given phase with its output files populated."""
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state(project=project, current=phase, task_flow=task_flow)
        _write_state(tmp_path, project, state)

        proj_dir = tmp_path / "_projects" / project
        # Create output files with enough content to pass MIN_CONTENT_SIZE
        output_files = SKILLS_REGISTRY["phases"][phase].get("output", [])
        for rel in output_files:
            f = proj_dir / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("x" * 300, encoding="utf-8")
        return state

    def test_advance_moves_to_next_phase(self, tmp_path, monkeypatch):
        """advance() marks current complete and sets next as in_progress."""
        self._setup_phase_with_output(tmp_path, monkeypatch, "p1", "0a-discovery")
        result = rp.advance("p1")
        assert result["current_phase"] == "1-design"
        assert result["phases"]["0a-discovery"]["status"] == "complete"
        assert result["phases"]["1-design"]["status"] == "in_progress"

    def test_advance_fails_without_output(self, tmp_path, monkeypatch):
        """advance() refuses to advance when output files are missing."""
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state(project="p2", current="0a-discovery")
        _write_state(tmp_path, "p2", state)
        # Don't create output files
        result = rp.advance("p2")
        # Should remain in the same phase
        assert result["current_phase"] == "0a-discovery"

    def test_advance_blocks_at_human_gate_without_approval(self, tmp_path, monkeypatch):
        """advance() blocks at sign-off gate without approved=True."""
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state(project="p3", current="2b-sign-off")
        # Sign-off has no output files, but has a non-auto transition
        state["transitions"] = [{"from": "2b-sign-off", "auto": False}]
        _write_state(tmp_path, "p3", state)
        result = rp.advance("p3")
        assert result["current_phase"] == "2b-sign-off"

    def test_advance_passes_gate_with_approval(self, tmp_path, monkeypatch):
        """advance() proceeds past gate when approved=True."""
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state(project="p4", current="2b-sign-off")
        state["transitions"] = [{"from": "2b-sign-off", "auto": False}]
        _write_state(tmp_path, "p4", state)
        result = rp.advance("p4", approved=True)
        assert result["current_phase"] == "2c-deploy"
        assert result["phases"]["2b-sign-off"]["status"] == "complete"

    def test_advance_extracts_task_flow_after_design(self, tmp_path, monkeypatch):
        """advance() extracts task_flow from architecture-handoff.md after 1-design."""
        self._setup_phase_with_output(tmp_path, monkeypatch, "p5", "1-design")
        # Write a handoff with task_flow frontmatter
        handoff = tmp_path / "_projects" / "p5" / "prd" / "architecture-handoff.md"
        handoff.write_text(
            "---\ntask_flow: medallion\n---\n# Handoff\n" + ("x" * 300),
            encoding="utf-8",
        )
        result = rp.advance("p5")
        assert result["task_flow"] == "medallion"


# ── Revise (sign-off loop) tests ────────────────────────────────────────


class TestRevise:
    """Tests for the --revise loop in advance()."""

    def test_revise_resets_to_design(self, tmp_path, monkeypatch):
        """--revise resets pipeline back to 1-design."""
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state(project="rv1", current="2b-sign-off")
        _write_state(tmp_path, "rv1", state)
        result = rp.advance("rv1", revise=True, feedback="Change the storage layer")
        assert result["current_phase"] == "1-design"
        assert result["sign_off_revisions"] == 1

    def test_revise_saves_feedback_file(self, tmp_path, monkeypatch):
        """--revise with feedback writes sign-off-feedback.md."""
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state(project="rv2", current="2b-sign-off")
        _write_state(tmp_path, "rv2", state)
        rp.advance("rv2", revise=True, feedback="Use EventStream instead")
        fb_path = tmp_path / "_projects" / "rv2" / "prd" / "sign-off-feedback.md"
        assert fb_path.exists()
        content = fb_path.read_text(encoding="utf-8")
        assert "Use EventStream instead" in content

    def test_revise_blocked_after_max_cycles(self, tmp_path, monkeypatch):
        """--revise is rejected after 3 revision cycles."""
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state(project="rv3", current="2b-sign-off")
        state["sign_off_revisions"] = 3
        _write_state(tmp_path, "rv3", state)
        result = rp.advance("rv3", revise=True)
        # Should remain at sign-off, not reset
        assert result["current_phase"] == "2b-sign-off"

    def test_revise_only_valid_at_sign_off(self, tmp_path, monkeypatch):
        """--revise is ignored when not at 2b-sign-off."""
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state(project="rv4", current="0a-discovery")
        _write_state(tmp_path, "rv4", state)
        result = rp.advance("rv4", revise=True)
        assert result["current_phase"] == "0a-discovery"


# ── Reset tests ──────────────────────────────────────────────────────────


class TestResetPhase:
    """Tests for reset_phase()."""

    def test_reset_resets_current_and_subsequent(self, tmp_path, monkeypatch):
        """reset_phase resets target and all later phases to pending."""
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state(project="rs1", current="3-validate")
        _write_state(tmp_path, "rs1", state)
        result = rp.reset_phase("rs1", "1-design")
        assert result["current_phase"] == "1-design"
        assert result["phases"]["1-design"]["status"] == "pending"
        assert result["phases"]["2a-test-plan"]["status"] == "pending"
        assert result["phases"]["4-document"]["status"] == "pending"
        # Phases before the reset point stay untouched
        assert result["phases"]["0a-discovery"]["status"] == "complete"


# ── Verify output tests ─────────────────────────────────────────────────


class TestVerifyOutput:
    """Tests for _verify_output."""

    def test_verify_passes_with_content(self, tmp_path, monkeypatch):
        """Files over MIN_CONTENT_SIZE without template markers pass."""
        _patch_repo(monkeypatch, tmp_path)
        proj_dir = tmp_path / "_projects" / "vo1"
        (proj_dir / "prd").mkdir(parents=True)
        (proj_dir / "prd" / "discovery-brief.md").write_text(
            "x" * 300, encoding="utf-8"
        )
        ok, msg = rp._verify_output("0a-discovery", "vo1")
        assert ok is True

    def test_verify_fails_for_missing_file(self, tmp_path, monkeypatch):
        """Missing output files cause verify to fail."""
        _patch_repo(monkeypatch, tmp_path)
        (tmp_path / "_projects" / "vo2" / "prd").mkdir(parents=True)
        ok, msg = rp._verify_output("0a-discovery", "vo2")
        assert ok is False
        assert "Missing" in msg

    def test_verify_fails_for_small_file(self, tmp_path, monkeypatch):
        """Files smaller than MIN_CONTENT_SIZE are flagged as unfilled."""
        _patch_repo(monkeypatch, tmp_path)
        proj_dir = tmp_path / "_projects" / "vo3"
        (proj_dir / "prd").mkdir(parents=True)
        (proj_dir / "prd" / "discovery-brief.md").write_text("tiny", encoding="utf-8")
        ok, msg = rp._verify_output("0a-discovery", "vo3")
        assert ok is False
        assert "template" in msg.lower() or "placeholder" in msg.lower()

    def test_verify_fails_for_template_marker(self, tmp_path, monkeypatch):
        """Files containing template markers are flagged as unfilled."""
        _patch_repo(monkeypatch, tmp_path)
        proj_dir = tmp_path / "_projects" / "vo4"
        (proj_dir / "prd").mkdir(parents=True)
        content = "# Brief\ntask_flow: TBD\n" + ("x" * 300)
        (proj_dir / "prd" / "discovery-brief.md").write_text(content, encoding="utf-8")
        ok, msg = rp._verify_output("0a-discovery", "vo4")
        assert ok is False

    def test_verify_ok_when_no_output_required(self, monkeypatch):
        """Phases with no required output always pass (e.g., sign-off)."""
        monkeypatch.setattr(rp, "_REGISTRY", SKILLS_REGISTRY)
        ok, msg = rp._verify_output("2b-sign-off", "any-project")
        assert ok is True


# ── Extract task flow tests ──────────────────────────────────────────────


class TestExtractTaskFlow:
    """Tests for _extract_task_flow."""

    def test_extracts_from_yaml_frontmatter(self, tmp_path, monkeypatch):
        _patch_repo(monkeypatch, tmp_path)
        proj_dir = tmp_path / "_projects" / "tf1" / "prd"
        proj_dir.mkdir(parents=True)
        (proj_dir / "architecture-handoff.md").write_text(
            "---\ntask_flow: lambda\n---\n# Handoff", encoding="utf-8"
        )
        assert rp._extract_task_flow("tf1") == "lambda"

    def test_extracts_hyphenated_key(self, tmp_path, monkeypatch):
        _patch_repo(monkeypatch, tmp_path)
        proj_dir = tmp_path / "_projects" / "tf2" / "prd"
        proj_dir.mkdir(parents=True)
        (proj_dir / "architecture-handoff.md").write_text(
            "---\ntask-flow: medallion\n---\n# Handoff", encoding="utf-8"
        )
        assert rp._extract_task_flow("tf2") == "medallion"

    def test_returns_none_when_no_handoff(self, tmp_path, monkeypatch):
        _patch_repo(monkeypatch, tmp_path)
        (tmp_path / "_projects" / "tf3" / "prd").mkdir(parents=True)
        assert rp._extract_task_flow("tf3") is None

    def test_extracts_from_body_fallback(self, tmp_path, monkeypatch):
        _patch_repo(monkeypatch, tmp_path)
        proj_dir = tmp_path / "_projects" / "tf4" / "prd"
        proj_dir.mkdir(parents=True)
        (proj_dir / "architecture-handoff.md").write_text(
            "# Handoff\nTask Flow: `medallion`\n", encoding="utf-8"
        )
        assert rp._extract_task_flow("tf4") == "medallion"


# ── get_status tests ─────────────────────────────────────────────────────


class TestGetStatus:
    """Tests for get_status (thin wrapper over _load_state)."""

    def test_returns_state_dict(self, tmp_path, monkeypatch):
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state()
        _write_state(tmp_path, "test-proj", state)
        result = rp.get_status("test-proj")
        assert result["project"] == "test-proj"

    def test_raises_for_missing_project(self, tmp_path, monkeypatch):
        _patch_repo(monkeypatch, tmp_path)
        with pytest.raises(FileNotFoundError):
            rp.get_status("nope")


# ── _is_auto tests ───────────────────────────────────────────────────────


class TestIsAuto:
    """Tests for _is_auto transition checking."""

    def test_returns_true_by_default(self):
        state = {"transitions": []}
        assert rp._is_auto(state, "0a-discovery") is True

    def test_returns_false_when_auto_false(self):
        state = {"transitions": [{"from": "2b-sign-off", "auto": False}]}
        assert rp._is_auto(state, "2b-sign-off") is False

    def test_returns_true_when_auto_true(self):
        state = {"transitions": [{"from": "0a-discovery", "auto": True}]}
        assert rp._is_auto(state, "0a-discovery") is True

    def test_returns_true_for_unmatched_phase(self):
        state = {"transitions": [{"from": "1-design", "auto": False}]}
        assert rp._is_auto(state, "0a-discovery") is True
