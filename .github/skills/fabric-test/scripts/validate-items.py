#!/usr/bin/env python3
"""
Fabric Task Flows — Validation Script (Python, no fab CLI dependency)

Parses a deployment-handoff.md, verifies each deployed item exists via the
Fabric REST API, and outputs a pre-filled validation-report.md YAML block
to stdout.

Authentication uses the same DefaultAzureCredential + requests pattern as the
generated deploy scripts — these are transitive dependencies of fabric-cicd,
not additional installs.

Usage:
    python validate-items.py <deployment-handoff.md>
    python validate-items.py <deployment-handoff.md> --workspace my-ws-dev
    python validate-items.py <deployment-handoff.md> > validation-report.yaml

Dependencies (already installed via fabric-cicd):
    azure-identity, requests
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from azure.identity import DefaultAzureCredential
except ImportError:
    print("ERROR: azure-identity not installed. Run: pip install azure-identity", file=sys.stderr)
    sys.exit(2)

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(2)

# ---------------------------------------------------------------------------
# Load item type metadata from registry
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
REGISTRY_PATH = REPO_ROOT / "_shared" / "item-type-registry.json"

def _load_registry() -> dict:
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        return json.load(f)["types"]


def _build_api_path_map(registry: dict) -> dict[str, str]:
    """Map item type variants → REST API path (e.g., 'Lakehouse' → 'lakehouses')."""
    result: dict[str, str] = {}
    for canonical, data in registry.items():
        api_path = data.get("api_path", "")
        if not api_path:
            continue
        result[canonical] = api_path
        result[data["fab_type"]] = api_path
        result[data["display_name"]] = api_path
        for alias in data.get("aliases", []):
            result[alias] = api_path
            # Title-case variant
            parts = alias.split()
            if len(parts) > 1:
                result[" ".join(w.capitalize() for w in parts)] = api_path
    return result


def _build_portal_only(registry: dict) -> set[str]:
    """Set of type names that cannot be created via REST API."""
    result: set[str] = set()
    for canonical, data in registry.items():
        if not data.get("rest_api", {}).get("creatable", False):
            result.add(canonical)
            result.add(data["fab_type"])
            result.add(data["display_name"])
            for alias in data.get("aliases", []):
                result.add(alias)
    return result


# ---------------------------------------------------------------------------
# Phase assignment (mirrors shell script logic)
# ---------------------------------------------------------------------------

PHASE_MAP = {
    "Lakehouse": "Foundation", "Warehouse": "Foundation", "Eventhouse": "Foundation",
    "SQLDatabase": "Foundation", "KQLDatabase": "Foundation", "CosmosDB": "Foundation",
    "Environment": "Environment",
    "CopyJob": "Ingestion", "Eventstream": "Ingestion", "DataPipeline": "Ingestion",
    "Pipeline": "Ingestion", "Dataflow": "Ingestion", "Mirroring": "Ingestion",
    "Notebook": "Transformation", "SparkJobDefinition": "Transformation",
    "KQLQueryset": "Transformation",
    "SemanticModel": "Visualization", "Report": "Visualization",
    "Dashboard": "Visualization", "RealTimeDashboard": "Visualization",
    "KQLDashboard": "Visualization",
    "MLExperiment": "ML", "MLModel": "ML",
}

def _get_phase(item_type: str) -> str:
    return PHASE_MAP.get(item_type, "Other")


# ---------------------------------------------------------------------------
# Fabric REST API client
# ---------------------------------------------------------------------------

FABRIC_API_BASE = "https://api.fabric.microsoft.com/v1"
FABRIC_SCOPE = "https://api.fabric.microsoft.com/.default"


class FabricApiClient:
    """Thin wrapper around the Fabric REST API for item existence checks."""

    def __init__(self):
        self._credential = DefaultAzureCredential()
        self._token: str | None = None
        self._workspace_cache: dict[str, str] = {}   # name → id
        self._items_cache: dict[str, dict[str, str]] = {}  # (ws_id, api_path) → {name: id}

    def _get_token(self) -> str:
        token = self._credential.get_token(FABRIC_SCOPE)
        self._token = token.token
        return self._token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json",
        }

    def resolve_workspace_id(self, workspace_name: str) -> str | None:
        """Resolve a workspace display name to its ID."""
        if workspace_name in self._workspace_cache:
            return self._workspace_cache[workspace_name]

        url = f"{FABRIC_API_BASE}/workspaces"
        try:
            resp = requests.get(url, headers=self._headers(), timeout=30)
            resp.raise_for_status()
            for ws in resp.json().get("value", []):
                self._workspace_cache[ws["displayName"]] = ws["id"]
            return self._workspace_cache.get(workspace_name)
        except requests.RequestException as e:
            print(f"  ⚠️  API error resolving workspace: {e}", file=sys.stderr)
            return None

    def item_exists(self, workspace_id: str, api_path: str, item_name: str) -> bool:
        """Check if an item with the given name exists in the workspace."""
        cache_key = f"{workspace_id}:{api_path}"
        if cache_key not in self._items_cache:
            self._items_cache[cache_key] = self._list_items(workspace_id, api_path)
        return item_name.lower() in self._items_cache[cache_key]

    def _list_items(self, workspace_id: str, api_path: str) -> dict[str, str]:
        """List all items of a type in a workspace. Returns {lowercase_name: id}."""
        url = f"{FABRIC_API_BASE}/workspaces/{workspace_id}/{api_path}"
        items: dict[str, str] = {}
        try:
            while url:
                resp = requests.get(url, headers=self._headers(), timeout=30)
                resp.raise_for_status()
                data = resp.json()
                for item in data.get("value", []):
                    items[item["displayName"].lower()] = item["id"]
                url = data.get("continuationUri")
        except requests.RequestException as e:
            print(f"  ⚠️  API error listing {api_path}: {e}", file=sys.stderr)
        return items


# ---------------------------------------------------------------------------
# Handoff parser (matches shell script logic)
# ---------------------------------------------------------------------------

def _parse_handoff(path: str) -> tuple[str, str, str, list[dict]]:
    """Parse deployment-handoff.md → (project, task_flow, workspace, items)."""
    text = Path(path).read_text(encoding="utf-8")
    items: list[dict] = []

    # Extract metadata from YAML block
    project = ""
    task_flow = ""
    workspace = ""

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("project:"):
            project = stripped.split(":", 1)[1].strip().strip('"').strip("'")
        elif stripped.startswith("task_flow:"):
            task_flow = stripped.split(":", 1)[1].strip().strip('"').strip("'")
        elif stripped.startswith("workspace:"):
            workspace = stripped.split(":", 1)[1].strip().strip('"').strip("'")

    # Parse items block
    in_items = False
    current: dict | None = None

    for line in text.splitlines():
        stripped = line.strip()

        if stripped in ("items_deployed:", "items:"):
            in_items = True
            continue

        if in_items and stripped.startswith("- "):
            if current:
                items.append(current)
            current = {"name": "", "type": "", "wave": "", "status": "deployed"}

            # Inline format: - { name: ..., type: ... }
            if "{" in stripped:
                mapping = stripped[stripped.index("{"):].strip("{}")
                for part in re.split(r",\s*(?=\w+\s*:)", mapping):
                    m = re.match(r"(\w+)\s*:\s*(.*)", part.strip())
                    if m:
                        key, val = m.group(1), m.group(2).strip().strip('"').strip("'")
                        if key in ("name", "item_name"):
                            current["name"] = val
                        elif key in ("type", "item_type"):
                            current["type"] = val
                        elif key == "wave":
                            current["wave"] = val
                        elif key == "status":
                            current["status"] = val
                continue

            # Multi-line: - name: value
            rest = stripped[2:].strip()
            m = re.match(r"(\w+)\s*:\s*(.*)", rest)
            if m:
                key, val = m.group(1), m.group(2).strip().strip('"').strip("'")
                if key in ("name", "item_name"):
                    current["name"] = val
                elif key in ("type", "item_type"):
                    current["type"] = val
                elif key == "wave":
                    current["wave"] = val
                elif key == "status":
                    current["status"] = val
            continue

        if in_items and current and ":" in stripped and not stripped.startswith("#"):
            m = re.match(r"(\w+)\s*:\s*(.*)", stripped)
            if m:
                key, val = m.group(1), m.group(2).strip().strip('"').strip("'")
                if key in ("name", "item_name"):
                    current["name"] = val
                elif key in ("type", "item_type"):
                    current["type"] = val
                elif key == "wave":
                    current["wave"] = val
                elif key == "status":
                    current["status"] = val

        # End of items block
        if in_items and stripped and not stripped.startswith("-") and not stripped.startswith("#") and ":" in stripped:
            if stripped.split(":")[0].strip() not in ("name", "item_name", "type", "item_type", "wave", "status", "command", "notes", "deployment_time"):
                in_items = False

    if current:
        items.append(current)

    return project, task_flow, workspace, items


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

# Use the shared banner module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / "_shared"))
from banner import print_banner


def _print_banner(project: str, task_flow: str, mode: str = "Validation"):
    print_banner(project=project, task_flow=task_flow, mode=mode)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Validate deployed Fabric items via REST API (no fab CLI needed)"
    )
    parser.add_argument("handoff", help="Path to deployment-handoff.md")
    parser.add_argument("--workspace", help="Override workspace name")
    args = parser.parse_args()

    if not Path(args.handoff).exists():
        print(f"Error: File not found: {args.handoff}", file=sys.stderr)
        sys.exit(2)

    # Load registry
    registry = _load_registry()
    api_paths = _build_api_path_map(registry)
    portal_only = _build_portal_only(registry)

    # Parse handoff
    project, task_flow, workspace, items = _parse_handoff(args.handoff)
    if args.workspace:
        workspace = args.workspace

    if not workspace:
        print("Error: No workspace found in handoff. Use --workspace to specify.", file=sys.stderr)
        sys.exit(2)

    if not items:
        print("Error: No items found in the deployment handoff.", file=sys.stderr)
        sys.exit(2)

    # Show banner
    _print_banner(project, task_flow, "Validation")
    print(f"  Handoff:   {args.handoff}", file=sys.stderr)
    print(f"  Workspace: {workspace}", file=sys.stderr)
    print(f"  Items:     {len(items)}", file=sys.stderr)
    print(f"  Method:    Fabric REST API (no fab CLI)", file=sys.stderr)
    print("", file=sys.stderr)

    # Initialize API client
    client = FabricApiClient()
    workspace_id = client.resolve_workspace_id(workspace)
    if not workspace_id:
        print(f"Error: Could not resolve workspace '{workspace}'. Check az login and workspace name.", file=sys.stderr)
        sys.exit(2)

    # Validate each item
    phase_status: dict[str, str] = {}
    results: list[dict] = []
    manual_items: list[str] = []
    pass_count = fail_count = skip_count = manual_count = 0

    for item in items:
        name = item["name"]
        item_type = item["type"]
        status = item["status"]
        phase = _get_phase(item_type)

        if status != "deployed":
            print(f"  ⏭️  SKIP  {name} ({item_type}) — status: {status}", file=sys.stderr)
            results.append({"name": name, "method": f"skipped (status: {status})", "verified": "false", "issue": f"Item was not deployed (status: {status})"})
            skip_count += 1
            if phase_status.get(phase, "pass") != "fail":
                phase_status[phase] = "warn"
            continue

        if item_type in portal_only:
            print(f"  ⏭️  SKIP  {name} ({item_type}) — portal-only, manual check required", file=sys.stderr)
            results.append({"name": name, "method": "manual (portal-only)", "verified": "false", "issue": "Cannot verify via API — check Fabric Portal"})
            manual_items.append(name)
            manual_count += 1
            continue

        api_path = api_paths.get(item_type)
        if not api_path:
            print(f"  ⚠️  SKIP  {name} ({item_type}) — no API path in registry", file=sys.stderr)
            results.append({"name": name, "method": "skipped (no API path)", "verified": "false", "issue": f"No REST API path for type {item_type}"})
            skip_count += 1
            continue

        print(f"  Checking: GET /workspaces/{workspace_id[:8]}.../{api_path} → {name}", file=sys.stderr)

        if client.item_exists(workspace_id, api_path, name):
            print(f"  ✅ PASS  {name} ({item_type})", file=sys.stderr)
            results.append({"name": name, "method": "REST API", "verified": "true", "issue": ""})
            pass_count += 1
            phase_status.setdefault(phase, "pass")
        else:
            print(f"  ❌ FAIL  {name} ({item_type}) — not found in workspace", file=sys.stderr)
            results.append({"name": name, "method": "REST API", "verified": "false", "issue": "Item not found in workspace via REST API"})
            fail_count += 1
            phase_status[phase] = "fail"

    # Overall status
    if fail_count > 0:
        overall = "failed"
    elif skip_count > 0:
        overall = "partial"
    else:
        overall = "passed"

    # Summary
    total_checkable = len(items) - skip_count
    print("", file=sys.stderr)
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", file=sys.stderr)
    print(f"  {pass_count}/{total_checkable} items verified, {fail_count} failed, {manual_count} manual checks needed", file=sys.stderr)
    print(f"  Overall status: {overall}", file=sys.stderr)
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", file=sys.stderr)
    print("", file=sys.stderr)

    # Output YAML to stdout
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    known_phases = ["Foundation", "Environment", "Ingestion", "Transformation", "Visualization", "ML", "Other"]
    active_phases = []
    for it in items:
        p = _get_phase(it["type"])
        if p not in active_phases:
            active_phases.append(p)

    print(f"# Validation Report (Automated Scan)")
    print(f"# Generated: {today}")
    print(f"# Run by: validate-items.py (REST API)")
    print(f"# ⚠️ LLM supplement needed: Validation Context + Future Considerations prose")
    print()
    print(f'project: "{project}"')
    print(f'task_flow: "{task_flow}"')
    print(f'date: "{today}"')
    print(f"status: {overall}  # passed | partial | failed")
    print()
    print("phases:")

    for phase in known_phases:
        if phase in active_phases:
            ps = phase_status.get(phase, "pass")
            print(f"  - name: {phase}")
            print(f"    status: {ps}")
            print(f'    notes: ""')

    print("  - name: CI/CD Readiness")
    print("    status: na")
    print('    notes: ""')
    print()
    print("items_validated:")

    for r in results:
        print(f'  - name: "{r["name"]}"')
        print(f'    verified: {r["verified"]}')
        print(f'    method: "{r["method"]}"')
        print(f'    issue: "{r["issue"]}"')

    print()
    print("manual_steps:")

    if manual_items:
        for i, mi in enumerate(manual_items, 1):
            print(f"  - id: M-{i}")
            print(f"    confirmed: false")
            print(f'    action_needed: "Verify {mi} manually in Fabric Portal"')
    else:
        print("  []")

    print()
    print("issues:")

    if fail_count > 0:
        for r in results:
            if r["verified"] == "false" and r["method"] == "REST API":
                print(f"  - severity: high")
                print(f'    item: "{r["name"]}"')
                print(f'    issue: "{r["issue"]}"')
                print(f'    action: "Re-deploy item or verify workspace name"')
    else:
        print("  []")

    print()
    print("next_steps:")
    print('  - "LLM: Add Validation Context prose section"')
    print('  - "LLM: Add Future Considerations prose section"')

    if manual_items:
        print(f'  - "Verify {len(manual_items)} portal-only item(s) manually"')

    if fail_count > 0:
        print(f'  - "Investigate and re-deploy {fail_count} failed item(s)"')
        print('  - "Re-run validation after fixes"')

    sys.exit(1 if fail_count > 0 else 0)


if __name__ == "__main__":
    main()
