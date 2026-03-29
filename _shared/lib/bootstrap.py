"""
One-line sys.path bootstrap for task-flows scripts.

Instead of each script computing its own parent chain::

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / "_shared" / "lib"))

Scripts can do::

    sys.path.insert(0, str(Path(__file__).resolve().parents[N] / "_shared" / "lib"))
    import bootstrap  # noqa: F401 — triggers path setup

This module, when imported, ensures that ``_shared/lib`` is on sys.path
(for ``paths``, ``registry_loader``, etc.) and ``_shared/scripts`` is
available for cross-script imports.

Since ``paths.py`` already handles REPO_ROOT discovery and UTF-8 stdout
configuration, bootstrap just needs to make sure the script directories
are importable.
"""

from __future__ import annotations

import sys
from pathlib import Path

_LIB_DIR = Path(__file__).resolve().parent       # _shared/lib/
_SHARED_DIR = _LIB_DIR.parent                    # _shared/
_SCRIPTS_DIR = _SHARED_DIR / "scripts"            # _shared/scripts/

# Ensure both lib and scripts dirs are on sys.path (idempotent)
for _dir in (_LIB_DIR, _SCRIPTS_DIR):
    _dir_str = str(_dir)
    if _dir_str not in sys.path:
        sys.path.insert(0, _dir_str)
