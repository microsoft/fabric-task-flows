#!/usr/bin/env python3
"""
Fleet runner — scaffolds and runs all problem statements through the pipeline
in parallel batches.

Reads problem-statements.md, scaffolds each as a project, runs the
deterministic pre-compute scripts, then generates discovery briefs and
architecture handoffs using template-based inference (no LLM required for
the deterministic portions).

For LLM-dependent phases (architecture decisions, reviews), the script
generates a batch prompt file that can be fed to an orchestrator.

Usage:
    python scripts/fleet-runner.py --problem-file .github/skills/fabric-heal/problem-statements.md
    python scripts/fleet-runner.py --problem-file .github/skills/fabric-heal/problem-statements.md --dry-run
    python scripts/fleet-runner.py --problem-file .github/skills/fabric-heal/problem-statements.md --phases discovery
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared" / "lib"))
from paths import REPO_ROOT

SCRIPTS_DIR = REPO_ROOT / "_shared" / "scripts"
PROJECTS_DIR = REPO_ROOT / "_projects"

sys.path.insert(0, str(SCRIPTS_DIR))


# ---------------------------------------------------------------------------
# Problem parser (reuse from analyze-inefficiencies)
# ---------------------------------------------------------------------------

def parse_problem_file(path: str) -> list[dict]:
    """Parse problem-statements.md into [{id, category, text, name}]."""
    # Import sanitize_name via text_utils.slugify (matches scaffold behavior)
    from text_utils import slugify as sanitize_name

    content = Path(path).read_text(encoding="utf-8")
    problems = []
    current_category = "Uncategorized"
    for line in content.splitlines():
        m = re.match(r"^##\s+(.+)", line)
        if m:
            current_category = m.group(1).strip()
            continue
        m = re.match(r'^\d+\.\s+"(.+)"', line)
        if m:
            pid = len(problems) + 1
            text = m.group(1)
            display_name = f"Fleet {current_category} {pid}"
            name = sanitize_name(display_name)
            problems.append({
                "id": pid,
                "category": current_category,
                "text": text,
                "name": name,
                "display_name": display_name,
            })
    return problems


# ---------------------------------------------------------------------------
# Signal mapper runner
# ---------------------------------------------------------------------------

def run_signal_mapper(problem_text: str) -> dict | None:
    """Run signal mapper and return parsed JSON result."""
    cmd = [sys.executable, str(SCRIPTS_DIR / "signal-mapper.py"),
           "--text", problem_text, "--format", "json"]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=30, encoding="utf-8", env=env)
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout)
    except Exception as e:
        print(f"⚠ signal mapper failed: {e}", file=sys.stderr)
    return None


# ---------------------------------------------------------------------------
# Discovery brief generator (deterministic from signal mapper output)
# ---------------------------------------------------------------------------

def generate_discovery_brief(problem: dict, signals: dict) -> str:
    """Generate a discovery brief from problem + signal mapper output."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Extract signal data
    sig_list = signals.get("signals", [])
    candidates = signals.get("task_flow_candidates", [])
    velocity = signals.get("primary_velocity", "unknown")

    # Build inferred signals table rows
    velocity_conf = "high" if signals.get("keyword_coverage", 0) > 0.1 else "medium"
    use_case_values = set()
    for s in sig_list:
        uc = s.get("value", "")
        if uc:
            use_case_values.add(uc)
    use_case = ", ".join(use_case_values) if use_case_values else "Analytics"

    # Build candidate table
    candidate_rows = ""
    for c in candidates[:3]:
        cid = c.get("id", "?")
        csigs = ", ".join(c.get("signals", []))
        candidate_rows += f"| {cid} | Matched signals: {csigs} | medium |\n"
    if not candidate_rows:
        candidate_rows = "| basic-data-analytics | Default — no strong signal match | low |\n"

    brief = f"""## Discovery Brief

**Project:** {problem['name']}
**Date:** {today}

### Problem Statement

> {problem['text']}

### Inferred Signals

| Signal | Value | Confidence | Source |
|--------|-------|------------|--------|
| Data Velocity | {velocity} | {velocity_conf} | Signal mapper inference |
| Use Case | {use_case} | medium | Signal mapper inference |

### Suggested Task Flow Candidates

| Candidate | Why It Fits | Confidence |
|-----------|-------------|------------|
{candidate_rows}
### 4 V's Assessment

| V | Value | Confidence | Source |
|---|-------|------------|--------|
| Volume | unknown | low | Not specified in problem statement |
| Velocity | {velocity} | {velocity_conf} | Signal mapper inference |
| Variety | unknown | low | Not specified in problem statement |
| Versatility | unknown | low | Not specified in problem statement |

### Confirmed with User

- [ ] Fleet run — no user confirmation (automated stress test)

### Architectural Judgment Calls

- Whether the signal mapper's top candidate is correct given limited context.
- Whether additional 4 V's data would change the task flow selection.
"""
    return brief


# ---------------------------------------------------------------------------
# Single project pipeline runner
# ---------------------------------------------------------------------------

def process_project(problem: dict, dry_run: bool = False) -> dict:
    """Scaffold a project, run signal mapper, write discovery brief, advance."""
    result = {
        "id": problem["id"],
        "name": problem["name"],
        "category": problem["category"],
        "status": "pending",
        "task_flow_candidates": [],
        "signals_matched": 0,
        "keyword_coverage": 0,
        "error": None,
    }

    project_dir = PROJECTS_DIR / problem["name"]

    if dry_run:
        signals = run_signal_mapper(problem["text"])
        if not signals:
            signals = {"signals": [], "task_flow_candidates": [],
                       "primary_velocity": "unknown", "keyword_coverage": 0}
        result["status"] = "dry-run"
        result["task_flow_candidates"] = [
            c.get("id", "?") for c in signals.get("task_flow_candidates", [])[:3]
        ]
        result["signals_matched"] = len(signals.get("signals", []))
        result["keyword_coverage"] = signals.get("keyword_coverage", 0)
        return result

    # 1. Scaffold
    try:
        cmd = [sys.executable, str(SCRIPTS_DIR / "run-pipeline.py"),
               "start", problem["display_name"], "--problem", problem["text"]]
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=60, encoding="utf-8", env=env)
        if r.returncode != 0:
            # May already exist
            if "already exists" in (r.stdout + r.stderr):
                pass  # continue with existing project
            else:
                result["status"] = "scaffold-failed"
                result["error"] = r.stderr[:200] if r.stderr else r.stdout[:200]
                return result
    except Exception as e:
        result["status"] = "scaffold-error"
        result["error"] = str(e)[:200]
        return result

    # 2. Run signal mapper
    signals = run_signal_mapper(problem["text"])
    if not signals:
        signals = {"signals": [], "task_flow_candidates": [],
                   "primary_velocity": "unknown", "keyword_coverage": 0}

    result["task_flow_candidates"] = [
        c.get("id", "?") for c in signals.get("task_flow_candidates", [])[:3]
    ]
    result["signals_matched"] = len(signals.get("signals", []))
    result["keyword_coverage"] = signals.get("keyword_coverage", 0)

    # 3. Write discovery brief
    brief_path = project_dir / "docs" / "discovery-brief.md"
    if brief_path.exists():
        brief_content = generate_discovery_brief(problem, signals)
        brief_path.write_text(brief_content, encoding="utf-8", newline="\n")

    # 4. Advance past discovery
    try:
        cmd = [sys.executable, str(SCRIPTS_DIR / "run-pipeline.py"),
               "advance", "--project", problem["name"]]
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=30, encoding="utf-8", env=env)
        if r.returncode == 0:
            result["status"] = "discovery-complete"
        else:
            result["status"] = "advance-failed"
            result["error"] = r.stderr[:200] if r.stderr else r.stdout[:200]
    except Exception as e:
        result["status"] = "advance-error"
        result["error"] = str(e)[:200]

    return result


# ---------------------------------------------------------------------------
# Fleet summary
# ---------------------------------------------------------------------------

def print_fleet_summary(results: list[dict]) -> None:
    """Print a summary table of all fleet results."""
    print(f"\n{'═'*100}")
    print("  FLEET DEPLOYMENT SUMMARY")
    print(f"{'═'*100}")
    print(f"  {'ID':>3}  {'Project':<30}  {'Category':<25}  {'Status':<20}  {'Candidates':<30}")
    print(f"  {'─'*3}  {'─'*30}  {'─'*25}  {'─'*20}  {'─'*30}")

    for r in results:
        candidates = ", ".join(r.get("task_flow_candidates", [])[:3]) or "—"
        status = r.get("status", "?")
        icon = {"discovery-complete": "✅", "dry-run": "🔍",
                "scaffold-failed": "❌", "signal-mapper-failed": "⚠️",
                "advance-failed": "⚠️"}.get(status, "❓")
        print(f"  {r['id']:>3}  {r['name']:<30}  {r['category']:<25}  {icon} {status:<17}  {candidates}")

    # Stats
    success = sum(1 for r in results if r["status"] in ("discovery-complete", "dry-run"))
    failed = sum(1 for r in results if "failed" in r.get("status", "") or "error" in r.get("status", ""))
    avg_cov = sum(r.get("keyword_coverage", 0) for r in results) / len(results) if results else 0
    avg_sigs = sum(r.get("signals_matched", 0) for r in results) / len(results) if results else 0

    print(f"\n  {'─'*96}")
    print(f"  Total: {len(results)} │ Success: {success} │ Failed: {failed} │ "
          f"Avg coverage: {avg_cov:.1%} │ Avg signals: {avg_sigs:.1f}")
    print(f"{'═'*100}\n")


def update_projects_md(results: list[dict]) -> None:
    """Add fleet projects to PROJECTS.md."""
    projects_md = REPO_ROOT / "PROJECTS.md"
    content = projects_md.read_text(encoding="utf-8")

    new_rows = []
    for r in results:
        if r["status"] == "discovery-complete":
            candidates = ", ".join(r.get("task_flow_candidates", [])[:2]) or "TBD"
            name = r["name"]
            # Skip if already in file
            if name in content:
                continue
            new_rows.append(
                f"| {name} | TBD | Discovery ✅ | "
                f"Fleet run — candidates: {candidates} | None | "
                f"Architecture Design (Phase 1a) |"
            )

    if new_rows:
        # Insert before the "> Project rows" line
        insert_point = content.find("> Project rows")
        if insert_point == -1:
            insert_point = len(content)
        else:
            # Find the line start
            insert_point = content.rfind("\n", 0, insert_point) + 1

        new_content = content[:insert_point] + "\n".join(new_rows) + "\n" + content[insert_point:]
        projects_md.write_text(new_content, encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Fleet runner — deploy multiple projects in parallel"
    )
    parser.add_argument("--problem-file",
                        default=str(REPO_ROOT / ".github" / "skills" / "fabric-heal" / "problem-statements.md"),
                        help="Path to problem-statements.md")
    parser.add_argument("--workers", type=int, default=4,
                        help="Parallel workers (default: 4)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run signal mapper only, don't scaffold")
    parser.add_argument("--heal", action="store_true",
                        help="Run self-heal.py before fleet deployment")
    parser.add_argument("--ids", type=str, default=None,
                        help="Comma-separated problem IDs to run (default: all)")
    args = parser.parse_args()

    # Run self-heal before fleet if requested
    if args.heal:
        print("\n  🔧 Running self-heal before fleet deployment...")
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        cmd = [sys.executable, str(SCRIPTS_DIR / "self-heal.py"),
               "--problem-file", args.problem_file]
        if args.dry_run:
            cmd.append("--dry-run")
        subprocess.run(cmd, env=env, encoding="utf-8")

    problems = parse_problem_file(args.problem_file)

    if args.ids:
        selected = set(int(i) for i in args.ids.split(","))
        problems = [p for p in problems if p["id"] in selected]

    print(f"\n{'═'*60}")
    print(f"  FLEET RUNNER — {len(problems)} projects")
    print(f"  Workers: {args.workers} │ Mode: {'dry-run' if args.dry_run else 'full scaffold'}")
    print(f"{'═'*60}\n")

    results: list[dict] = []

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(process_project, p, args.dry_run): p
            for p in problems
        }
        for future in as_completed(futures):
            problem = futures[future]
            try:
                result = future.result()
                results.append(result)
                status = result.get("status", "?")
                icon = "✅" if "complete" in status or status == "dry-run" else "❌"
                print(f"  {icon} P{result['id']:02d} {result['name']}: {status}")
                if result.get("error"):
                    print(f"       └─ {result['error'][:80]}")
            except Exception as e:
                print(f"  ❌ P{problem['id']:02d} {problem['name']}: exception — {e}")
                results.append({
                    "id": problem["id"], "name": problem["name"],
                    "category": problem["category"], "status": "exception",
                    "task_flow_candidates": [], "signals_matched": 0,
                    "keyword_coverage": 0, "error": str(e)[:200],
                })

    # Sort by ID for display
    results.sort(key=lambda r: r["id"])
    print_fleet_summary(results)

    # Update PROJECTS.md for scaffolded projects
    if not args.dry_run:
        update_projects_md(results)
        print("  PROJECTS.md updated with fleet projects.\n")

    # Write fleet results to session file
    results_path = PROJECTS_DIR / "_fleet-results.json"
    with open(results_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(results, f, indent=2)
    print(f"  Results saved to {results_path}\n")


if __name__ == "__main__":
    main()
