"""Tests for SKILL.md instruction files — verifies critical content that prevents
pipeline regressions (re-ask bugs, template predictability, auto-chain instructions)."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = REPO_ROOT / ".github" / "skills"


# ── Helper ────────────────────────────────────────────────────────────────


def _read_skill(skill_name: str) -> str:
    path = SKILLS_DIR / skill_name / "SKILL.md"
    assert path.exists(), f"SKILL.md not found for {skill_name}"
    return path.read_text(encoding="utf-8")


# ── Discovery: re-run detection ──────────────────────────────────────────


class TestDiscoverRerunDetection:
    """Bug #8: Discovery SKILL.md must instruct agents to reuse problem
    statement and project name when already provided in the prompt context,
    rather than re-asking the user."""

    def test_reuse_instruction_present(self):
        content = _read_skill("fabric-discover")
        assert "already provided" in content.lower(), (
            "Discovery SKILL.md must instruct agent to reuse problem/name "
            "when already provided in the prompt"
        )

    def test_no_unconditional_ask(self):
        """Step 1 should NOT start with an unconditional 'Ask the user for'
        — it must have a conditional check first."""
        content = _read_skill("fabric-discover")
        lines = content.split("\n")
        step1_idx = None
        for i, line in enumerate(lines):
            if "### Step 1" in line and "Collect Intake" in line:
                step1_idx = i
                break
        assert step1_idx is not None, "Step 1: Collect Intake not found"
        # The line immediately after the heading should NOT be "Ask the user"
        next_content_line = None
        for line in lines[step1_idx + 1 :]:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                next_content_line = stripped
                break
        assert next_content_line is not None
        assert not next_content_line.lower().startswith("ask the user"), (
            "Step 1 must have a conditional re-use check before 'Ask the user'"
        )


# ── Design: ADR template reference ───────────────────────────────────────


class TestDesignADRTemplateReference:
    """Bug #9: Design SKILL.md must document the exact ADR file titles so
    agents can construct edit old_str without viewing each file first."""

    ADR_FILES = {
        "001-task-flow.md": "ADR-001: Task Flow Selection",
        "002-storage.md": "ADR-002: Storage Layer Selection",
        "003-ingestion.md": "ADR-003: Ingestion Approach",
        "004-processing.md": "ADR-004: Processing Selection",
        "005-visualization.md": "ADR-005: Visualization Selection",
    }

    def test_all_adr_titles_documented(self):
        content = _read_skill("fabric-design")
        for filename, title in self.ADR_FILES.items():
            assert title in content, (
                f"Design SKILL.md must document ADR title '{title}' "
                f"so agents can predict old_str for {filename}"
            )

    def test_all_adr_filenames_documented(self):
        content = _read_skill("fabric-design")
        for filename in self.ADR_FILES:
            assert filename in content, (
                f"Design SKILL.md must reference filename '{filename}'"
            )

    def test_template_body_documented(self):
        """The template body must be included so agents know the exact
        old_str to use for replacement."""
        content = _read_skill("fabric-design")
        # Key template markers that must be present
        assert "<!-- /fabric-document: date -->" in content
        assert "<!-- /fabric-document: what was chosen -->" in content
        assert "<!-- /fabric-document: link to decisions/*.md -->" in content

    def test_adr_titles_match_scaffolder(self):
        """ADR titles in SKILL.md must match what new-project.py scaffolds."""
        import importlib.util
        import sys

        np_path = REPO_ROOT / "_shared" / "scripts" / "new-project.py"
        spec = importlib.util.spec_from_file_location("new_project", str(np_path))
        mod = importlib.util.module_from_spec(spec)
        sys.modules["new_project"] = mod
        spec.loader.exec_module(mod)

        for _filename, title in self.ADR_FILES.items():
            number = title.split("-")[1].split(":")[0]
            title_text = title.split(": ", 1)[1]
            generated = mod.adr_template(number, title_text)
            assert f"# ADR-{number}: {title_text}" in generated


# ── Auto-chain instructions ──────────────────────────────────────────────


class TestAutoChainInstructions:
    """Bug #2 regression: All 5 skill SKILL.md files must contain auto-chain
    instructions in their Handoff section."""

    SKILLS = [
        "fabric-discover",
        "fabric-design",
        "fabric-test",
        "fabric-deploy",
        "fabric-document",
    ]

    @pytest.mark.parametrize("skill_name", SKILLS)
    def test_auto_chain_instruction_present(self, skill_name):
        content = _read_skill(skill_name)
        assert "AUTO-CHAIN" in content, (
            f"{skill_name}/SKILL.md must contain AUTO-CHAIN instruction in Handoff"
        )

    @pytest.mark.parametrize("skill_name", SKILLS)
    def test_human_gate_instruction_present(self, skill_name):
        content = _read_skill(skill_name)
        assert "HUMAN GATE" in content, (
            f"{skill_name}/SKILL.md must reference HUMAN GATE in Handoff"
        )

    @pytest.mark.parametrize("skill_name", SKILLS)
    def test_advance_command_present(self, skill_name):
        content = _read_skill(skill_name)
        assert "run-pipeline.py advance" in content, (
            f"{skill_name}/SKILL.md must include advance command in Handoff"
        )
