#!/usr/bin/env python3
"""
Deterministic intake writer for the Fabric discovery phase.

Writes the user-confirmed 4 V's assessment into
``_projects/<project>/docs/.discovery-intake.json`` so that downstream tools
(notably ``run-pipeline.py discovery-summary``) can render a stable,
stakeholder-facing review without the agent re-stating the values in prose.

Each V carries two fields:

* ``value``  — the confirmed value (free text, e.g. "10 GB/day", "near real-time")
* ``source`` — one of ``user`` (stated outright), ``inferred`` (agent's best
  guess pending confirmation), or ``unknown`` (still a gap)

Usage:
    python .github/skills/fabric-discover/scripts/intake-writer.py \
        --project my-project \
        --volume "under 10 GB/day" --volume-source user \
        --velocity "daily batch" --velocity-source user \
        --variety "Square API + CSV" --variety-source user \
        --versatility "low-code preferred" --versatility-source inferred
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Standard bootstrap: add _shared/lib to sys.path, then import canonical REPO_ROOT.
_LIB = Path(__file__).resolve().parents[4] / "_shared" / "lib"
sys.path.insert(0, str(_LIB))
import bootstrap  # noqa: F401
from paths import REPO_ROOT

VALID_SOURCES = ("user", "inferred", "unknown")


def _resolve_repo_root() -> Path:
    """Return the canonical repo root (from paths.REPO_ROOT).

    Kept as a thin wrapper so tests can still monkey-patch it.
    """
    return REPO_ROOT


def build_intake(
    volume: str | None,
    volume_source: str,
    velocity: str | None,
    velocity_source: str,
    variety: str | None,
    variety_source: str,
    versatility: str | None,
    versatility_source: str,
) -> dict:
    """Assemble the intake dict. Any missing value becomes source=unknown."""

    def _v(value: str | None, source: str) -> dict:
        if not value or not value.strip():
            return {"value": None, "source": "unknown"}
        if source not in VALID_SOURCES:
            source = "inferred"
        return {"value": value.strip(), "source": source}

    intake = {
        "volume": _v(volume, volume_source),
        "velocity": _v(velocity, velocity_source),
        "variety": _v(variety, variety_source),
        "versatility": _v(versatility, versatility_source),
    }
    intake["confidence_floor_met"] = all(
        v["source"] in ("user", "inferred") for v in intake.values()
        if isinstance(v, dict)
    )
    return intake


def write_intake(project: str, intake: dict) -> Path:
    """Write intake JSON to _projects/<project>/docs/.discovery-intake.json."""
    repo_root = _resolve_repo_root()
    project_dir = repo_root / "_projects" / project
    if not project_dir.is_dir():
        print(
            f"ERROR: Project '{project}' not found at {project_dir}.\n"
            "       Scaffold it first with: run-pipeline.py start \"<Name>\".",
            file=sys.stderr,
        )
        sys.exit(1)

    docs = project_dir / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    out = docs / ".discovery-intake.json"
    out.write_text(json.dumps(intake, indent=2) + "\n", encoding="utf-8")
    return out


def main() -> None:
    p = argparse.ArgumentParser(
        description="Write the confirmed 4 V's intake for a discovery project"
    )
    p.add_argument("--project", required=True, help="Project folder name (kebab-case)")

    for v in ("volume", "velocity", "variety", "versatility"):
        p.add_argument(f"--{v}", type=str, default=None,
                       help=f"Confirmed {v} value (free text)")
        p.add_argument(f"--{v}-source", choices=VALID_SOURCES, default="inferred",
                       help=f"Source of the {v} value (default: inferred)")

    args = p.parse_args()

    intake = build_intake(
        args.volume, args.volume_source,
        args.velocity, args.velocity_source,
        args.variety, args.variety_source,
        args.versatility, args.versatility_source,
    )
    out = write_intake(args.project, intake)
    print(f"Intake written → {out}")
    if not intake["confidence_floor_met"]:
        print(
            "⚠️  One or more V's still marked 'unknown' — "
            "ask the user again before rendering the discovery summary.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
