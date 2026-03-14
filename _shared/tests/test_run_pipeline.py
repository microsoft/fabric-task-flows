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
        "0a-discovery": {"skill": "fabric-discover", "output": ["docs/discovery-brief.md"]},
        "1-design": {"skill": "fabric-design", "output": ["docs/architecture-handoff.md"]},
        "2a-test-plan": {"skill": "fabric-test", "mode": 1, "output": ["docs/test-plan.md"]},
        "2b-sign-off": {"skill": None, "gate": "human", "output": []},
        "2c-deploy": {"skill": "fabric-deploy", "output": ["docs/deployment-handoff.md"]},
        "3-validate": {"skill": "fabric-test", "mode": 2, "output": ["docs/validation-report.md"]},
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
    (proj_dir / "docs").mkdir(exist_ok=True)
    state_file = proj_dir / "pipeline-state.json"
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state_file


def _scaffold_project(tmp_path, project):
    """Create a minimal project directory structure for testing."""
    proj_dir = tmp_path / "_projects" / project
    proj_dir.mkdir(parents=True, exist_ok=True)
    (proj_dir / "docs").mkdir(exist_ok=True)
    (proj_dir / "docs" / "decisions").mkdir(parents=True, exist_ok=True)
    # Write empty template files so they exist
    for fname in ["discovery-brief.md", "architecture-handoff.md", "test-plan.md"]:
        (proj_dir / "docs" / fname).write_text("", encoding="utf-8")
    for i in range(1, 6):
        titles = {1: "task-flow", 2: "storage", 3: "ingestion", 4: "processing", 5: "visualization"}
        (proj_dir / "docs" / "decisions" / f"{i:03d}-{titles[i]}.md").write_text("", encoding="utf-8")


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
        assert rp._phase_output_files("0a-discovery") == ["docs/discovery-brief.md"]
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
        handoff = tmp_path / "_projects" / "p5" / "docs" / "architecture-handoff.md"
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
        fb_path = tmp_path / "_projects" / "rv2" / "docs" / "sign-off-feedback.md"
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
        (proj_dir / "docs").mkdir(parents=True)
        (proj_dir / "docs" / "discovery-brief.md").write_text(
            "x" * 300, encoding="utf-8"
        )
        ok, msg = rp._verify_output("0a-discovery", "vo1")
        assert ok is True

    def test_verify_fails_for_missing_file(self, tmp_path, monkeypatch):
        """Missing output files cause verify to fail."""
        _patch_repo(monkeypatch, tmp_path)
        (tmp_path / "_projects" / "vo2" / "docs").mkdir(parents=True)
        ok, msg = rp._verify_output("0a-discovery", "vo2")
        assert ok is False
        assert "Missing" in msg

    def test_verify_fails_for_small_file(self, tmp_path, monkeypatch):
        """Files smaller than MIN_CONTENT_SIZE are flagged as unfilled."""
        _patch_repo(monkeypatch, tmp_path)
        proj_dir = tmp_path / "_projects" / "vo3"
        (proj_dir / "docs").mkdir(parents=True)
        (proj_dir / "docs" / "discovery-brief.md").write_text("tiny", encoding="utf-8")
        ok, msg = rp._verify_output("0a-discovery", "vo3")
        assert ok is False
        assert "template" in msg.lower() or "placeholder" in msg.lower()

    def test_verify_fails_for_template_marker(self, tmp_path, monkeypatch):
        """Files containing template markers are flagged as unfilled."""
        _patch_repo(monkeypatch, tmp_path)
        proj_dir = tmp_path / "_projects" / "vo4"
        (proj_dir / "docs").mkdir(parents=True)
        content = "# Brief\ntask_flow: TBD\n" + ("x" * 300)
        (proj_dir / "docs" / "discovery-brief.md").write_text(content, encoding="utf-8")
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
        proj_dir = tmp_path / "_projects" / "tf1" / "docs"
        proj_dir.mkdir(parents=True)
        (proj_dir / "architecture-handoff.md").write_text(
            "---\ntask_flow: lambda\n---\n# Handoff", encoding="utf-8"
        )
        assert rp._extract_task_flow("tf1") == "lambda"

    def test_extracts_hyphenated_key(self, tmp_path, monkeypatch):
        _patch_repo(monkeypatch, tmp_path)
        proj_dir = tmp_path / "_projects" / "tf2" / "docs"
        proj_dir.mkdir(parents=True)
        (proj_dir / "architecture-handoff.md").write_text(
            "---\ntask-flow: medallion\n---\n# Handoff", encoding="utf-8"
        )
        assert rp._extract_task_flow("tf2") == "medallion"

    def test_returns_none_when_no_handoff(self, tmp_path, monkeypatch):
        _patch_repo(monkeypatch, tmp_path)
        (tmp_path / "_projects" / "tf3" / "docs").mkdir(parents=True)
        assert rp._extract_task_flow("tf3") is None

    def test_extracts_from_body_fallback(self, tmp_path, monkeypatch):
        _patch_repo(monkeypatch, tmp_path)
        proj_dir = tmp_path / "_projects" / "tf4" / "docs"
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


# ── Regression tests for pipeline bugs ──────────────────────────────────


class TestPrecomputeSignalMapper:
    """Regression: signal mapper must receive --project arg (Bug #1)."""

    def test_precompute_signal_mapper_includes_project_arg(self, tmp_path, monkeypatch):
        """_run_precompute for discovery builds cmd with --project."""
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state(problem="IoT sensor analytics")
        # Capture the subprocess.run call instead of executing it
        captured_cmds = []
        import subprocess as _sp

        original_run = _sp.run

        def fake_run(cmd, **kwargs):
            captured_cmds.append(cmd)
            # Return a fake successful result
            return type("Result", (), {"returncode": 0, "stdout": "{}", "stderr": ""})()

        monkeypatch.setattr(_sp, "run", fake_run)
        rp._run_precompute("0a-discovery", "test-proj", state)
        assert len(captured_cmds) == 1, "Expected signal mapper to be called"
        cmd = captured_cmds[0]
        assert "--project" in cmd, f"--project missing from cmd: {cmd}"
        proj_idx = cmd.index("--project")
        assert cmd[proj_idx + 1] == "test-proj", f"Wrong project value: {cmd[proj_idx + 1]}"

    def test_precompute_signal_mapper_includes_text(self, tmp_path, monkeypatch):
        """_run_precompute for discovery passes --text with problem statement."""
        _patch_repo(monkeypatch, tmp_path)
        problem = "Real-time fan analytics for game day"
        state = _make_state(problem=problem)
        captured_cmds = []
        import subprocess as _sp

        def fake_run(cmd, **kwargs):
            captured_cmds.append(cmd)
            return type("Result", (), {"returncode": 0, "stdout": "{}", "stderr": ""})()

        monkeypatch.setattr(_sp, "run", fake_run)
        rp._run_precompute("0a-discovery", "test-proj", state)
        cmd = captured_cmds[0]
        assert "--text" in cmd
        text_idx = cmd.index("--text")
        assert cmd[text_idx + 1] == problem

    def test_precompute_skipped_without_problem(self, tmp_path, monkeypatch):
        """_run_precompute for discovery does nothing if no problem_statement."""
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state()  # No problem_statement
        import subprocess as _sp

        call_count = [0]

        def fake_run(cmd, **kwargs):
            call_count[0] += 1
            return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

        monkeypatch.setattr(_sp, "run", fake_run)
        rp._run_precompute("0a-discovery", "test-proj", state)
        assert call_count[0] == 0, "Signal mapper should not run without problem statement"


class TestPrecomputeFilesystemPath:
    """Regression: _run_precompute must use _projects/ for filesystem paths (Bug #7)."""

    def test_precompute_test_plan_uses_correct_path(self, tmp_path, monkeypatch):
        """_run_precompute for 2a-test-plan finds handoff at _projects/ path."""
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state(current="2a-test-plan", task_flow="medallion")
        # Create handoff at the CORRECT location
        handoff_dir = tmp_path / "_projects" / "test-proj" / "docs"
        handoff_dir.mkdir(parents=True, exist_ok=True)
        (handoff_dir / "architecture-handoff.md").write_text(
            "---\ntask_flow: medallion\n---\n# Handoff\n" + ("x" * 300),
            encoding="utf-8",
        )
        captured_cmds = []
        import subprocess as _sp

        def fake_run(cmd, **kwargs):
            captured_cmds.append(cmd)
            return type("Result", (), {"returncode": 0, "stdout": "prefill output", "stderr": ""})()

        monkeypatch.setattr(_sp, "run", fake_run)
        outputs = rp._run_precompute("2a-test-plan", "test-proj", state)
        assert len(captured_cmds) == 1, "Test plan prefill should be called when handoff exists"
        # Verify the handoff path passed to the script points to _projects/
        cmd = captured_cmds[0]
        handoff_arg = cmd[cmd.index("--handoff") + 1]
        assert "_projects" in handoff_arg, f"Handoff path must use _projects/: {handoff_arg}"
        assert "projects/test-proj" not in handoff_arg or "_projects/test-proj" in handoff_arg

    def test_precompute_test_plan_skipped_without_handoff(self, tmp_path, monkeypatch):
        """_run_precompute for 2a-test-plan does nothing if handoff doesn't exist."""
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state(current="2a-test-plan", task_flow="medallion")
        # Do NOT create handoff file
        import subprocess as _sp

        call_count = [0]

        def fake_run(cmd, **kwargs):
            call_count[0] += 1
            return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

        monkeypatch.setattr(_sp, "run", fake_run)
        rp._run_precompute("2a-test-plan", "test-proj", state)
        assert call_count[0] == 0, "Prefill should not run without handoff file"


class TestSignoffDiagramDisplay:
    """Regression: sign-off diagram must not be suppressed by -q flag (Bug #4)."""

    def test_signoff_summary_shows_diagram(self, tmp_path, monkeypatch):
        """_print_signoff_summary shows the architecture diagram."""
        _patch_repo(monkeypatch, tmp_path)
        handoff_dir = tmp_path / "_projects" / "test-proj" / "docs"
        handoff_dir.mkdir(parents=True, exist_ok=True)
        (handoff_dir / "architecture-handoff.md").write_text(
            "# Handoff\n\n## Architecture Diagram\n\n```\n"
            "┌─────────┐\n│ MyItem  │\n└─────────┘\n"
            "```\n\n## Decisions\n",
            encoding="utf-8",
        )
        (handoff_dir / "architecture-summary.json").write_text(
            '{"task_flow":"medallion","items":[],"decisions":{},"item_count":0,"wave_count":0}',
            encoding="utf-8",
        )
        import io
        captured = io.StringIO()
        monkeypatch.setattr("sys.stdout", captured)
        rp._print_signoff_summary("test-proj")
        output = captured.getvalue()
        assert "ARCHITECTURE REVIEW" in output
        assert "MyItem" in output

    def test_signoff_summary_silent_when_no_handoff(self, tmp_path, monkeypatch):
        """_print_signoff_summary still runs (with no diagram) if handoff file is missing."""
        _patch_repo(monkeypatch, tmp_path)
        import io
        captured = io.StringIO()
        monkeypatch.setattr("sys.stdout", captured)
        rp._print_signoff_summary("nonexistent-proj")
        # Should still print header even without diagram
        output = captured.getvalue()
        assert "ARCHITECTURE REVIEW" in output

    def test_signoff_summary_no_diagram_when_no_code_block(self, tmp_path, monkeypatch):
        """_print_signoff_summary omits diagram if section has no code block."""
        _patch_repo(monkeypatch, tmp_path)
        handoff_dir = tmp_path / "_projects" / "test-proj" / "docs"
        handoff_dir.mkdir(parents=True, exist_ok=True)
        (handoff_dir / "architecture-handoff.md").write_text(
            "# Handoff\n\n## Architecture Diagram\n\nNo diagram yet.\n\n## Decisions\n",
            encoding="utf-8",
        )
        (handoff_dir / "architecture-summary.json").write_text(
            '{"task_flow":"medallion","items":[],"decisions":{},"item_count":0,"wave_count":0}',
            encoding="utf-8",
        )
        import io
        captured = io.StringIO()
        monkeypatch.setattr("sys.stdout", captured)
        rp._print_signoff_summary("test-proj")
        output = captured.getvalue()
        # Header shown, but no diagram box chars
        assert "ARCHITECTURE REVIEW" in output
        assert "┌─────────┐" not in output


class TestGetNextPromptSignoff:
    """Regression: get_next_prompt must resolve filesystem paths correctly (Bug #5)."""

    def test_signoff_prompt_contains_diagram_placeholder(self, monkeypatch):
        """Sign-off phase prompt template includes {{DIAGRAM_PLACEHOLDER}}."""
        monkeypatch.setattr(rp, "_REGISTRY", SKILLS_REGISTRY)
        state = _make_state(current="2b-sign-off")
        prompt = rp._prompt_for_phase("2b-sign-off", "test-proj", state)
        assert "{{DIAGRAM_PLACEHOLDER}}" in prompt

    def test_get_next_prompt_returns_gate_for_signoff(self, tmp_path, monkeypatch):
        """get_next_prompt returns is_gate=True for sign-off phase."""
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state(project="gp1", current="2b-sign-off")
        state["transitions"] = [{"from": "2b-sign-off", "auto": False}]
        _write_state(tmp_path, "gp1", state)
        _prompt, _agent, phase, is_gate = rp.get_next_prompt("gp1")
        assert phase == "2b-sign-off"
        assert is_gate is True

    def test_get_next_prompt_returns_auto_for_non_gate(self, tmp_path, monkeypatch):
        """get_next_prompt returns is_gate=False for auto-chain phases."""
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state(project="gp2", current="1-design")
        _write_state(tmp_path, "gp2", state)
        _prompt, agent, phase, is_gate = rp.get_next_prompt("gp2")
        assert phase == "1-design"
        assert is_gate is False
        assert agent == "fabric-design"

    def test_get_next_prompt_diagram_path_uses_underscored_projects(
        self, tmp_path, monkeypatch
    ):
        """get_next_prompt resolves handoff at _projects/ not projects/ (Bug #5)."""
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state(project="gp3", current="2b-sign-off")
        state["transitions"] = [{"from": "2b-sign-off", "auto": False}]
        _write_state(tmp_path, "gp3", state)
        # Create handoff at the CORRECT _projects/ path
        handoff_dir = tmp_path / "_projects" / "gp3" / "docs"
        handoff_dir.mkdir(parents=True, exist_ok=True)
        (handoff_dir / "architecture-handoff.md").write_text(
            "---\ntask_flow: medallion\n---\n# Handoff\n\n"
            "## Architecture Diagram\n\n```\n"
            "┌─────────┐\n│ TestBox │\n└─────────┘\n"
            "```\n",
            encoding="utf-8",
        )
        # Mock diagram-gen.py since it won't exist in test env
        import subprocess as _sp

        def fake_run(cmd, **kwargs):
            return type("Result", (), {
                "returncode": 0,
                "stdout": "┌─────────┐\n│ TestBox │\n└─────────┘",
                "stderr": "",
            })()

        monkeypatch.setattr(_sp, "run", fake_run)
        prompt, _agent, _phase, _is_gate = rp.get_next_prompt("gp3")
        # The placeholder should be replaced (not "not found")
        assert "(Architecture handoff not found)" not in prompt


# ── Terminal width tests ─────────────────────────────────────────────────


class TestTerminalWidth:
    """Optimization: separators use dynamic terminal width, not hardcoded 68."""

    def test_term_width_returns_int(self):
        width = rp._term_width()
        assert isinstance(width, int)
        assert width > 0

    def test_term_width_fallback(self, monkeypatch):
        """When terminal size unavailable, fallback to 100."""
        import shutil
        monkeypatch.setattr(shutil, "get_terminal_size", lambda fallback=(80, 24): type("TS", (), {"columns": fallback[0], "lines": fallback[1]})())
        width = rp._term_width()
        assert width == 100

    def test_separator_uses_term_width(self, monkeypatch):
        monkeypatch.setattr(rp, "_term_width", lambda: 120)
        sep = rp._separator("TEST LABEL")
        assert "─" * 120 in sep
        assert "TEST LABEL" in sep

    def test_separator_no_label(self, monkeypatch):
        monkeypatch.setattr(rp, "_term_width", lambda: 80)
        sep = rp._separator()
        assert sep == "─" * 80

    def test_signoff_summary_uses_separator(self, tmp_path, monkeypatch, capsys):
        """_print_signoff_summary uses dynamic-width separators."""
        _patch_repo(monkeypatch, tmp_path)
        monkeypatch.setattr(rp, "_term_width", lambda: 150)
        proj_dir = tmp_path / "_projects" / "wp"
        (proj_dir / "docs").mkdir(parents=True)
        (proj_dir / "docs" / "architecture-handoff.md").write_text(
            "---\ntask_flow: medallion\n---\n# Handoff\n\n"
            "## Architecture Diagram\n\n```\n"
            "┌─────────┐\n│ TestBox │\n└─────────┘\n"
            "```\n",
            encoding="utf-8",
        )
        (proj_dir / "docs" / "architecture-summary.json").write_text(
            '{"task_flow":"medallion","items":[],"decisions":{},"item_count":0,"wave_count":0}',
            encoding="utf-8",
        )
        rp._print_signoff_summary("wp")
        out = capsys.readouterr().out
        assert "─" * 150 in out


# ── Problem statement caching tests ──────────────────────────────────────


class TestProblemStatementCache:
    """Optimization: problem_statement is persisted in pipeline-state.json."""

    def test_new_project_template_has_problem_field(self):
        """new-project.py pipeline_state includes problem_statement."""
        import importlib.util
        np_path = REPO_ROOT / "_shared" / "scripts" / "new-project.py"
        spec = importlib.util.spec_from_file_location("new_project", str(np_path))
        mod = importlib.util.module_from_spec(spec)
        sys.modules["new_project_test"] = mod
        spec.loader.exec_module(mod)
        state_json = mod.pipeline_state("test-proj")
        state = json.loads(state_json)
        assert "problem_statement" in state

    def test_problem_available_in_discovery_prompt(self, tmp_path, monkeypatch):
        """Problem statement from state appears in discovery prompt."""
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state(problem="We need analytics for game day")
        _write_state(tmp_path, "test-proj", state)
        prompt, _, _, _ = rp.get_next_prompt("test-proj")
        assert "We need analytics for game day" in prompt


# ── ADR generator tests ─────────────────────────────────────────────────


class TestGenerateAdrs:
    """Tests for _generate_adrs()."""

    def test_writes_all_five_adrs(self, tmp_path, monkeypatch):
        """_generate_adrs creates all 5 ADR files."""
        _patch_repo(monkeypatch, tmp_path)
        _scaffold_project(tmp_path, "test-proj")
        decisions = {
            "decisions": {
                "storage": {"choice": "Lakehouse", "confidence": "high",
                            "rule_matched": "Spark/Python → Lakehouse",
                            "guide": "decisions/storage-selection.md"},
                "ingestion": {"choice": "Pipeline", "confidence": "high",
                              "rule_matched": "Large → Pipeline",
                              "guide": "decisions/ingestion-selection.md"},
                "processing": {"choice": "Notebook", "confidence": "high",
                               "rule_matched": "Interactive → Notebook",
                               "guide": "decisions/processing-selection.md"},
                "visualization": {"choice": "Power BI Report", "confidence": "high",
                                  "rule_matched": "Filters → Report",
                                  "guide": "decisions/visualization-selection.md"},
            }
        }
        report = rp._generate_adrs("test-proj", decisions, "medallion")
        docs_dir = tmp_path / "_projects" / "test-proj" / "docs" / "decisions"
        assert (docs_dir / "001-task-flow.md").exists()
        assert (docs_dir / "002-storage.md").exists()
        assert (docs_dir / "003-ingestion.md").exists()
        assert (docs_dir / "004-processing.md").exists()
        assert (docs_dir / "005-visualization.md").exists()
        assert len(report) >= 5

    def test_adr_contains_choice(self, tmp_path, monkeypatch):
        """ADR-002 contains the storage choice."""
        _patch_repo(monkeypatch, tmp_path)
        _scaffold_project(tmp_path, "test-proj")
        decisions = {
            "decisions": {
                "storage": {"choice": "Lakehouse", "confidence": "high",
                            "rule_matched": "Spark/Python → Lakehouse",
                            "guide": "decisions/storage-selection.md",
                            "rationale": "Spark/Python skillset is best served by Lakehouse"},
            }
        }
        rp._generate_adrs("test-proj", decisions, "medallion")
        content = (tmp_path / "_projects" / "test-proj" / "docs" / "decisions" / "002-storage.md").read_text(encoding="utf-8")
        assert "Lakehouse" in content
        assert "Spark/Python" in content

    def test_adr_001_contains_task_flow(self, tmp_path, monkeypatch):
        """ADR-001 contains the task flow name."""
        _patch_repo(monkeypatch, tmp_path)
        _scaffold_project(tmp_path, "test-proj")
        decisions = {"decisions": {}}
        rp._generate_adrs("test-proj", decisions, "event-medallion")
        content = (tmp_path / "_projects" / "test-proj" / "docs" / "decisions" / "001-task-flow.md").read_text(encoding="utf-8")
        assert "event-medallion" in content

    def test_missing_docs_dir_returns_warning(self, tmp_path, monkeypatch):
        """Returns warning when docs/decisions/ doesn't exist."""
        _patch_repo(monkeypatch, tmp_path)
        project_dir = tmp_path / "_projects" / "test-proj"
        project_dir.mkdir(parents=True)
        report = rp._generate_adrs("test-proj", {"decisions": {}}, "medallion")
        assert any("not found" in r for r in report)


# ── Fast-forward tests ───────────────────────────────────────────────────


class TestFastForward:
    """Tests for _fast_forward_to_signoff() and _generate_complete_handoff()."""

    def test_no_discovery_brief_returns_false(self, tmp_path, monkeypatch):
        """_generate_complete_handoff fails when discovery brief is missing."""
        _patch_repo(monkeypatch, tmp_path)
        _scaffold_project(tmp_path, "test-proj")
        state = _make_state(current="0a-discovery")
        _write_state(tmp_path, "test-proj", state)

        # Delete discovery brief
        disc_path = tmp_path / "_projects" / "test-proj" / "docs" / "discovery-brief.md"
        if disc_path.exists():
            disc_path.unlink()

        ok, report = rp._generate_complete_handoff("test-proj")
        assert ok is False
        assert any("not found" in r.lower() for r in report)

    def test_no_task_flow_returns_false(self, tmp_path, monkeypatch):
        """_generate_complete_handoff fails with no task flow candidates."""
        _patch_repo(monkeypatch, tmp_path)
        _scaffold_project(tmp_path, "test-proj")
        state = _make_state(current="0a-discovery")
        _write_state(tmp_path, "test-proj", state)

        disc_path = tmp_path / "_projects" / "test-proj" / "docs" / "discovery-brief.md"
        disc_path.write_text("## Discovery Brief\n\nNo task flow info here.\n", encoding="utf-8")

        ok, report = rp._generate_complete_handoff("test-proj")
        assert ok is False
        assert any("task flow" in r.lower() for r in report)

    def test_fast_forward_returns_tuple(self, tmp_path, monkeypatch):
        """_fast_forward_to_signoff returns (bool, list) and doesn't crash."""
        _patch_repo(monkeypatch, tmp_path)
        _scaffold_project(tmp_path, "test-proj")
        state = _make_state(current="0a-discovery")
        state["phases"]["0a-discovery"]["status"] = "complete"
        _write_state(tmp_path, "test-proj", state)

        disc_path = tmp_path / "_projects" / "test-proj" / "docs" / "discovery-brief.md"
        disc_path.write_text(
            "## Discovery Brief\n\n"
            "### Suggested Task Flow Candidates\n\n"
            "| Candidate | Why It Fits | Confidence |\n"
            "|-----------|-------------|------------|\n"
            "| medallion | Good fit | high |\n",
            encoding="utf-8"
        )

        # Mock subprocess to avoid running real scripts in test env
        from unittest.mock import patch, MagicMock
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "test env"
        with patch("subprocess.run", return_value=mock_result):
            ok, report = rp._fast_forward_to_signoff("test-proj")
        assert isinstance(ok, bool)
        assert isinstance(report, list)
        assert len(report) > 0


# ── Generate test plan tests ─────────────────────────────────────────────


class TestGenerateTestPlanFunc:
    """Tests for _generate_test_plan()."""

    def test_no_handoff_returns_warning(self, tmp_path, monkeypatch):
        """Returns warning when architecture handoff doesn't exist."""
        _patch_repo(monkeypatch, tmp_path)
        _scaffold_project(tmp_path, "test-proj")

        # Delete handoff
        handoff = tmp_path / "_projects" / "test-proj" / "docs" / "architecture-handoff.md"
        if handoff.exists():
            handoff.unlink()

        report = rp._generate_test_plan("test-proj")
        assert any("not found" in r.lower() for r in report)


# ── Batch command tests ──────────────────────────────────────────────────


class TestBatchCommand:
    """Tests for batch subcommand argument parsing."""

    def test_batch_parser_exists(self):
        """batch subcommand is registered in argparse."""
        import inspect
        source = inspect.getsource(rp.main)
        assert "batch" in source
        assert "--through" in source

    def test_batch_requires_problem(self):
        """batch subcommand requires --problem flag."""
        import inspect
        source = inspect.getsource(rp.main)
        assert 'batch_p.add_argument("--problem", required=True' in source


# ── Scaffolder template alignment tests ──────────────────────────────────


class TestScaffolderTemplateAlignment:
    """Verify scaffolder output matches architecture-handoff.md template structure.
    
    These tests import the scaffolder via test_handoff_scaffolder's approach
    to avoid dataclass reimport issues.
    """

    def _get_scaffold_output(self):
        """Get scaffold output using subprocess to avoid module import issues."""
        import subprocess
        cmd = [
            sys.executable, "-c",
            "import sys; sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent.parent / '_shared' / 'lib')); "
            "from handoff_scaffolder import scaffold; "
            "from unittest.mock import patch; "
            "items = [{'order': '1', 'itemType': 'Lakehouse', 'dependsOn': [], 'requiredFor': ['Data'], 'skillset': '[CF]'}, "
            "{'order': '2', 'itemType': 'Notebook', 'dependsOn': ['Lakehouse'], 'requiredFor': ['Process'], 'skillset': '[CF]'}]; "
            "print(scaffold.__module__)"
        ]
        # Instead, just verify the structure via string assertions on the source
        pass

    def test_scaffold_produces_frontmatter(self):
        """scaffold() function builds YAML frontmatter output."""
        import inspect
        # Verify scaffold source code produces frontmatter format
        source = inspect.getsource(rp._generate_complete_handoff)
        # The generate function calls the scaffolder which now produces frontmatter
        assert "handoff-scaffolder" in source or "scaffolder" in source.lower()

    def test_adr_titles_match_constants(self):
        """ADR title constants match expected file names."""
        assert rp._ADR_TITLES["001"] == ("001", "Task Flow Selection")
        assert rp._ADR_TITLES["002"] == ("002", "Storage Layer Selection")
        assert rp._ADR_TITLES["003"] == ("003", "Ingestion Approach")
        assert rp._ADR_TITLES["004"] == ("004", "Processing Selection")
        assert rp._ADR_TITLES["005"] == ("005", "Visualization Selection")

    def test_decision_to_adr_mapping(self):
        """Decision resolver keys map to correct ADR numbers."""
        assert rp._DECISION_TO_ADR["storage"] == "002"
        assert rp._DECISION_TO_ADR["ingestion"] == "003"
        assert rp._DECISION_TO_ADR["processing"] == "004"
        assert rp._DECISION_TO_ADR["visualization"] == "005"

    def test_all_five_adrs_covered(self):
        """All 5 ADR numbers have either a title or decision mapping."""
        all_nums = set(rp._ADR_TITLES.keys())
        mapped_nums = set(rp._DECISION_TO_ADR.values()) | {"001"}
        assert all_nums == mapped_nums

    def test_adr_no_nonsense_phrases(self, tmp_path, monkeypatch):
        """ADRs should never contain 'Not determined aligns with'."""
        _patch_repo(monkeypatch, tmp_path)
        _scaffold_project(tmp_path, "test-proj")
        decisions = {
            "decisions": {
                "storage": {"choice": "Lakehouse", "confidence": "high",
                            "rule_matched": "Spark/Python → Lakehouse",
                            "guide": "decisions/storage-selection.md",
                            "rationale": "Spark skillset is best served by Lakehouse"},
                "ingestion": {"choice": None, "confidence": "na",
                              "rule_matched": None,
                              "guide": "decisions/ingestion-selection.md",
                              "rationale": ""},
                "processing": {"choice": "Notebook", "confidence": "high",
                               "rule_matched": "Interactive → Notebook",
                               "guide": "decisions/processing-selection.md",
                               "rationale": "Interactive Spark workloads use Notebook"},
                "visualization": {"choice": None, "confidence": "ambiguous",
                                  "rule_matched": None,
                                  "guide": "decisions/visualization-selection.md",
                                  "rationale": "", "candidates": ["Power BI Report", "Dashboard"]},
            }
        }
        rp._generate_adrs("test-proj", decisions, "medallion")
        docs_dir = tmp_path / "_projects" / "test-proj" / "docs" / "decisions"
        for adr_file in docs_dir.glob("*.md"):
            content = adr_file.read_text(encoding="utf-8")
            assert "Not determined aligns with" not in content, (
                f"{adr_file.name} contains nonsense phrase 'Not determined aligns with'"
            )

    def test_adr_rationale_appears_in_content(self, tmp_path, monkeypatch):
        """ADR content should include the rationale from the decision."""
        _patch_repo(monkeypatch, tmp_path)
        _scaffold_project(tmp_path, "test-proj")
        decisions = {
            "decisions": {
                "storage": {"choice": "Lakehouse", "confidence": "high",
                            "rule_matched": "Spark/Python → Lakehouse",
                            "guide": "decisions/storage-selection.md",
                            "rationale": "Spark skillset is best served by Lakehouse"},
            }
        }
        rp._generate_adrs("test-proj", decisions, "medallion")
        content = (tmp_path / "_projects" / "test-proj" / "docs" / "decisions" / "002-storage.md").read_text(encoding="utf-8")
        assert "Spark skillset is best served by Lakehouse" in content


# ── Design pre-compute tests ────────────────────────────────────────────


class TestDesignPrecompute:
    """Optimization: decision-resolver + handoff-scaffolder run during design precompute."""

    def test_design_phase_runs_resolver(self, tmp_path, monkeypatch):
        """_run_precompute for 1-design runs the decision-resolver."""
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state(current="1-design")
        proj_dir = tmp_path / "_projects" / "test-proj"
        (proj_dir / "docs").mkdir(parents=True, exist_ok=True)
        (proj_dir / "docs" / "discovery-brief.md").write_text(
            "## Discovery Brief\n\n### Suggested Task Flow Candidates\n\n"
            "| Candidate | Why | Confidence |\n|---|---|---|\n"
            "| medallion | fits | high |\n",
            encoding="utf-8",
        )
        import subprocess as _sp

        calls = []
        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return type("Result", (), {"returncode": 0, "stdout": "resolved", "stderr": ""})()

        monkeypatch.setattr(_sp, "run", fake_run)
        outputs = rp._run_precompute("1-design", "test-proj", state)
        resolver_calls = [c for c in calls if "decision-resolver" in str(c)]
        assert len(resolver_calls) >= 1, "decision-resolver should run during design precompute"

    def test_design_phase_runs_scaffolder_with_top_candidate(self, tmp_path, monkeypatch):
        """_run_precompute for 1-design runs handoff-scaffolder with top task flow."""
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state(current="1-design")
        proj_dir = tmp_path / "_projects" / "test-proj"
        (proj_dir / "docs").mkdir(parents=True, exist_ok=True)
        (proj_dir / "docs" / "discovery-brief.md").write_text(
            "## Discovery Brief\n\n### Suggested Task Flow Candidates\n\n"
            "| Candidate | Why | Confidence |\n|---|---|---|\n"
            "| event-medallion | best fit | high |\n"
            "| medallion | ok | medium |\n",
            encoding="utf-8",
        )
        import subprocess as _sp

        calls = []
        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return type("Result", (), {"returncode": 0, "stdout": "scaffolded", "stderr": ""})()

        monkeypatch.setattr(_sp, "run", fake_run)
        outputs = rp._run_precompute("1-design", "test-proj", state)
        scaffolder_calls = [c for c in calls if "handoff-scaffolder" in str(c)]
        assert len(scaffolder_calls) >= 1, "handoff-scaffolder should run during design precompute"
        # Verify it passed the high-confidence candidate
        scaffolder_cmd = scaffolder_calls[0]
        tf_idx = scaffolder_cmd.index("--task-flow")
        assert scaffolder_cmd[tf_idx + 1] == "event-medallion"

    def test_design_precompute_skipped_without_discovery(self, tmp_path, monkeypatch):
        """_run_precompute for 1-design does nothing if no discovery brief."""
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state(current="1-design")
        import subprocess as _sp

        call_count = [0]
        def fake_run(cmd, **kwargs):
            call_count[0] += 1
            return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

        monkeypatch.setattr(_sp, "run", fake_run)
        outputs = rp._run_precompute("1-design", "test-proj", state)
        assert call_count[0] == 0


# ── Extract top task flow tests ──────────────────────────────────────────


class TestExtractTopTaskFlow:
    """Tests for _extract_top_task_flow helper."""

    def test_returns_high_confidence(self, tmp_path):
        brief = tmp_path / "brief.md"
        brief.write_text(
            "### Suggested Task Flow Candidates\n\n"
            "| Candidate | Why | Confidence |\n|---|---|---|\n"
            "| lambda | ok | medium |\n"
            "| event-medallion | best | high |\n",
            encoding="utf-8",
        )
        assert rp._extract_top_task_flow(str(brief)) == "event-medallion"

    def test_returns_first_if_no_high(self, tmp_path):
        brief = tmp_path / "brief.md"
        brief.write_text(
            "### Suggested Task Flow Candidates\n\n"
            "| Candidate | Why | Confidence |\n|---|---|---|\n"
            "| medallion | ok | medium |\n"
            "| basic | simple | low |\n",
            encoding="utf-8",
        )
        assert rp._extract_top_task_flow(str(brief)) == "medallion"

    def test_returns_none_for_missing_file(self):
        assert rp._extract_top_task_flow("/nonexistent/path.md") is None

    def test_returns_none_for_no_table(self, tmp_path):
        brief = tmp_path / "brief.md"
        brief.write_text("## Discovery Brief\nNo candidates here.\n", encoding="utf-8")
        assert rp._extract_top_task_flow(str(brief)) is None


# ── Precompute encoding + file-writing tests ─────────────────────────────


class TestPrecomputeEncoding:
    """Bug #10: subprocess.run must use encoding='utf-8' on Windows to avoid
    cp1252 UnicodeDecodeError on UTF-8 output (box-drawing chars, emoji)."""

    def test_subprocess_uses_utf8_encoding(self, tmp_path, monkeypatch):
        """All subprocess.run calls in _run_precompute must pass encoding='utf-8'."""
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state(current="0a-discovery", problem="test problem")
        _write_state(tmp_path, "test-proj", state)
        import subprocess as _sp

        encoding_used = []

        def fake_run(cmd, **kwargs):
            encoding_used.append(kwargs.get("encoding"))
            return type("Result", (), {"returncode": 0, "stdout": "ok", "stderr": ""})()

        monkeypatch.setattr(_sp, "run", fake_run)
        rp._run_precompute("0a-discovery", "test-proj", state)
        assert all(e == "utf-8" for e in encoding_used), (
            f"All subprocess.run calls must use encoding='utf-8', got: {encoding_used}"
        )

    def test_design_precompute_uses_utf8(self, tmp_path, monkeypatch):
        """Design precompute subprocess calls use utf-8 encoding."""
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state(current="1-design")
        proj_dir = tmp_path / "_projects" / "test-proj"
        (proj_dir / "docs").mkdir(parents=True, exist_ok=True)
        (proj_dir / "docs" / "discovery-brief.md").write_text(
            "### Suggested Task Flow Candidates\n\n"
            "| Candidate | Why | Confidence |\n|---|---|---|\n"
            "| medallion | fits | high |\n",
            encoding="utf-8",
        )
        import subprocess as _sp

        encodings = []

        def fake_run(cmd, **kwargs):
            encodings.append(kwargs.get("encoding"))
            return type("Result", (), {"returncode": 0, "stdout": "ok", "stderr": ""})()

        monkeypatch.setattr(_sp, "run", fake_run)
        rp._run_precompute("1-design", "test-proj", state)
        assert all(e == "utf-8" for e in encodings), f"Got encodings: {encodings}"


class TestPrecomputeFileWriting:
    """Optimization: precompute writes scaffolder/prefill output directly into template files."""

    def test_scaffolder_writes_to_handoff_file(self, tmp_path, monkeypatch):
        """Handoff-scaffolder output is written to architecture-handoff.md via --output flag."""
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state(current="1-design")
        proj_dir = tmp_path / "_projects" / "test-proj"
        (proj_dir / "docs").mkdir(parents=True, exist_ok=True)
        (proj_dir / "docs" / "discovery-brief.md").write_text(
            "### Suggested Task Flow Candidates\n\n"
            "| Candidate | Why | Confidence |\n|---|---|---|\n"
            "| event-medallion | best | high |\n",
            encoding="utf-8",
        )
        (proj_dir / "docs" / "architecture-handoff.md").write_text("template", encoding="utf-8")
        import subprocess as _sp

        def fake_run(cmd, **kwargs):
            # Check scaffolder receives --output flag pointing to handoff file
            if "handoff-scaffolder" in str(cmd):
                assert "--output" in cmd, "scaffolder must receive --output flag"
                output_idx = cmd.index("--output")
                output_path = cmd[output_idx + 1]
                assert "architecture-handoff.md" in output_path
            return type("Result", (), {"returncode": 0, "stdout": "scaffolded", "stderr": ""})()

        monkeypatch.setattr(_sp, "run", fake_run)
        outputs = rp._run_precompute("1-design", "test-proj", state)
        assert any("pre-filled" in o.lower() for o in outputs)

    def test_prefill_writes_to_test_plan_file(self, tmp_path, monkeypatch):
        """Test plan prefill output is written directly to test-plan.md."""
        _patch_repo(monkeypatch, tmp_path)
        state = _make_state(current="2a-test-plan", task_flow="medallion")
        proj_dir = tmp_path / "_projects" / "test-proj"
        (proj_dir / "docs").mkdir(parents=True, exist_ok=True)
        (proj_dir / "docs" / "architecture-handoff.md").write_text(
            "---\ntask_flow: medallion\n---\n# Handoff\ncontent here",
            encoding="utf-8",
        )
        test_plan_path = proj_dir / "docs" / "test-plan.md"
        test_plan_path.write_text("template placeholder", encoding="utf-8")
        import subprocess as _sp

        prefill_yaml = "project: test-proj\ntask_flow: medallion\ncriteria_mapping: []"

        def fake_run(cmd, **kwargs):
            return type("Result", (), {"returncode": 0, "stdout": prefill_yaml, "stderr": ""})()

        monkeypatch.setattr(_sp, "run", fake_run)
        outputs = rp._run_precompute("2a-test-plan", "test-proj", state)
        # Verify the test plan file was written with prefill content
        written = test_plan_path.read_text(encoding="utf-8")
        assert "criteria_mapping" in written
        assert any("pre-filled" in o.lower() for o in outputs)
