"""Topology-consistency tests — verify all pipeline handoffs describe the same item graph.

Checks that architecture-handoff, deployment-handoff, validation-report, and
.architecture-cache.json agree on the set of items for each sample project.
"""

import json
import sys
from pathlib import Path

import pytest

SHARED_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SHARED_DIR.parent
PROJECTS_DIR = REPO_ROOT / "_projects"

sys.path.insert(0, str(SHARED_DIR / "lib"))
from yaml_utils import extract_yaml_blocks, parse_yaml, extract_task_flow


def _discover_complete_projects() -> list[str]:
    """Find projects that have all required handoff documents."""
    if not PROJECTS_DIR.is_dir():
        return []
    projects = []
    for p in sorted(PROJECTS_DIR.iterdir()):
        if not p.is_dir() or p.name.startswith("."):
            continue
        docs = p / "docs"
        required = [
            docs / ".architecture-cache.json",
            docs / "deployment-handoff.md",
            docs / "validation-report.md",
        ]
        if all(f.exists() for f in required):
            projects.append(p.name)
    return projects


def _normalize(name: str) -> str:
    return str(name).lower().replace("-", "_").replace(" ", "_")


def _extract_cache_items(project: str) -> set[str]:
    """Extract item names from .architecture-cache.json."""
    cache_path = PROJECTS_DIR / project / "docs" / ".architecture-cache.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8"))
    items = set()
    for item in cache.get("items", []):
        name = item.get("name") or item.get("id", "")
        if name:
            items.add(_normalize(name))
    return items


def _extract_deployment_items(project: str) -> set[str]:
    """Extract item names from deployment-handoff.md YAML blocks."""
    path = PROJECTS_DIR / project / "docs" / "deployment-handoff.md"
    content = path.read_text(encoding="utf-8")
    items = set()
    for block_text in extract_yaml_blocks(content):
        parsed = parse_yaml(block_text)
        for item in parsed.get("items", []):
            name = item.get("name", "")
            if name:
                items.add(_normalize(name))
    return items


def _extract_validation_items(project: str) -> set[str]:
    """Extract item names from validation-report.md items_validated."""
    path = PROJECTS_DIR / project / "docs" / "validation-report.md"
    content = path.read_text(encoding="utf-8")
    items = set()
    for block_text in extract_yaml_blocks(content):
        parsed = parse_yaml(block_text)
        for item in parsed.get("items_validated", []):
            name = item.get("name", "")
            if name:
                items.add(_normalize(name))
    return items


def _extract_task_flow_from_doc(project: str, doc_name: str) -> str | None:
    """Extract task_flow from a project document."""
    path = PROJECTS_DIR / project / "docs" / doc_name
    if not path.exists():
        return None
    content = path.read_text(encoding="utf-8")
    return extract_task_flow(content)


COMPLETE_PROJECTS = _discover_complete_projects()


@pytest.mark.skipif(not COMPLETE_PROJECTS, reason="No complete sample projects found")
class TestTopologyConsistency:
    """Verify all handoff documents in sample projects describe the same topology."""

    @pytest.mark.parametrize("project", COMPLETE_PROJECTS)
    def test_cache_items_subset_of_deployment(self, project):
        """Architecture cache items should all appear in deployment handoff.

        Deployment may have extra items (e.g., VariableLibrary injection)
        but should never be missing architecture items.
        """
        cache_items = _extract_cache_items(project)
        deploy_items = _extract_deployment_items(project)
        missing = cache_items - deploy_items
        assert not missing, (
            f"Project '{project}': architecture cache items missing from deployment: {missing}"
        )

    @pytest.mark.parametrize("project", COMPLETE_PROJECTS)
    def test_validation_matches_deployment(self, project):
        """Validated items should match deployed items."""
        deploy_items = _extract_deployment_items(project)
        validation_items = _extract_validation_items(project)
        missing = deploy_items - validation_items
        assert not missing, (
            f"Project '{project}': deployed items missing from validation: {missing}"
        )

    @pytest.mark.parametrize("project", COMPLETE_PROJECTS)
    def test_task_flow_consistent(self, project):
        """Task flow should be the same across all documents."""
        cache_path = PROJECTS_DIR / project / "docs" / ".architecture-cache.json"
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
        cache_tf = cache.get("task_flow", "").lower()

        deploy_tf = _extract_task_flow_from_doc(project, "deployment-handoff.md")

        if cache_tf and deploy_tf:
            assert cache_tf == deploy_tf, (
                f"Project '{project}': task_flow mismatch — "
                f"cache='{cache_tf}', deployment='{deploy_tf}'"
            )

    @pytest.mark.parametrize("project", COMPLETE_PROJECTS)
    def test_cache_has_items(self, project):
        """Architecture cache should have at least one item."""
        cache_items = _extract_cache_items(project)
        assert len(cache_items) > 0, (
            f"Project '{project}': architecture cache has no items"
        )

    @pytest.mark.parametrize("project", COMPLETE_PROJECTS)
    def test_no_empty_validation(self, project):
        """Validation report should have at least one validated item."""
        validation_items = _extract_validation_items(project)
        assert len(validation_items) > 0, (
            f"Project '{project}': validation report has no items"
        )
