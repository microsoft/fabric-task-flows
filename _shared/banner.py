"""
Shared banner and terminal output styling for Fabric Task Flows.

All scripts that print banners MUST import from here instead of
maintaining their own. Single source of truth for branding.

Usage:
    from banner import print_banner
    print_banner(project="My Project", task_flow="lambda", mode="Deploy")
"""

from __future__ import annotations

import sys

import pyfiglet

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich import box

    HAS_RICH = True
except ImportError:
    HAS_RICH = False

VERSION = "1.0.0"

# Microsoft Fabric brand teal
FABRIC_TEAL = "#008272"

# Pre-render FIGlet art once at import time
_FABRIC_ART = pyfiglet.figlet_format("FABRIC", font="slant").rstrip()
_SUBTITLE = "         T A S K   F L O W S"


def print_banner(
    project: str = "",
    task_flow: str = "",
    mode: str = "",
    *,
    file=sys.stderr,
) -> None:
    """Print the Fabric Task Flows banner with optional project context."""
    if HAS_RICH:
        _print_rich_banner(project, task_flow, mode, file)
    else:
        _print_plain_banner(project, task_flow, mode, file)


def _print_rich_banner(
    project: str, task_flow: str, mode: str, file
) -> None:
    console = Console(file=file, width=72)

    content = f"[bold {FABRIC_TEAL}]{_FABRIC_ART}[/]\n"
    content += f"[bold {FABRIC_TEAL}]{_SUBTITLE}[/]"

    if project or task_flow or mode:
        content += "\n"
    if project:
        content += f"\n[bold white]Project:[/]   [dim]{project}[/]"
    if task_flow:
        content += f"\n[bold white]Task Flow:[/] [dim]{task_flow}[/]"
    if mode:
        content += f"\n[bold white]Mode:[/]      [dim]{mode}[/]"

    console.print(Panel(
        content,
        box=box.HEAVY,
        border_style=FABRIC_TEAL,
        padding=(1, 3),
        subtitle=f"[dim]v{VERSION}[/]",
    ))


def _print_plain_banner(
    project: str, task_flow: str, mode: str, file
) -> None:
    """Fallback for terminals without rich."""
    w = 62
    lines = [
        "",
        "┏" + "━" * w + "┓",
        "┃" + " " * w + "┃",
    ]
    for art_line in _FABRIC_ART.split("\n"):
        lines.append(f"┃   {art_line.ljust(w - 3)}┃")
    lines.append(f"┃   {_SUBTITLE.ljust(w - 3)}┃")
    lines.append("┃" + " " * w + "┃")
    if project:
        lines.append(f"┃   Project:   {project.ljust(w - 16)}┃")
    if task_flow:
        lines.append(f"┃   Task Flow: {task_flow.ljust(w - 16)}┃")
    if mode:
        lines.append(f"┃   Mode:      {mode.ljust(w - 16)}┃")
    if project or task_flow or mode:
        lines.append("┃" + " " * w + "┃")
    lines.append("┗" + "━" * w + "┛")
    lines.append("")
    print("\n".join(lines), file=file)
