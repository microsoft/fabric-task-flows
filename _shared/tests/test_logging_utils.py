"""Tests for logging_utils — structured logging for task-flows scripts."""

from __future__ import annotations

import io
import os
import sys
from unittest import mock

from lib.logging_utils import ScriptLogger, get_logger


# ── get_logger returns ScriptLogger ───────────────────────────────────────


def test_get_logger_returns_script_logger():
    log = get_logger("test")
    assert isinstance(log, ScriptLogger)


def test_get_logger_preserves_name():
    log = get_logger("my-script")
    assert log.name == "my-script"


# ── info/warn/error write to stderr ───────────────────────────────────────


def test_info_writes_to_stderr():
    log = get_logger("test")
    captured = io.StringIO()
    with mock.patch("sys.stderr", captured):
        log.info("hello")
    output = captured.getvalue()
    assert "INFO" in output
    assert "[test]" in output
    assert "hello" in output


def test_warn_writes_to_stderr():
    log = get_logger("test")
    captured = io.StringIO()
    with mock.patch("sys.stderr", captured):
        log.warn("something off")
    output = captured.getvalue()
    assert "WARN" in output
    assert "something off" in output


def test_error_writes_to_stderr():
    log = get_logger("test")
    captured = io.StringIO()
    with mock.patch("sys.stderr", captured):
        log.error("bad thing")
    output = captured.getvalue()
    assert "ERROR" in output
    assert "bad thing" in output


# ── Context formatting ────────────────────────────────────────────────────


def test_context_included_in_output():
    log = get_logger("ctx-test")
    captured = io.StringIO()
    with mock.patch("sys.stderr", captured):
        log.info("deploying", project="acme", items=5)
    output = captured.getvalue()
    assert "project=acme" in output
    assert "items=5" in output


def test_no_context_no_parens():
    log = get_logger("ctx-test")
    captured = io.StringIO()
    with mock.patch("sys.stderr", captured):
        log.info("simple message")
    output = captured.getvalue()
    assert "(" not in output


# ── Debug only emits when env var is set ──────────────────────────────────


def test_debug_silent_without_env_var():
    log = get_logger("dbg")
    captured = io.StringIO()
    with mock.patch("sys.stderr", captured), mock.patch.dict(os.environ, {}, clear=True):
        # Ensure TASK_FLOWS_DEBUG is NOT set
        os.environ.pop("TASK_FLOWS_DEBUG", None)
        log.debug("should not appear")
    assert captured.getvalue() == ""


def test_debug_emits_with_env_var():
    log = get_logger("dbg")
    captured = io.StringIO()
    with mock.patch("sys.stderr", captured), mock.patch.dict(os.environ, {"TASK_FLOWS_DEBUG": "1"}):
        log.debug("should appear")
    output = captured.getvalue()
    assert "DEBUG" in output
    assert "should appear" in output


# ── Timestamp format ──────────────────────────────────────────────────────


def test_output_contains_timestamp():
    log = get_logger("ts")
    captured = io.StringIO()
    with mock.patch("sys.stderr", captured):
        log.info("tick")
    output = captured.getvalue()
    # Timestamp format: [HH:MM:SS]
    assert output.startswith("[")
    assert "]" in output
