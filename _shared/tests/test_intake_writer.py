"""Tests for .github/skills/fabric-discover/scripts/intake-writer.py."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT_PATH = (
    REPO_ROOT
    / ".github" / "skills" / "fabric-discover" / "scripts" / "intake-writer.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("intake_writer", str(SCRIPT_PATH))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["intake_writer"] = mod
    spec.loader.exec_module(mod)
    return mod


iw = _load_module()


class TestBuildIntake:
    def test_all_values_present_floor_met(self):
        intake = iw.build_intake(
            "10 GB/day", "user",
            "nightly", "user",
            "SQL + CSV", "user",
            "low-code", "inferred",
        )
        assert intake["volume"] == {"value": "10 GB/day", "source": "user"}
        assert intake["versatility"]["source"] == "inferred"
        assert intake["confidence_floor_met"] is True

    def test_missing_value_becomes_unknown(self):
        intake = iw.build_intake(
            None, "user",
            "", "user",
            "SQL", "user",
            "low-code", "user",
        )
        assert intake["volume"] == {"value": None, "source": "unknown"}
        assert intake["velocity"]["source"] == "unknown"
        assert intake["confidence_floor_met"] is False

    def test_invalid_source_defaults_to_inferred(self):
        intake = iw.build_intake(
            "x", "bogus",
            "y", "user",
            "z", "user",
            "w", "user",
        )
        assert intake["volume"]["source"] == "inferred"

    def test_value_is_trimmed(self):
        intake = iw.build_intake(
            "  10 GB  ", "user",
            "batch", "user",
            "csv", "user",
            "low", "user",
        )
        assert intake["volume"]["value"] == "10 GB"


class TestWriteIntake:
    def test_roundtrip_utf8(self, tmp_path, monkeypatch):
        monkeypatch.setattr(iw, "_resolve_repo_root", lambda: tmp_path)
        proj = tmp_path / "_projects" / "sensor-hub"
        proj.mkdir(parents=True)

        intake = iw.build_intake(
            "10 GB — daily", "user",
            "≈1 min", "user",
            "Kafka → Lakehouse", "user",
            "low-code", "inferred",
        )
        out = iw.write_intake("sensor-hub", intake)
        assert out.exists()
        # Read back with strict UTF-8
        loaded = json.loads(out.read_text(encoding="utf-8"))
        assert loaded["volume"]["value"] == "10 GB — daily"
        assert loaded["velocity"]["value"] == "≈1 min"
        assert loaded["confidence_floor_met"] is True

    def test_missing_project_exits(self, tmp_path, monkeypatch):
        monkeypatch.setattr(iw, "_resolve_repo_root", lambda: tmp_path)
        (tmp_path / "_projects").mkdir()
        intake = iw.build_intake("x", "user", "y", "user", "z", "user", "w", "user")
        with pytest.raises(SystemExit):
            iw.write_intake("nonexistent", intake)
