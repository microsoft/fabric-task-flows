"""
Shared banner for Fabric Task Flows.

All scripts that print banners MUST import from here.
Single source of truth for branding.

Usage:
    from banner import print_banner
    print_banner(project="my-project", task_flow="medallion")
"""

BANNER_ART = r"""
  __  __ _                           __ _      _____     _          _      
 |  \/  (_) ___ _ __ ___  ___  ___  / _| |_   |  ___|_ _| |__  _ __(_) ___ 
 | |\/| | |/ __| '__/ _ \/ __|/ _ \| |_| __|  | |_ / _` | '_ \| '__| |/ __|
 | |  | | | (__| | | (_) \__ \ (_) |  _| |_   |  _| (_| | |_) | |  | | (__ 
 |_|  |_|_|\___|_|  \___/|___/\___/|_|  \__|  |_|  \__,_|_.__/|_|  |_|\___|
""".strip("\n")


def print_banner(
    project: str = "",
    task_flow: str = "",
    **_kwargs,
) -> None:
    """Print the Fabric Task Flows banner with project context."""
    art_lines = BANNER_ART.split("\n")
    divider = "-" * max(len(line) for line in art_lines)
    
    print()
    print(BANNER_ART)
    print()
    print(divider)
    print("  T A S K   F L O W S")
    if project:
        print(f"  Project:   {project}")
    if task_flow:
        print(f"  Task Flow: {task_flow}")
    print(divider)
    print()


if __name__ == "__main__":
    print_banner(project="retail-of-the-future", task_flow="medallion")