"""
Structured logging utilities for task-flows scripts.

Provides a consistent logging interface that writes to stderr with
timestamps and context.  Scripts should use this instead of ad-hoc
``print(f"⚠ ...", file=sys.stderr)`` calls.

Usage::

    from logging_utils import get_logger
    log = get_logger("deploy-script-gen")
    log.info("Generating artifacts", project="my-project", items=5)
    log.warn("Missing wave", wave=3)
    log.error("Failed to parse handoff", path="handoff.md", error=str(e))
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone


class ScriptLogger:
    """Simple structured logger that writes to stderr."""

    def __init__(self, name: str) -> None:
        self.name = name

    def _emit(self, level: str, message: str, **context: object) -> None:
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        ctx = " ".join(f"{k}={v}" for k, v in context.items()) if context else ""
        line = f"[{ts}] {level} [{self.name}] {message}"
        if ctx:
            line += f" ({ctx})"
        print(line, file=sys.stderr)

    def info(self, message: str, **context: object) -> None:
        self._emit("INFO", message, **context)

    def warn(self, message: str, **context: object) -> None:
        self._emit("WARN", message, **context)

    def error(self, message: str, **context: object) -> None:
        self._emit("ERROR", message, **context)

    def debug(self, message: str, **context: object) -> None:
        """Only emits when TASK_FLOWS_DEBUG env var is set."""
        import os
        if os.environ.get("TASK_FLOWS_DEBUG"):
            self._emit("DEBUG", message, **context)


def get_logger(name: str) -> ScriptLogger:
    """Get a named logger instance."""
    return ScriptLogger(name)
