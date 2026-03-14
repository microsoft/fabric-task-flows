"""
Shared text utilities for task-flows scripts.

Consolidates duplicated slugify / kebab-case logic from deploy-script-gen.py,
new-project.py, and test-plan-prefill.py.
"""

from __future__ import annotations

import re


def slugify(name: str) -> str:
    """Convert a name to kebab-case (lowercase, hyphens, no special chars).

    >>> slugify("My Cool Project!")
    'my-cool-project'
    >>> slugify("  Hello   World  ")
    'hello-world'
    """
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s]+", "-", s)
    return s.strip("-")


def slugify_phase(name: str) -> str:
    """Convert a phase name to a kebab-case slug.

    More aggressive than ``slugify`` — collapses any non-alphanumeric
    sequence into a single hyphen.

    >>> slugify_phase("Phase 1: Foundation")
    'phase-1-foundation'
    """
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def escape_for_python_string(s: str) -> str:
    """Escape a string for safe embedding in Python string literals.

    Handles backslashes, quotes, and newlines to prevent template
    injection when generating Python code via f-strings.
    """
    return (
        s.replace('\\', '\\\\')
        .replace('"', '\\"')
        .replace("'", "\\'")
        .replace('\n', '\\n')
        .replace('\r', '\\r')
    )
