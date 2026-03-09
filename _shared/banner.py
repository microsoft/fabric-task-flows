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
                                                                          
 T A S K   F L O W S
___________________________________
""".strip("\n")

VERSION = "1.0.0"


def print_banner(
    project: str = "",
    task_flow: str = "",
    **_kwargs,
) -> None:
    """Print the Fabric Task Flows banner with project context."""
    print()
    print(BANNER_ART)
    if project or task_flow:
        label = ""
        if project:
            label += project
        if task_flow:
            label += f" | {task_flow}"
        print(f"  {label}")
        print()


if __name__ == "__main__":
    print_banner(project="retail-of-the-future", task_flow="medallion")