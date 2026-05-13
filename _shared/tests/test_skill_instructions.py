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


# ── Auto-chain instructions ──────────────────────────────────────────────


class TestAutoChainInstructions:
    """Bug #2 regression: Auto-chain handoff instructions must exist in the
    shared copilot-instructions.md (injected into all skill contexts)."""

    COPILOT_INSTRUCTIONS = (REPO_ROOT / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")

    def test_auto_chain_instruction_present(self):
        assert "AUTO-CHAIN" in self.COPILOT_INSTRUCTIONS, (
            "copilot-instructions.md must contain AUTO-CHAIN instruction"
        )

    def test_human_gate_instruction_present(self):
        assert "HUMAN GATE" in self.COPILOT_INSTRUCTIONS, (
            "copilot-instructions.md must reference HUMAN GATE"
        )

    def test_advance_command_present(self):
        assert "run-pipeline.py advance" in self.COPILOT_INSTRUCTIONS, (
            "copilot-instructions.md must include advance command"
        )
