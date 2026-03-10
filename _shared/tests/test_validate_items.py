"""Tests for validate-items.py — verifies Fabric item validation via REST API."""

import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

SHARED_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SHARED_DIR / "lib"))

REPO_ROOT = SHARED_DIR.parent
SCRIPT_PATH = (
    REPO_ROOT / ".github" / "skills" / "fabric-test" / "scripts" / "validate-items.py"
)

# Ensure azure.identity and requests are available (mock if missing)
_mocked_azure = False
_mocked_requests = False

if "azure.identity" not in sys.modules:
    _azure_pkg = types.ModuleType("azure")
    _azure_pkg.__path__ = []
    _azure_id = types.ModuleType("azure.identity")
    _azure_id.DefaultAzureCredential = MagicMock
    sys.modules["azure"] = _azure_pkg
    sys.modules["azure.identity"] = _azure_id
    _mocked_azure = True

if "requests" not in sys.modules:
    _req = types.ModuleType("requests")
    _req.RequestException = type("RequestException", (Exception,), {})
    _req.get = MagicMock()
    sys.modules["requests"] = _req
    _mocked_requests = True

# Now import the module
_spec = importlib.util.spec_from_file_location("validate_items", str(SCRIPT_PATH))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

_parse_handoff = _mod._parse_handoff
_build_api_path_map = _mod._build_api_path_map
_build_portal_only = _mod._build_portal_only
_build_phase_map = _mod._build_phase_map
_get_phase = _mod._get_phase
FabricApiClient = _mod.FabricApiClient
_load_registry = _mod._load_registry


# ── Mock registry data ─────────────────────────────────────────────

MOCK_REGISTRY = {
    "Lakehouse": {
        "fab_type": "Lakehouse",
        "api_path": "lakehouses",
        "display_name": "Lakehouse",
        "phase": "Foundation",
        "aliases": ["lakehouse"],
        "rest_api": {"creatable": True, "definition": True},
    },
    "Notebook": {
        "fab_type": "Notebook",
        "api_path": "notebooks",
        "display_name": "Notebook",
        "phase": "Transformation",
        "aliases": ["notebook"],
        "rest_api": {"creatable": True, "definition": True},
    },
    "Activator": {
        "fab_type": "Activator",
        "api_path": "",
        "display_name": "Activator (Reflex)",
        "phase": "Other",
        "aliases": ["reflex"],
        "rest_api": {"creatable": False},
    },
}


# ── _build_api_path_map tests ──────────────────────────────────────


class TestBuildApiPathMap:
    def test_maps_canonical_name(self):
        result = _build_api_path_map(MOCK_REGISTRY)
        assert result["Lakehouse"] == "lakehouses"
        assert result["Notebook"] == "notebooks"

    def test_maps_fab_type(self):
        result = _build_api_path_map(MOCK_REGISTRY)
        assert result["Lakehouse"] == "lakehouses"

    def test_maps_display_name(self):
        result = _build_api_path_map(MOCK_REGISTRY)
        # Activator has empty api_path so it's skipped entirely
        assert "Activator (Reflex)" not in result
        assert result["Notebook"] == "notebooks"

    def test_maps_aliases(self):
        result = _build_api_path_map(MOCK_REGISTRY)
        assert result["lakehouse"] == "lakehouses"
        assert result["notebook"] == "notebooks"

    def test_skips_empty_api_path(self):
        result = _build_api_path_map(MOCK_REGISTRY)
        # Activator has empty api_path, so it shouldn't be in the map
        assert "Activator" not in result


# ── _build_portal_only tests ───────────────────────────────────────


class TestBuildPortalOnly:
    def test_includes_non_creatable(self):
        result = _build_portal_only(MOCK_REGISTRY)
        assert "Activator" in result
        assert "reflex" in result

    def test_excludes_creatable(self):
        result = _build_portal_only(MOCK_REGISTRY)
        assert "Lakehouse" not in result
        assert "Notebook" not in result


# ── _build_phase_map tests ─────────────────────────────────────────


class TestBuildPhaseMap:
    def test_maps_canonical_name(self):
        result = _build_phase_map(MOCK_REGISTRY)
        assert result["Lakehouse"] == "Foundation"
        assert result["Notebook"] == "Transformation"

    def test_maps_aliases(self):
        result = _build_phase_map(MOCK_REGISTRY)
        assert result["lakehouse"] == "Foundation"

    def test_tbd_becomes_other(self):
        reg = {
            "TestType": {
                "fab_type": "TestType",
                "display_name": "TestType",
                "phase": "TBD",
                "aliases": [],
            }
        }
        result = _build_phase_map(reg)
        assert result["TestType"] == "Other"


# ── _get_phase tests ───────────────────────────────────────────────


class TestGetPhase:
    def test_known_type(self):
        pm = {"Lakehouse": "Foundation", "Notebook": "Transformation"}
        assert _get_phase("Lakehouse", pm) == "Foundation"

    def test_unknown_type_returns_other(self):
        assert _get_phase("UnknownType", {}) == "Other"


# ── _parse_handoff tests ──────────────────────────────────────────


SAMPLE_DEPLOYMENT_HANDOFF = """\
# Deployment Handoff

project: "Test Project"
task_flow: "medallion"
workspace: "test-workspace-dev"

items_deployed:
  - name: bronze-lakehouse
    type: Lakehouse
    wave: 1
    status: deployed
  - name: transform-notebook
    type: Notebook
    wave: 2
    status: deployed
  - name: failed-item
    type: Report
    wave: 3
    status: failed
"""

INLINE_DEPLOYMENT_HANDOFF = """\
project: "Inline Test"
task_flow: "lambda"
workspace: "inline-ws"

items:
  - { name: lh-bronze, type: Lakehouse, wave: 1, status: deployed }
  - { name: nb-silver, type: Notebook, wave: 2, status: deployed }
"""


class TestParseHandoff:
    def test_extracts_project(self, tmp_path):
        f = tmp_path / "handoff.md"
        f.write_text(SAMPLE_DEPLOYMENT_HANDOFF, encoding="utf-8")
        project, task_flow, workspace, items = _parse_handoff(str(f))
        assert project == "Test Project"

    def test_extracts_task_flow(self, tmp_path):
        f = tmp_path / "handoff.md"
        f.write_text(SAMPLE_DEPLOYMENT_HANDOFF, encoding="utf-8")
        _, task_flow, _, _ = _parse_handoff(str(f))
        assert task_flow == "medallion"

    def test_extracts_workspace(self, tmp_path):
        f = tmp_path / "handoff.md"
        f.write_text(SAMPLE_DEPLOYMENT_HANDOFF, encoding="utf-8")
        _, _, workspace, _ = _parse_handoff(str(f))
        assert workspace == "test-workspace-dev"

    def test_extracts_items(self, tmp_path):
        f = tmp_path / "handoff.md"
        f.write_text(SAMPLE_DEPLOYMENT_HANDOFF, encoding="utf-8")
        _, _, _, items = _parse_handoff(str(f))
        assert len(items) == 3
        names = [i["name"] for i in items]
        assert "bronze-lakehouse" in names
        assert "transform-notebook" in names

    def test_extracts_item_status(self, tmp_path):
        f = tmp_path / "handoff.md"
        f.write_text(SAMPLE_DEPLOYMENT_HANDOFF, encoding="utf-8")
        _, _, _, items = _parse_handoff(str(f))
        statuses = {i["name"]: i["status"] for i in items}
        assert statuses["bronze-lakehouse"] == "deployed"
        assert statuses["failed-item"] == "failed"

    def test_inline_format(self, tmp_path):
        f = tmp_path / "handoff.md"
        f.write_text(INLINE_DEPLOYMENT_HANDOFF, encoding="utf-8")
        project, task_flow, workspace, items = _parse_handoff(str(f))
        assert project == "Inline Test"
        assert workspace == "inline-ws"
        assert len(items) == 2
        assert items[0]["name"] == "lh-bronze"


# ── Validation result structure ────────────────────────────────────


class TestValidationResultStructure:
    """Verify the expected shape of validation output fields."""

    def test_registry_loads(self):
        reg = _load_registry()
        assert isinstance(reg, dict)
        assert len(reg) > 0

    def test_api_path_map_from_real_registry(self):
        reg = _load_registry()
        api_map = _build_api_path_map(reg)
        assert "Lakehouse" in api_map
        assert api_map["Lakehouse"] == "lakehouses"

    def test_portal_only_from_real_registry(self):
        reg = _load_registry()
        portal = _build_portal_only(reg)
        assert isinstance(portal, set)

    def test_phase_map_from_real_registry(self):
        reg = _load_registry()
        pm = _build_phase_map(reg)
        assert pm.get("Lakehouse") == "Foundation"


# ── FabricApiClient tests (mocked HTTP) ────────────────────────────


class TestFabricApiClient:
    def test_item_exists_returns_true_when_found(self):
        client = FabricApiClient()
        # Pre-populate cache to avoid actual HTTP calls
        client._items_cache["ws-123:lakehouses"] = {"bronze-lh": "item-id-1"}
        assert client.item_exists("ws-123", "lakehouses", "bronze-lh")

    def test_item_exists_returns_false_when_missing(self):
        client = FabricApiClient()
        client._items_cache["ws-123:lakehouses"] = {"bronze-lh": "item-id-1"}
        assert not client.item_exists("ws-123", "lakehouses", "missing-item")

    def test_item_exists_case_insensitive(self):
        client = FabricApiClient()
        client._items_cache["ws-123:lakehouses"] = {"bronze-lh": "item-id-1"}
        assert client.item_exists("ws-123", "lakehouses", "Bronze-LH")

    def test_workspace_cache_hit(self):
        client = FabricApiClient()
        client._workspace_cache["my-workspace"] = "ws-id-123"
        result = client.resolve_workspace_id("my-workspace")
        assert result == "ws-id-123"
