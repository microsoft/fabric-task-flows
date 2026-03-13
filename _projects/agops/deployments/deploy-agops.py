#!/usr/bin/env python3
"""
Fabric Task Flows - Deploy Script
Project:   agops
Task Flow: event-medallion

Uses fabric-cicd (pip install fabric-cicd) for deployment.
"""

import argparse
import os
import sys
import yaml

BASE_URL = "https://api.fabric.microsoft.com/v1"

def print_banner():
    divider = "-" * 75
    print()
    print("  __  __ _                           __ _      _____     _          _      ")
    print(" |  \\/  (_) ___ _ __ ___  ___  ___  / _| |_   |  ___|_ _| |__  _ __(_) ___ ")
    print(" | |\\/| | |/ __| '__/ _ \\/ __|/ _ \\| |_| __|  | |_ / _` | '_ \\| '__| |/ __|")
    print(" | |  | | | (__| | | (_) \\__ \\ (_) |  _| |_   |  _| (_| | |_) | |  | | (__ ")
    print(" |_|  |_|_|\\___|_|  \\___/|___/\\___/|_|  \\__|  |_|  \\__,_|_.__/|_|  |_|\\___|")
    print()
    print(divider)
    print("  T A S K   F L O W S")
    print("  Project:   agops")
    print("  Task Flow: event-medallion")
    print(divider)
    print()


def get_auth_headers():
    try:
        from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
        import requests
    except ImportError:
        print("  -- azure-identity not installed. Run: pip install azure-identity")
        sys.exit(1)
    scope = "https://api.fabric.microsoft.com/.default"
    try:
        token = DefaultAzureCredential().get_token(scope).token
    except Exception:
        print("  -- Default credentials not available. Opening browser for sign-in...")
        token = InteractiveBrowserCredential().get_token(scope).token
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def ensure_workspace(name, headers, description=""):
    import requests
    resp = requests.get(f"{BASE_URL}/workspaces", headers=headers)
    if resp.ok:
        for ws in resp.json().get("value", []):
            if ws.get("displayName") == name:
                print(f"  -- Found workspace: {name} ({ws['id'][:8]}...)")
                return ws["id"]
    print(f"  -- Workspace '{name}' not found.")
    response = input("  ? Create it now? [Y/n]: ").strip() or "Y"
    if response.upper() != "Y":
        sys.exit(1)
    create_resp = requests.post(f"{BASE_URL}/workspaces", headers=headers,
        json={"displayName": name, "description": description})
    if create_resp.ok:
        new_id = create_resp.json()["id"]
        print(f"  -- Created workspace: {name} ({new_id[:8]}...)")
        return new_id
    else:
        print(f"  -- Failed: {create_resp.json().get('message', create_resp.text)}")
        sys.exit(1)


def ensure_capacity(ws_id, headers):
    import requests
    ws_resp = requests.get(f"{BASE_URL}/workspaces/{ws_id}", headers=headers)
    if ws_resp.ok:
        ws_data = ws_resp.json()
        if ws_data.get("capacityId") and ws_data["capacityId"] != "00000000-0000-0000-0000-000000000000":
            print(f"  -- Capacity already assigned")
            return
    print("  -- No capacity assigned. Fetching available capacities...")
    cap_resp = requests.get(f"{BASE_URL}/capacities", headers=headers)
    capacities = cap_resp.json().get("value", []) if cap_resp.ok else []
    if not capacities:
        print("  -- No capacities available.")
        sys.exit(1)
    print()
    for i, cap in enumerate(capacities):
        print(f"  {i+1:3})  {cap.get('displayName', 'Unknown')} ({cap.get('sku', '')})")
    print()
    num = 0
    while num < 1 or num > len(capacities):
        try: num = int(input("  ? Select capacity: ").strip())
        except ValueError: num = 0
    cap_id = capacities[num - 1]["id"]
    assign_resp = requests.post(f"{BASE_URL}/workspaces/{ws_id}/assignToCapacity",
        headers=headers, json={"capacityId": cap_id})
    if assign_resp.ok or assign_resp.status_code == 202:
        print(f"  -- Capacity assigned: {capacities[num-1].get('displayName', '')}")
    else:
        print("  -- Failed to assign capacity")
        sys.exit(1)


def deploy_to_workspace(config_path, ws_id, environment=None):
    from fabric_cicd import deploy_with_config
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    config["core"]["workspace_id"] = ws_id
    config["core"].pop("workspace", None)
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    kwargs = {"config_file_path": config_path}
    if environment:
        kwargs["environment"] = environment

    # Retry deploy up to 3 times — fabric-cicd skips already-published items on re-run
    import time
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            deploy_with_config(**kwargs)
            return
        except Exception as e:
            err_msg = str(e)
            if "timed out" in err_msg.lower() or "timeout" in err_msg.lower() or "connection" in err_msg.lower():
                if attempt < max_retries:
                    wait = attempt * 30
                    print(f"  -- Timeout on attempt {attempt}, retrying in {wait}s...")
                    time.sleep(wait)
                    continue
            raise


def populate_variable_library(ws_id, headers):
    # Post-deploy: populate Variable Library with ItemReference variables for all deployed items.
    # Uses ItemReference type (workspaceId + itemId in one variable) — no separate _WSID vars needed.
    import requests, base64
    import json as _json
    from datetime import datetime
    print()
    print("  -- POPULATING VARIABLE LIBRARY --")

    resp = requests.get(f"{BASE_URL}/workspaces/{ws_id}/items", headers=headers)
    if not resp.ok:
        print(f"  ── Could not list items: {resp.text}")
        return

    items = resp.json().get("value", [])

    vl_item = None
    for item in items:
        if item.get("type") == "VariableLibrary":
            vl_item = item
            break

    if not vl_item:
        print("  ── No Variable Library found — skipping")
        return

    vl_id = vl_item["id"]
    print(f"  ── Found Variable Library: {vl_item.get('displayName', '')} ({vl_id[:8]}...)")

    # Map item types to role-based names
    ROLE_MAP = {
        "Lakehouse": "Raw_Lakehouse",
        "Warehouse": "Curated_Warehouse",
        "Eventhouse": "Streaming_Eventhouse",
        "Environment": "Spark_Environment",
        "DataPipeline": "Batch_Pipeline",
        "Eventstream": "Feed_Eventstream",
        "Notebook": "NLP_Notebook",
        "KQLQueryset": "KQL_Queryset",
        "SemanticModel": "Semantic_Model",
        "Report": "Leadership_Report",
        "Reflex": "Alerts_Activator",
        "KQLDashboard": "RT_Dashboard",
        "MLExperiment": "ML_Experiment",
    }

    variables = []
    role_counter = {}
    # Only these types support ItemReference consumers (Notebooks, Shortcuts, UDFs)
    ITEM_REF_TYPES = {"Lakehouse", "Warehouse", "Eventhouse", "Environment", "SemanticModel"}

    for item in items:
        item_type = item.get("type", "")
        if item_type == "VariableLibrary":
            continue

        role_name = ROLE_MAP.get(item_type, item["displayName"].replace("-", "_").replace(" ", "_"))

        role_counter[role_name] = role_counter.get(role_name, 0) + 1
        if role_counter[role_name] > 1:
            role_name = f"{role_name}_{role_counter[role_name]}"

        if item_type in ITEM_REF_TYPES:
            # ItemReference — contains workspaceId + itemId (no separate String needed)
            variables.append({
                "name": role_name,
                "type": "ItemReference",
                "value": {"workspaceId": ws_id, "itemId": item["id"]},
                "note": f"{item_type} — {item.get('displayName', '')}"
            })
        else:
            # String — for types that don't support ItemReference
            variables.append({
                "name": role_name,
                "type": "String",
                "value": item["id"],
                "note": f"{item_type} — {item.get('displayName', '')}"
            })

    # Operational metadata (String type — not item references)
    variables.append({"name": "Workspace_ID", "type": "String", "value": ws_id, "note": "Current workspace GUID"})
    variables.append({"name": "Workspace_URL", "type": "String", "value": f"https://app.fabric.microsoft.com/groups/{ws_id}", "note": "Fabric Portal URL"})
    variables.append({"name": "Project_Name", "type": "String", "value": "agops", "note": "Project name"})
    variables.append({"name": "Environment_Name", "type": "String", "value": "dev", "note": "Current deployment stage"})
    variables.append({"name": "Deploy_Timestamp", "type": "String", "value": datetime.utcnow().isoformat() + "Z", "note": "Deployment timestamp"})

    # Build and push definition
    var_json = _json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/variableLibrary/definition/variables/1.0.0/schema.json",
        "variables": variables
    })
    settings_json = _json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/variableLibrary/definition/settings/1.0.0/schema.json",
        "valueSetsOrder": []
    })

    body = {
        "definition": {
            "format": "VariableLibraryV1",
            "parts": [
                {"path": "variables.json", "payload": base64.b64encode(var_json.encode()).decode(), "payloadType": "InlineBase64"},
                {"path": "settings.json", "payload": base64.b64encode(settings_json.encode()).decode(), "payloadType": "InlineBase64"}
            ]
        }
    }

    update_resp = requests.post(
        f"{BASE_URL}/workspaces/{ws_id}/VariableLibraries/{vl_id}/updateDefinition",
        headers=headers, json=body
    )

    ref_count = sum(1 for v in variables if v["type"] == "ItemReference")
    str_count = sum(1 for v in variables if v["type"] == "String")

    if update_resp.ok or update_resp.status_code == 202:
        print(f"  ── Populated {len(variables)} variables ({ref_count} ItemReferences + {str_count} metadata)")
    else:
        print(f"  ── Could not update Variable Library: {update_resp.text[:200]}")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        fallback = os.path.join(script_dir, "variable-library-definition.json")
        with open(fallback, "w", encoding="utf-8") as f:
            _json.dump(body, f, indent=2)
        print(f"  ── Definition saved to: {fallback}")


def main():
    parser = argparse.ArgumentParser(description="Deploy agops")
    parser.add_argument("--workspace-id", default=os.getenv("FABRIC_WORKSPACE_ID", ""))
    parser.add_argument("--workspace", default=os.getenv("FABRIC_WORKSPACE_NAME", ""))
    parser.add_argument("--mode", choices=["single", "multi"], default=os.getenv("FABRIC_DEPLOY_MODE", ""))
    parser.add_argument("--config", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yml"))
    args = parser.parse_args()

    try:
        import fabric_cicd
    except ImportError:
        print("  fabric-cicd is not installed.")
        response = input("  ? Install it now? [Y/n]: ").strip() or "Y"
        if response.upper() == "Y":
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "fabric-cicd"])
        else:
            sys.exit(1)

    print_banner()

    if not args.mode:
        print("    1)  Single workspace (demo / simple deploy)")
        print("    2)  Multi-environment (dev / ppe / prod)")
        print()
        choice = ""
        while choice not in ("1", "2"):
            choice = input("  ? Select mode (1 or 2): ").strip()
        args.mode = "single" if choice == "1" else "multi"

    headers = get_auth_headers()

    if args.mode == "single":
        print()
        print("  -- WORKSPACE --")
        if args.workspace_id:
            ws_id = args.workspace_id
        else:
            ws_name = args.workspace or input("  ? Workspace name (Enter = agops): ").strip() or "agops"
            ws_id = ensure_workspace(ws_name, headers, "agops — event-medallion architecture. IoT fleet telemetry, predictive maintenance ML, executive dashboards, and AI chat for a 2,000-acre ag operation.")
        print()
        print("  -- CAPACITY --")
        ensure_capacity(ws_id, headers)
        print()
        print("  -- DEPLOYING --")
        try:
            deploy_to_workspace(args.config, ws_id)
            populate_variable_library(ws_id, headers)
            print()
            print("  Deployment complete!")
        except Exception as e:
            print(f"  Deployment failed: {e}")
            sys.exit(1)
    else:
        base_name = args.workspace or input("  ? Base workspace name (Enter = agops): ").strip() or "agops"
        envs = ["dev", "ppe", "prod"]
        print()
        print("  -- WORKSPACES (3 environments) --")
        ws_ids = {}
        for env in envs:
            ws_name = f"{base_name}-{env}"
            print(f"  {env.upper()}:")
            ws_ids[env] = ensure_workspace(ws_name, headers, "agops — event-medallion architecture. IoT fleet telemetry, predictive maintenance ML, executive dashboards, and AI chat for a 2,000-acre ag operation.")
        print()
        print("  -- CAPACITY --")
        for env in envs:
            print(f"  {env.upper()}:")
            ensure_capacity(ws_ids[env], headers)
        print()
        print("  -- DEPLOYING (dev -> ppe -> prod) --")
        for env in envs:
            print(f"  Deploying to {env.upper()}...")
            try:
                deploy_to_workspace(args.config, ws_ids[env], environment=env)
                populate_variable_library(ws_ids[env], headers)
                print(f"  {env.upper()} complete!")
            except Exception as e:
                print(f"  {env.upper()} failed: {e}")
                sys.exit(1)
        print()
        print("  All environments deployed!")


if __name__ == "__main__":
    main()
