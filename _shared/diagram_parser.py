"""
Shared diagram parsing utilities for task-flows scripts.

Consolidates the duplicated deployment-order table extraction from
handoff-scaffolder.py and taskflow-gen.py.
"""

from __future__ import annotations

import re
from pathlib import Path

# Box-drawing characters used in deployment order tables
_BORDER_CHARS = set("┌├└─┼┬┴┐┤┘│")


def is_border_row(line: str) -> bool:
    """True when the row is purely box-drawing border characters."""
    return all(ch in _BORDER_CHARS or ch.isspace() for ch in line)


def extract_deployment_table(diagram_path: Path) -> list[str]:
    """Return the raw lines of the deployment-order code block.

    Looks for ``## Deployment Order`` and extracts the first fenced
    code block beneath it.
    """
    text = diagram_path.read_text(encoding="utf-8")
    match = re.search(r"^## Deployment Order\s*$", text, re.MULTILINE)
    if not match:
        return []
    rest = text[match.end():]
    fence_start = rest.find("```")
    if fence_start == -1:
        return []
    after_fence = rest[fence_start + 3:]
    fence_end = after_fence.find("```")
    block = after_fence[:fence_end] if fence_end != -1 else after_fence
    return block.splitlines()
