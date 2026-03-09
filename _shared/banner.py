"""
Shared banner and terminal output styling for Fabric Task Flows.

All scripts that print banners MUST import from here instead of
maintaining their own. Single source of truth for branding.

Zero external dependencies — uses a static ASCII art block.

Usage:
    from banner import print_banner
    print_banner(project="My Project", task_flow="lambda", mode="Deploy")
"""

from __future__ import annotations

import sys

VERSION = "1.0.0"

# Static ASCII art — no pyfiglet dependency.
# Source: pyfiglet.figlet_format("FABRIC", font="slant")
# To update: change the lines below and run tests.
BANNER_ART = r"""
    _________    ____  ____  __________
   / ____/   |  / __ )/ __ \/  _/ ____/
  / /_  / /| | / __  / /_/ // // /
 / __/ / ___ |/ /_/ / _, _// // /___
/_/   /_/  |_/_____/_/ |_/___/\____/
        T A S K   F L O W S
""".strip("\n")


def print_banner(
    project: str = "",
    task_flow: str = "",
    mode: str = "",
    *,
    file=sys.stdout,
) -> None:
    """Print the Fabric Task Flows banner with optional project context.

    Outputs to stdout by default for visibility. Pass file=sys.stderr
    to suppress in piped contexts.
    """
    w = 62
    lines = [
        "",
        "+" + "-" * w + "+",
        "|" + " " * w + "|",
    ]
    for art_line in BANNER_ART.split("\n"):
        content = f"   {art_line}"
        lines.append(f"|{content.ljust(w)}|")
    lines.append("|" + " " * w + "|")
    if project:
        content = f"   Project:   {project}"
        lines.append(f"|{content.ljust(w)}|")
    if task_flow:
        content = f"   Task Flow: {task_flow}"
        lines.append(f"|{content.ljust(w)}|")
    if mode:
        content = f"   Mode:      {mode}"
        lines.append(f"|{content.ljust(w)}|")
    if project or task_flow or mode:
        lines.append("|" + " " * w + "|")
    lines.append("+" + f" v{VERSION} ".center(w, "-") + "+")
    lines.append("")
    print("\n".join(lines), file=file)


def banner_lines(
    project: str = "",
    task_flow: str = "",
) -> str:
    """Return the banner as a raw string for embedding in generated scripts.

    Uses simple print() calls so the generated script has zero dependencies.
    """
    w = 62
    parts = [
        '    print()',
        f'    print("+" + "-" * {w} + "+")',
        f'    print("|" + " " * {w} + "|")',
    ]
    for art_line in BANNER_ART.split("\n"):
        escaped = art_line.replace("\\", "\\\\").replace('"', '\\"')
        padded = escaped.ljust(w - 3)
        parts.append(f'    print("|   {padded}|")')
    parts.append(f'    print("|" + " " * {w} + "|")')
    if project:
        label = f"Project:   {project}"
        padded_label = label.ljust(w - 6)
        parts.append(f'    print("|   {padded_label}|")')
    if task_flow:
        label = f"Task Flow: {task_flow}"
        padded_label = label.ljust(w - 6)
        parts.append(f'    print("|   {padded_label}|")')
    if project or task_flow:
        parts.append(f'    print("|" + " " * {w} + "|")')
    version_bar = f" v{VERSION} ".center(w, "-")
    parts.append(f'    print("+" + "{version_bar}" + "+")')
    parts.append('    print()')
    return "\n".join(parts)
