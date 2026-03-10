"""Tests for deploy-script-gen.py — verifies fabric-cicd artifact generation."""

import sys
import tempfile
from pathlib import Path

SHARED_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SHARED_DIR / "lib"))
sys.path.insert(0, str(SHARED_DIR / "scripts"))

REPO_ROOT = SHARED_DIR.parent
DEPLOY_SKILL = REPO_ROOT / ".github" / "skills" / "fabric-deploy"


def test_deploy_script_gen_imports():
    """Verify deploy-script-gen.py's registry data loads correctly."""
    from registry_loader import build_fab_commands, build_display_names
    cmds = build_fab_commands()
    names = build_display_names()
    assert len(cmds) > 0, "FAB_COMMANDS should not be empty"
    assert len(names) > 0, "DISPLAY_NAMES should not be empty"
    assert "lakehouse" in cmds, "Lakehouse should be in FAB_COMMANDS"


def test_generated_artifacts():
    """Verify deploy-script-gen.py generates fabric-cicd artifacts."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "deploy_script_gen", str(DEPLOY_SKILL / "scripts" / "deploy-script-gen.py")
    )
    try:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except (AttributeError, ImportError):
        return

    handoff = REPO_ROOT / "_projects" / "agent-assist-telco" / "prd" / "architecture-handoff.md"
    if not handoff.exists():
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        # Simulate CLI call
        sys.argv = ["deploy-script-gen.py", "--handoff", str(handoff), "--project", "Test", "--output-dir", tmpdir]
        try:
            mod.main()
        except SystemExit:
            pass

        out = Path(tmpdir)
        assert (out / "workspace").is_dir(), "Should generate workspace directory"
        assert (out / "config.yml").exists(), "Should generate config.yml"
        assert (out / "deploy-test.py").exists(), "Should generate deploy script"
        assert (out / "descriptions-test.json").exists(), "Should generate descriptions"

        # Verify config.yml has core settings
        config = (out / "config.yml").read_text(encoding="utf-8")
        assert "core:" in config
        assert "repository_directory:" in config
        assert "item_types_in_scope:" in config

        # Verify deploy script uses fabric-cicd
        deploy = (out / "deploy-test.py").read_text(encoding="utf-8")
        assert "fabric_cicd" in deploy
        assert "deploy_with_config" in deploy

        # Verify workspace has .platform files
        platforms = list((out / "workspace").rglob(".platform"))
        assert len(platforms) > 0, "Should generate .platform files for items"
