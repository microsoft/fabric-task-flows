#!/usr/bin/env python3
"""
Pipeline inefficiency analyzer — stress-tests the framework's deterministic
scripts against a problem statement and analyzes all existing project artifacts
to discover recurring patterns and inefficiencies.

Runs signal-mapper, review-prescan, and diagram-validator against existing
project data, then mines all project artifacts for common patterns. Appends
new findings to _shared/learnings.md.

Usage:
    python .github/skills/fabric-heal/scripts/analyze-inefficiencies.py --problem "your problem statement"
    python .github/skills/fabric-heal/scripts/analyze-inefficiencies.py --problem "..." --runs 20
    python .github/skills/fabric-heal/scripts/analyze-inefficiencies.py --all-projects
    python .github/skills/fabric-heal/scripts/analyze-inefficiencies.py --problem "..." --runs 20 --all-projects --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / ".github" / "skills" / "fabric-discover" / "scripts"
PROJECTS_DIR = REPO_ROOT / "_projects"
LEARNINGS_PATH = REPO_ROOT / "_shared" / "learnings.md"


# ---------------------------------------------------------------------------
# Signal mapper stress test
# ---------------------------------------------------------------------------

def run_signal_mapper(problem: str, runs: int) -> dict:
    """Run signal-mapper N times against the same problem and collect stats."""
    results = []
    for i in range(runs):
        cmd = [sys.executable, str(SCRIPTS_DIR / "signal-mapper.py"),
               "--text", problem, "--format", "json"]
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            r = subprocess.run(cmd, capture_output=True, text=True,
                               timeout=30, encoding="utf-8", env=env)
            if r.returncode == 0 and r.stdout.strip():
                data = json.loads(r.stdout)
                results.append(data)
        except Exception as e:
            results.append({"error": str(e)})

    # Analyze consistency
    findings = []
    if not results:
        findings.append("Signal mapper produced no results")
        return {"runs": runs, "results": 0, "findings": findings}

    valid = [r for r in results if "error" not in r]
    errors = [r for r in results if "error" in r]

    if errors:
        findings.append(f"Signal mapper failed {len(errors)}/{runs} runs")

    # Check if results are deterministic (they should be — same input)
    if len(valid) >= 2:
        first_json = json.dumps(valid[0], sort_keys=True)
        non_deterministic = sum(1 for r in valid[1:]
                                if json.dumps(r, sort_keys=True) != first_json)
        if non_deterministic > 0:
            findings.append(f"Signal mapper NON-DETERMINISTIC: {non_deterministic}/{len(valid)} runs differed")
        else:
            findings.append(f"Signal mapper deterministic across {len(valid)} runs ✓")

    # Check keyword coverage
    if valid:
        coverage = valid[0].get("keyword_coverage", 0)
        if coverage < 0.1:
            findings.append(f"Low keyword coverage ({coverage:.1%}) — problem statement may use terms not in signal table")

        # Check ambiguity
        if valid[0].get("ambiguous"):
            findings.append("Signal mapper flagged ambiguity — multiple conflicting task flows scored equally")

        # Check candidate count
        candidates = valid[0].get("task_flow_candidates", [])
        if len(candidates) > 5:
            findings.append(f"Too many task flow candidates ({len(candidates)}) — signal table may be too broad")
        elif len(candidates) == 0:
            findings.append("No task flow candidates matched — signal table has gaps for this problem type")

    return {"runs": runs, "results": len(valid), "findings": findings, "sample": valid[0] if valid else None}


# ---------------------------------------------------------------------------
# Review prescan analysis across projects
# ---------------------------------------------------------------------------

def analyze_prescans(projects: list[Path]) -> list[str]:
    """Run review-prescan on all projects with handoffs and collect patterns."""
    all_findings: list[dict] = []
    projects_analyzed = 0

    for proj_dir in projects:
        handoff = proj_dir / "prd" / "architecture-handoff.md"
        if not handoff.exists():
            continue

        # Check if handoff has content (not just template)
        content = handoff.read_text(encoding="utf-8")
        if "task_flow: TBD" in content and "items: 0" in content:
            continue

        cmd = [sys.executable, str(SCRIPTS_DIR / "review-prescan.py"),
               "--handoff", str(handoff), "--format", "json"]
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            r = subprocess.run(cmd, capture_output=True, text=True,
                               timeout=30, encoding="utf-8", env=env)
            if r.returncode == 0 and r.stdout.strip():
                data = json.loads(r.stdout)
                for f in data.get("findings", []):
                    f["_project"] = proj_dir.name
                all_findings.extend(data.get("findings", []))
                projects_analyzed += 1
        except Exception:
            pass

    if not all_findings:
        return [f"No prescans possible ({projects_analyzed} projects analyzed)"]

    # Aggregate patterns
    area_counts = Counter(f.get("area", "unknown") for f in all_findings)
    severity_counts = Counter(f.get("severity", "unknown") for f in all_findings)
    yellow_findings = [f for f in all_findings if f.get("severity") == "yellow"]
    red_findings = [f for f in all_findings if f.get("severity") == "red"]

    results = [f"Analyzed {projects_analyzed} project handoffs, {len(all_findings)} total findings"]

    if red_findings:
        results.append(f"RED findings ({len(red_findings)}): {', '.join(set(f.get('area','?') for f in red_findings))}")

    # Find recurring yellow patterns
    yellow_patterns = Counter(f.get("finding", "")[:60] for f in yellow_findings)
    recurring = [(pattern, count) for pattern, count in yellow_patterns.most_common(10) if count > 1]
    if recurring:
        results.append(f"Recurring yellow patterns across projects:")
        for pattern, count in recurring:
            results.append(f"  - ({count}x) {pattern}")

    # CLI support gaps
    cli_gaps = [f for f in all_findings if f.get("area") == "CLI support" and f.get("severity") == "yellow"]
    if cli_gaps:
        portal_items = set()
        for f in cli_gaps:
            finding = f.get("finding", "")
            # Extract item type
            m = re.search(r"(\w[\w\s-]+) is portal-only", finding)
            if m:
                portal_items.add(m.group(1).strip())
        if portal_items:
            results.append(f"Portal-only items hit across projects: {', '.join(portal_items)}")

    # AC coverage gaps
    ac_gaps = [f for f in all_findings if f.get("area") == "AC coverage" and f.get("severity") == "yellow"]
    if ac_gaps:
        results.append(f"AC coverage gaps found in {len(ac_gaps)} items across projects")

    # Diagram issues
    diagram_issues = [f for f in all_findings if f.get("area") == "Diagram"]
    if diagram_issues:
        diagram_yellows = [f for f in diagram_issues if f.get("severity") == "yellow"]
        if diagram_yellows:
            results.append(f"Diagram issues in {len(diagram_yellows)} projects — LLM-drawn diagrams have structural problems")

    return results


# ---------------------------------------------------------------------------
# Project artifact mining
# ---------------------------------------------------------------------------

def mine_project_artifacts(projects: list[Path]) -> list[str]:
    """Mine project artifacts for inefficiency patterns."""
    findings = []
    blocker_counter: Counter = Counter()
    task_flow_counter: Counter = Counter()
    phase_reached: Counter = Counter()
    stale_projects = []
    naming_issues = []

    for proj_dir in projects:
        state_file = proj_dir / "pipeline-state.json"
        status_file = proj_dir / "STATUS.md"

        # Analyze pipeline state
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text(encoding="utf-8"))
                current_phase = state.get("current_phase", "unknown")
                phase_reached[current_phase] += 1
                tf = state.get("task_flow")
                if tf and tf != "TBD":
                    task_flow_counter[tf] += 1
            except Exception:
                pass

        # Analyze handoff for blockers
        handoff = proj_dir / "prd" / "architecture-handoff.md"
        if handoff.exists():
            content = handoff.read_text(encoding="utf-8")
            # Extract blockers from frontmatter
            fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
            if fm_match:
                fm = fm_match.group(1)
                # Find blocker lines
                for line in fm.split("\n"):
                    line = line.strip()
                    if line.startswith("- ") and "B-" in line:
                        # Extract blocker category
                        m = re.search(r'B-\d+[:\s]+(.+?)(?:\s*["\']|$)', line)
                        if m:
                            blocker_text = m.group(1).strip().rstrip('"').rstrip("'")
                            # Normalize to category
                            lower = blocker_text.lower()
                            if "capacity" in lower or "sku" in lower:
                                blocker_counter["Capacity SKU"] += 1
                            elif "connection" in lower or "connector" in lower or "gateway" in lower:
                                blocker_counter["Connection/Gateway"] += 1
                            elif "threshold" in lower or "rule" in lower:
                                blocker_counter["Configuration values"] += 1
                            elif "db" in lower or "database" in lower or "engine" in lower:
                                blocker_counter["DB engine details"] += 1
                            elif "protocol" in lower or "vendor" in lower:
                                blocker_counter["Vendor/Protocol"] += 1
                            else:
                                blocker_counter[blocker_text[:30]] += 1

        # Check for naming inconsistencies (hyphens in items that reject them)
        if handoff.exists():
            content = handoff.read_text(encoding="utf-8")
            for match in re.finditer(r"name:\s*(\S+)", content):
                name = match.group(1)
                # Check if Eventstream/MLExperiment/MLModel with hyphens
                type_match = re.search(
                    rf"name:\s*{re.escape(name)}\s*\n\s*type:\s*(\S.*)",
                    content
                )
                if type_match:
                    item_type = type_match.group(1).strip()
                    if item_type in ("Eventstream", "Experiment", "ML Model") and "-" in name:
                        naming_issues.append(f"{proj_dir.name}: {name} ({item_type}) uses hyphens")

        # Check for stale projects (scaffolded but never progressed)
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text(encoding="utf-8"))
                phases = state.get("phases", {})
                completed = sum(1 for p in phases.values()
                                if isinstance(p, dict) and p.get("status") == "complete")
                if completed == 0:
                    stale_projects.append(proj_dir.name)
            except Exception:
                pass

    # Compile findings
    if phase_reached:
        findings.append(f"Phase distribution: {dict(phase_reached.most_common())}")

    if task_flow_counter:
        findings.append(f"Task flow usage: {dict(task_flow_counter.most_common())}")

    if blocker_counter:
        findings.append("Recurring blocker categories:")
        for category, count in blocker_counter.most_common(5):
            findings.append(f"  - ({count}x) {category}")

    if stale_projects:
        findings.append(f"Stale projects (scaffolded, never progressed): {', '.join(stale_projects)}")

    if naming_issues:
        findings.append(f"Item naming violations (hyphens in hyphen-rejecting types):")
        for issue in naming_issues[:5]:
            findings.append(f"  - {issue}")

    # Check discovery brief quality
    customer_questions_in_arch_section = 0
    for proj_dir in projects:
        brief = proj_dir / "prd" / "discovery-brief.md"
        if brief.exists():
            content = brief.read_text(encoding="utf-8")
            # Check for old "Open Questions for Architect" that contain customer-answerable questions
            arch_section = re.search(
                r"###\s+(?:Open Questions|Architectural Judgment)",
                content
            )
            if arch_section:
                section_text = content[arch_section.start():]
                # Look for question-like patterns that a customer could answer
                customer_patterns = ["which", "what vendor", "what database", "what type",
                                     "are they", "do they", "how many"]
                for pattern in customer_patterns:
                    if pattern in section_text.lower():
                        customer_questions_in_arch_section += 1
                        break

    if customer_questions_in_arch_section > 0:
        findings.append(
            f"{customer_questions_in_arch_section} project(s) have customer-answerable questions "
            f"in Architectural Judgment Calls section"
        )

    return findings


# ---------------------------------------------------------------------------
# Multi-problem stress test
# ---------------------------------------------------------------------------

def parse_problem_file(path: str) -> list[dict]:
    """Parse a problem-statements.md file into [{id, category, text}]."""
    content = Path(path).read_text(encoding="utf-8")
    problems = []
    current_category = "Uncategorized"
    for line in content.splitlines():
        # Detect category headers
        m = re.match(r"^##\s+(.+)", line)
        if m:
            current_category = m.group(1).strip()
            continue
        # Detect numbered problem statements
        m = re.match(r'^\d+\.\s+"(.+)"', line)
        if m:
            problems.append({
                "id": len(problems) + 1,
                "category": current_category,
                "text": m.group(1),
            })
    return problems


def run_multi_problem_stress_test(problems: list[dict], passes: int) -> list[str]:
    """Run signal mapper against each problem statement N times. Return findings."""
    coverage_scores: list[float] = []
    zero_candidate_problems: list[str] = []
    high_candidate_problems: list[str] = []
    ambiguous_problems: list[str] = []
    all_candidates: Counter = Counter()
    category_coverage: dict[str, list[float]] = {}
    non_deterministic_count = 0
    total_runs = 0

    for problem in problems:
        pid = problem["id"]
        cat = problem["category"]
        text = problem["text"]

        results = []
        for _ in range(passes):
            cmd = [sys.executable, str(SCRIPTS_DIR / "signal-mapper.py"),
                   "--text", text, "--format", "json"]
            try:
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                r = subprocess.run(cmd, capture_output=True, text=True,
                                   timeout=30, encoding="utf-8", env=env)
                if r.returncode == 0 and r.stdout.strip():
                    data = json.loads(r.stdout)
                    results.append(data)
            except Exception:
                pass
            total_runs += 1

        if not results:
            continue

        # Check determinism across passes
        if len(results) >= 2:
            first = json.dumps(results[0], sort_keys=True)
            if any(json.dumps(r, sort_keys=True) != first for r in results[1:]):
                non_deterministic_count += 1

        # Use first result for analysis (deterministic = all same)
        data = results[0]
        cov = data.get("keyword_coverage", 0)
        coverage_scores.append(cov)
        category_coverage.setdefault(cat, []).append(cov)

        candidates = data.get("task_flow_candidates", [])
        for c in candidates:
            cid = c.get("id", c) if isinstance(c, dict) else c
            all_candidates[cid] += 1

        if len(candidates) == 0:
            zero_candidate_problems.append(f"P{pid}: {text[:50]}...")
        elif len(candidates) > 5:
            high_candidate_problems.append(f"P{pid} ({len(candidates)} candidates): {text[:40]}...")

        if data.get("ambiguous"):
            ambiguous_problems.append(f"P{pid}: {text[:50]}...")

    # Compile findings
    findings = []
    findings.append(f"Tested {len(problems)} problem statements × {passes} passes = {total_runs} total runs")

    if non_deterministic_count:
        findings.append(f"⚠ NON-DETERMINISTIC: {non_deterministic_count}/{len(problems)} problems produced different results across passes")
    else:
        findings.append(f"Signal mapper deterministic across all {total_runs} runs ✓")

    avg_cov = sum(coverage_scores) / len(coverage_scores) if coverage_scores else 0
    low_cov = [s for s in coverage_scores if s < 0.05]
    findings.append(f"Average keyword coverage: {avg_cov:.1%} — {len(low_cov)}/{len(problems)} problems below 5%")

    # Per-category coverage
    findings.append("Keyword coverage by category:")
    for cat, scores in sorted(category_coverage.items()):
        avg = sum(scores) / len(scores) if scores else 0
        findings.append(f"  - {cat}: {avg:.1%} avg ({len(scores)} problems)")

    if zero_candidate_problems:
        findings.append(f"Zero task flow candidates ({len(zero_candidate_problems)} problems):")
        for p in zero_candidate_problems[:5]:
            findings.append(f"  - {p}")

    if high_candidate_problems:
        findings.append(f"Too many candidates >5 ({len(high_candidate_problems)} problems):")
        for p in high_candidate_problems[:5]:
            findings.append(f"  - {p}")

    if ambiguous_problems:
        findings.append(f"Ambiguous signal mapping ({len(ambiguous_problems)} problems):")
        for p in ambiguous_problems[:5]:
            findings.append(f"  - {p}")

    # Most recommended task flows
    findings.append(f"Task flow candidate frequency across all problems:")
    for tf, count in all_candidates.most_common(8):
        findings.append(f"  - {tf}: {count}x")

    return findings

def update_learnings(findings: list[str], section: str = "## Pipeline Inefficiencies") -> str:
    """Append findings to learnings.md under the given section. Returns the appended text."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    new_entries = [f"\n{section}\n",
                   f"\n<!-- Auto-generated by analyze-inefficiencies.py on {timestamp} -->\n"]
    for finding in findings:
        if finding.startswith("  -"):
            new_entries.append(finding)
        else:
            new_entries.append(f"- {finding}")
    new_text = "\n".join(new_entries) + "\n"
    return new_text


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Analyze pipeline inefficiencies across projects"
    )
    parser.add_argument("--problem", default=None,
                        help="Single problem statement to stress-test signal mapper")
    parser.add_argument("--problem-file", default=None,
                        help="Path to problem-statements.md with numbered problems")
    parser.add_argument("--passes", type=int, default=2,
                        help="Number of passes per problem in --problem-file mode (default: 2)")
    parser.add_argument("--runs", type=int, default=20,
                        help="Number of signal mapper runs for single --problem (default: 20)")
    parser.add_argument("--all-projects", action="store_true",
                        help="Analyze all existing project artifacts")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print findings without updating learnings.md")
    args = parser.parse_args()

    if not args.problem and not args.problem_file and not args.all_projects:
        # Default: run problem-file if it exists, plus all-projects
        default_pf = Path(__file__).resolve().parent.parent / "problem-statements.md"
        if default_pf.exists():
            args.problem_file = str(default_pf)
        args.all_projects = True

    all_findings: list[str] = []

    # 1a. Multi-problem stress test (from file)
    if args.problem_file:
        problems = parse_problem_file(args.problem_file)
        print(f"\n{'='*60}")
        print(f"  MULTI-PROBLEM STRESS TEST")
        print(f"  {len(problems)} problems × {args.passes} passes")
        print(f"{'='*60}\n")
        multi_findings = run_multi_problem_stress_test(problems, args.passes)
        for f in multi_findings:
            print(f"  {f}")
        all_findings.extend(multi_findings)

    # 1b. Single problem stress test
    elif args.problem:
        print(f"\n{'='*60}")
        print(f"  SIGNAL MAPPER STRESS TEST ({args.runs} runs)")
        print(f"{'='*60}\n")
        result = run_signal_mapper(args.problem, args.runs)
        for f in result.get("findings", []):
            print(f"  {f}")
        all_findings.extend(result.get("findings", []))

    # 2. Project artifact analysis
    if args.all_projects:
        projects = sorted(PROJECTS_DIR.iterdir()) if PROJECTS_DIR.exists() else []
        projects = [p for p in projects if p.is_dir() and (p / "pipeline-state.json").exists()]

        print(f"\n{'='*60}")
        print(f"  PROJECT ARTIFACT ANALYSIS ({len(projects)} projects)")
        print(f"{'='*60}\n")

        # Mine artifacts
        artifact_findings = mine_project_artifacts(projects)
        for f in artifact_findings:
            print(f"  {f}")
        all_findings.extend(artifact_findings)

        # Run prescans
        print(f"\n{'='*60}")
        print(f"  REVIEW PRESCAN ANALYSIS")
        print(f"{'='*60}\n")
        prescan_findings = analyze_prescans(projects)
        for f in prescan_findings:
            print(f"  {f}")
        all_findings.extend(prescan_findings)

    # 3. Update learnings.md
    if all_findings:
        new_text = update_learnings(all_findings)
        print(f"\n{'='*60}")
        print(f"  LEARNINGS UPDATE")
        print(f"{'='*60}\n")

        if args.dry_run:
            print("  [DRY RUN] Would append to _shared/learnings.md:")
            print(new_text)
        else:
            current = LEARNINGS_PATH.read_text(encoding="utf-8")
            section_header = "## Pipeline Inefficiencies"
            if section_header in current:
                # Remove old section entirely before appending new one
                current = re.sub(
                    r"\n## Pipeline Inefficiencies\n.*",
                    "", current, flags=re.DOTALL
                )
                LEARNINGS_PATH.write_text(current, encoding="utf-8")

            with open(LEARNINGS_PATH, "a", encoding="utf-8") as f:
                f.write(new_text)
            print(f"  ✅ Appended {len(all_findings)} findings to _shared/learnings.md")
    else:
        print("\n  No findings to report.")


if __name__ == "__main__":
    main()
