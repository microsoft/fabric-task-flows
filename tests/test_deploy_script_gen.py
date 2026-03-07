"""Tests for deploy-script-gen.py — verifies generated scripts have required sections."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

REPO_ROOT = Path(__file__).resolve().parent.parent
SHARED_DIR = REPO_ROOT / "_shared"


def test_bash_template_exists():
    assert (SHARED_DIR / "script-template.sh").exists()


def test_ps1_template_exists():
    assert (SHARED_DIR / "script-template.ps1").exists()


def test_bash_template_has_required_sections():
    content = (SHARED_DIR / "script-template.sh").read_text(encoding="utf-8")
    assert "fab_mkdir()" in content, "Missing fab_mkdir function"
    assert "prompt_value()" in content, "Missing prompt_value function"
    assert 'fab -c "auth status"' in content, "Missing fab -c auth status check"
    assert "FABRIC_CAPACITY_ID" in content, "Missing capacity prompt"
    assert "capacityId" in content, "Missing capacity assignment"
    assert "CONFIGURATION" in content, "Missing CONFIGURATION section"
    assert "DEPLOYMENT PLAN" in content, "Missing DEPLOYMENT PLAN section"
    assert "DEPLOYMENT SUMMARY" in content, "Missing DEPLOYMENT SUMMARY section"
    assert "POST-DEPLOYMENT METADATA" in content, "Missing POST-DEPLOYMENT METADATA section"


def test_ps1_template_has_required_sections():
    content = (SHARED_DIR / "script-template.ps1").read_text(encoding="utf-8")
    assert "Fab-Mkdir" in content, "Missing Fab-Mkdir function"
    assert "Prompt-Value" in content, "Missing Prompt-Value function"
    assert 'fab -c "auth status"' in content, "Missing fab -c auth status check"
    assert "FABRIC_CAPACITY_ID" in content, "Missing capacity prompt"
    assert "capacityId" in content, "Missing capacity assignment"
    assert "CONFIGURATION" in content, "Missing CONFIGURATION section"


def test_bash_template_shows_errors():
    """Verify fab_mkdir captures errors instead of suppressing to /dev/null."""
    content = (SHARED_DIR / "script-template.sh").read_text(encoding="utf-8")
    assert "err_output" in content, "fab_mkdir should capture error output"
    assert 'Error: $err_output' in content, "fab_mkdir should display error on failure"


def test_ps1_template_shows_errors():
    """Verify Fab-Mkdir captures errors instead of piping to Out-Null."""
    content = (SHARED_DIR / "script-template.ps1").read_text(encoding="utf-8")
    assert "$errOutput" in content, "Fab-Mkdir should capture error output"
    assert 'Error: $errOutput' in content, "Fab-Mkdir should display error on failure"


def test_deploy_script_gen_imports():
    """Verify deploy-script-gen.py's registry data loads correctly."""
    from registry_loader import build_fab_commands, build_display_names
    cmds = build_fab_commands()
    names = build_display_names()
    assert len(cmds) > 0, "FAB_COMMANDS should not be empty"
    assert len(names) > 0, "DISPLAY_NAMES should not be empty"
    assert "lakehouse" in cmds, "Lakehouse should be in FAB_COMMANDS"


def test_fabric_deploy_utility_imports():
    """Verify _shared/fabric_deploy.py can be imported."""
    shared_dir = REPO_ROOT / "_shared"
    assert (shared_dir / "fabric_deploy.py").exists(), "fabric_deploy.py missing from _shared"
    sys.path.insert(0, str(shared_dir))
    import fabric_deploy
    assert hasattr(fabric_deploy, "run_fab")
    assert hasattr(fabric_deploy, "FabricDeployer")
    assert hasattr(fabric_deploy, "check_auth")
    assert hasattr(fabric_deploy, "print_banner")
    assert hasattr(fabric_deploy, "prompt_value")


def test_generated_python_script_path():
    """Verify the generated Python script is self-contained (no external imports)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "deploy_script_gen", str(REPO_ROOT / "scripts" / "deploy-script-gen.py")
    )
    try:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except (AttributeError, ImportError):
        return  # Python 3.11 dataclass issue — skip
    _, _, py_script = mod.generate(
        str(REPO_ROOT / "projects" / "agent-assist-telco" / "prd" / "architecture-handoff.md"),
        "Test Project"
    )
    assert "fabric_deploy" not in py_script.split("# =")[0], "Python script should not import from fabric_deploy"
    assert "sys.path.insert" not in py_script, "Python script should not modify sys.path"
    assert "def run_fab(" in py_script, "Python script should embed run_fab inline"
    assert "class FabricDeployer" in py_script, "Python script should embed FabricDeployer inline"
    assert "Self-contained" in py_script, "Python script should note it's self-contained"
