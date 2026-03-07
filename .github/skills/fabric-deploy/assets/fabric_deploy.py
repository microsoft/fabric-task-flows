"""
Fabric Task Flows — Python Deploy Utility

Shared utility for Python-based deploy scripts. Uses `fab <command>`
(direct CLI invocation, not interactive REPL).

Usage in generated deploy scripts:
    from fabric_deploy import FabricDeployer
    deployer = FabricDeployer(workspace="my-workspace", capacity="my-capacity")
    deployer.authenticate()
    deployer.create_workspace()
    deployer.create_item("my-lakehouse", "Lakehouse", enableSchemas="true")
"""

import os
import subprocess
import sys
from dataclasses import dataclass, field


def run_fab(command: str, capture: bool = False, allow_failure: bool = False) -> str | None:
    """Run a fab CLI command.

    Args:
        command: The fab command to run (e.g., 'get ws1.Workspace -q .').
        capture: If True, capture and return stdout.
        allow_failure: If True, don't raise on non-zero exit or stderr.

    Returns:
        Captured stdout (last line) if capture=True, else None.

    Raises:
        RuntimeError: If command fails and allow_failure is False.
    """
    # Split command into args for subprocess
    parts = command.split()
    result = subprocess.run(
        ["fab"] + parts,
        capture_output=True,
        text=True,
    )

    if not allow_failure and (result.returncode != 0 or result.stderr):
        raise RuntimeError(
            f"fab command failed: {command}\n"
            f"  exit_code: {result.returncode}\n"
            f"  stderr: {result.stderr.strip()}"
        )

    if capture:
        output = result.stdout.strip()
        return output.split("\n")[-1] if output else ""

    return None


def check_auth() -> bool:
    """Check if fab is authenticated by parsing status output text."""
    result = subprocess.run(
        ["fab", "auth", "status"],
        capture_output=True,
        text=True,
    )
    return "Not logged in" not in result.stdout


def authenticate_interactive():
    """Authenticate via interactive browser login."""
    print("  ── Opening Fabric login (browser)...")
    subprocess.run(["fab", "auth", "login"], text=True)
    if not check_auth():
        raise RuntimeError("Authentication failed. Run 'fab auth login' manually.")
    print("  ── ✅ Authenticated")


def authenticate_spn(client_id: str = None, client_secret: str = None, tenant_id: str = None):
    """Authenticate via Service Principal (for CI/CD)."""
    client_id = client_id or os.getenv("FABRIC_CLIENT_ID")
    client_secret = client_secret or os.getenv("FABRIC_CLIENT_SECRET")
    tenant_id = tenant_id or os.getenv("FABRIC_TENANT_ID")

    if not all([client_id, client_secret, tenant_id]):
        raise RuntimeError(
            "SPN auth requires FABRIC_CLIENT_ID, FABRIC_CLIENT_SECRET, FABRIC_TENANT_ID"
        )

    print("  ── Authenticating with Service Principal...")
    run_fab(f"auth login -u {client_id} -p {client_secret} --tenant {tenant_id}")
    print("  ── ✅ Authenticated (SPN)")


def fab_exists(path: str) -> bool:
    """Check if a Fabric item exists (idempotency check).
    
    The fab CLI outputs '* true' if the item exists, '* false' if not.
    Exit code is always 0 regardless.
    """
    result = subprocess.run(
        ["fab", "exists", path],
        capture_output=True,
        text=True,
    )
    return "* true" in result.stdout


@dataclass
class DeployResult:
    label: str
    status: str  # "created", "exists", "failed", "manual"


@dataclass
class FabricDeployer:
    """Manages Fabric workspace deployment with idempotency and retry."""

    workspace: str
    capacity: str = ""
    results: list[DeployResult] = field(default_factory=list)

    def authenticate(self, spn: bool = False):
        """Check auth status; auto-login if needed."""
        print("  Checking authentication...")
        if check_auth():
            print("  ── ✅ Already authenticated")
        elif spn:
            authenticate_spn()
        else:
            authenticate_interactive()

    def create_workspace(self) -> str:
        """Create workspace and assign capacity. Returns workspace ID."""
        ws_path = f"{self.workspace}.Workspace"
        print(f"\n  Creating workspace: {self.workspace}")

        if fab_exists(ws_path):
            print(f"  ── ✅ Workspace already exists")
        else:
            run_fab(f"mkdir {ws_path}", allow_failure=True)
            print(f"  ── ✅ Workspace created")

        # Assign capacity (uses capacity NAME, not GUID)
        if self.capacity:
            assign_result = run_fab(
                f"assign .capacities/{self.capacity}.Capacity -W {ws_path}",
                allow_failure=True
            )
            if assign_result is not None or True:  # assign doesn't return output on success
                print(f"  ── ✅ Capacity assigned: {self.capacity}")

        # Get workspace ID
        ws_id = run_fab(f"get {ws_path} -q id", capture=True, allow_failure=True) or "(unavailable)"
        print(f"  ── Workspace ID: {ws_id}")
        return ws_id

    def create_item(self, name: str, item_type: str, tree_char: str = "├──",
                    max_retries: int = 3, **params) -> str | None:
        """Create a Fabric item with idempotency and retry.

        Args:
            name: Item display name.
            item_type: Fabric item type (e.g., 'Lakehouse', 'Warehouse').
            tree_char: Tree connector for display.
            max_retries: Number of retry attempts.
            **params: Additional -P parameters (e.g., enableSchemas="true").

        Returns:
            Item ID if created/exists, None if failed.
        """
        path = f"{self.workspace}.Workspace/{name}.{item_type}"
        label = f"{item_type}: {name}"

        # Idempotency check
        if fab_exists(path):
            print(f"  {tree_char} ✅ {label} (already exists)")
            self.results.append(DeployResult(label, "exists"))
            item_id = run_fab(f"get {path} -q id", capture=True, allow_failure=True)
            return item_id

        # Build command with parameters
        param_str = ""
        if params:
            param_str = " -P " + ",".join(f"{k}={v}" for k, v in params.items())

        # Retry with backoff
        last_error = ""
        for attempt in range(1, max_retries + 1):
            try:
                run_fab(f"mkdir {path}{param_str}")
                print(f"  {tree_char} ✅ {label}")
                self.results.append(DeployResult(label, "created"))
                item_id = run_fab(f"get {path} -q id", capture=True, allow_failure=True)
                return item_id
            except RuntimeError as e:
                last_error = str(e)
                if attempt < max_retries:
                    wait = attempt * 10
                    print(f"  {tree_char} ⚠️  {label} (attempt {attempt} failed, retrying in {wait}s...)")
                    print(f"         Error: {last_error}")
                    import time
                    time.sleep(wait)

        print(f"  {tree_char} ❌ {label} (failed after {max_retries} attempts)")
        print(f"         Error: {last_error}")
        self.results.append(DeployResult(label, "failed"))
        return None

    def manual_step(self, label: str, tree_char: str = "├──"):
        """Record a manual (portal-only) step."""
        print(f"  {tree_char} ⏭️  [MANUAL] {label}")
        self.results.append(DeployResult(label, "manual"))

    def print_summary(self):
        """Print deployment summary."""
        created = sum(1 for r in self.results if r.status == "created")
        exists = sum(1 for r in self.results if r.status == "exists")
        failed = sum(1 for r in self.results if r.status == "failed")
        manual = sum(1 for r in self.results if r.status == "manual")

        print("\n┌──────────────────────────────────────────────────────────────────┐")
        print("│  DEPLOYMENT SUMMARY                                              │")
        print("└──────────────────────────────────────────────────────────────────┘\n")

        icons = {"created": "✅ Created", "exists": "✅ Exists ", "failed": "❌ Failed ",
                 "manual": "⏭️  Manual "}
        for r in self.results:
            print(f"  {icons.get(r.status, '?')}  {r.label}")

        print(f"\n  Created: {created}  |  Already existed: {exists}  |  Failed: {failed}  |  Manual: {manual}")

        if failed > 0:
            print("\n  ⚠️  Some items failed — check errors above and retry.")
            sys.exit(1)

    def print_metadata(self):
        """Print post-deployment metadata (workspace ID, tenant, portal URL)."""
        print("\n┌──────────────────────────────────────────────────────────────────┐")
        print("│  POST-DEPLOYMENT METADATA                                       │")
        print("└──────────────────────────────────────────────────────────────────┘\n")

        ws_id = run_fab(f"get {self.workspace}.Workspace -q id", capture=True, allow_failure=True) or "(unavailable)"
        print(f"  Workspace ID:   {ws_id}")

        # Parse tenant ID from auth status text output
        auth_out = run_fab("auth status", capture=True, allow_failure=True) or ""
        print(f"  Workspace URL:  https://app.fabric.microsoft.com/groups/{ws_id}")

        # List items
        print("\n  Item Details:")
        items_out = run_fab(f"ls {self.workspace}.Workspace -l", capture=True, allow_failure=True) or ""
        if items_out:
            print(f"  {items_out}")

        print("\n  ℹ️  Save these IDs — they are required for CI/CD parameterization")
        print("     and fabric-cicd library configuration.")


def print_banner(project: str, task_flow: str, mode: str = "Deploy to Fabric"):
    """Print the Fabric Task Flows banner."""
    def trim_text(text: str, max_len: int = 53) -> str:
        if not text:
            return ""
        return text[:max_len - 1] + "…" if len(text) > max_len else text

    project = trim_text(project)
    task_flow = trim_text(task_flow)
    mode = trim_text(mode)

    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║                                                                  ║")
    print("║       M I C R O S O F T   F A B R I C   T A S K   F L O W S      ║")
    print("║                                                                  ║")
    print("║  Deploy Microsoft Fabric architectures with guided wave rollout. ║")
    print("║                                                                  ║")
    print(f"║  Project:   {project:<53}║")
    print(f"║  Task Flow: {task_flow:<53}║")
    print(f"║  Mode:      {mode:<53}║")
    print("║                                                                  ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()


def prompt_value(env_var: str, prompt_text: str, default: str = "", optional: bool = False) -> str:
    """Prompt for a value with env var fallback."""
    env_val = os.getenv(env_var)
    if env_val:
        return env_val

    if default:
        response = input(f"  ? {prompt_text} (Enter = {default}, or type to rename): ").strip()
        return response or default
    elif optional:
        response = input(f"  ? {prompt_text} (optional, Enter to skip): ").strip()
        return response
    else:
        return input(f"  ? {prompt_text}: ").strip()
