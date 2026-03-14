"""
Canonical repo-root discovery for task-flows scripts.

Every script that needs REPO_ROOT should import from here instead of
computing its own parent-chain.  This module walks up from its own
location (``_shared/lib/``) to find the repo root, validated by the
presence of the ``_shared/registry/`` marker directory.

Usage (from any script that already has ``_shared/lib`` on sys.path)::

    from paths import REPO_ROOT, SHARED_DIR, REGISTRY_DIR
"""

from __future__ import annotations

from pathlib import Path

_HERE = Path(__file__).resolve().parent          # _shared/lib/
_SHARED = _HERE.parent                           # _shared/
_CANDIDATE = _SHARED.parent                      # repo root candidate


def _find_repo_root() -> Path:
    """Walk up from _shared/lib/ to locate the repo root.

    Validates by checking for ``_shared/registry/`` marker.  Falls back
    to the computed candidate if the marker is absent (e.g. in test
    environments with trimmed directory trees).
    """
    # Fast path — the expected layout
    if (_CANDIDATE / "_shared" / "registry").is_dir():
        return _CANDIDATE

    # Walk up (handles unexpected nesting)
    cur = _HERE
    for _ in range(10):
        if (cur / "_shared" / "registry").is_dir():
            return cur
        parent = cur.parent
        if parent == cur:
            break
        cur = parent

    # Fallback — trust the computed path
    return _CANDIDATE


REPO_ROOT: Path = _find_repo_root()
"""Absolute path to the repository root."""

SHARED_DIR: Path = REPO_ROOT / "_shared"
"""Absolute path to ``_shared/``."""

REGISTRY_DIR: Path = SHARED_DIR / "registry"
"""Absolute path to ``_shared/registry/``."""

LIB_DIR: Path = SHARED_DIR / "lib"
"""Absolute path to ``_shared/lib/``."""
