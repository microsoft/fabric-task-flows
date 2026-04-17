#!/usr/bin/env python3
"""
Heal orchestrator — drives the self-healing loop by coordinating between
the /fabric-heal skill (LLM) and deterministic scripts.

Workflow per iteration:
  1. Generate prompt for /fabric-heal Mode 1 → agent writes problem-statements.md
  2. Benchmark signal-mapper against generated problems (deterministic)
  3. Find uncovered keywords (deterministic)
  4. Generate prompt for /fabric-heal Mode 2 → agent patches signal-mapper.py
  5. Re-benchmark to measure improvement delta
  6. Log results

Usage:
    python .github/skills/fabric-heal/scripts/heal-orchestrator.py                    # 10 iterations
    python .github/skills/fabric-heal/scripts/heal-orchestrator.py --iterations 5     # custom count
    python .github/skills/fabric-heal/scripts/heal-orchestrator.py --dry-run           # measure only, no patches
    python .github/skills/fabric-heal/scripts/heal-orchestrator.py --problems-only     # generate problems only
    python .github/skills/fabric-heal/scripts/heal-orchestrator.py --no-agent          # fallback: template generation
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "_shared" / "lib"))
import bootstrap  # noqa: F401
from paths import REPO_ROOT
from heal_keyword_utils import find_uncovered_keywords

SIGNAL_MAPPER_PATH = REPO_ROOT / ".github" / "skills" / "fabric-discover" / "scripts" / "signal-mapper.py"
SKILL_DIR = Path(__file__).resolve().parent.parent  # .github/skills/fabric-heal/
PROBLEMS_PATH = SKILL_DIR / "problem-statements.md"
LEARNINGS_PATH = REPO_ROOT / "_shared" / "learnings.md"
RESULTS_PATH = SKILL_DIR / "scripts" / "_heal-loop-results.json"
BACKUP_PATH = SKILL_DIR / "problem-statements.md.bak"

# Category rotation for agent prompts — loaded from shared config
_SCRIPT_CONFIG_PATH = REPO_ROOT / "_shared" / "registry" / "script-config.json"
with open(_SCRIPT_CONFIG_PATH, encoding="utf-8") as _f:
    _script_config = json.load(_f)
CATEGORY_ROTATION: list[list[str]] = _script_config["category_rotation"]["values"]

# Fallback templates for --no-agent mode (preserved from heal-loop.py)
_FALLBACK_TEMPLATES = [
    ("Retail AI", "We're a {size} retailer. Our {source} data needs {velocity} analytics for {goal}. Team skill level: {skill}."),
    ("Finance Risk", "Our {size} financial firm needs to {goal} using data from {source}. Regulatory deadline is {deadline}. We use {platform} today."),
    ("Healthcare", "We're a {size} healthcare system. We need to {goal} with data from {source}. Must maintain {compliance}. Our team knows {skill}."),
    ("Manufacturing", "Our {size} manufacturing operation has {source} producing {volume}. We need {velocity} {goal}. Engineers prefer {skill}."),
    ("Energy", "We're a {size} energy company with {source}. We need {goal} with {velocity} requirements. Budget is {budget}."),
]

_FALLBACK_FILLS = {
    "size": ["mid-size", "Fortune 1000", "startup", "global", "regional"],
    "source": ["ERP and CRM", "IoT sensors and SCADA", "flat files and APIs",
               "Snowflake and on-prem SQL", "Databricks and ADLS"],
    "velocity": ["real-time", "near-real-time", "daily batch",
                 "both batch and real-time", "weekly"],
    "goal": ["customer churn prediction", "operational dashboards",
             "regulatory compliance reporting", "predictive maintenance",
             "demand forecasting"],
    "skill": ["SQL only", "Python and SQL", "no-code / Power BI only",
              "Spark and Scala", "mixed — some code, some no-code"],
    "deadline": ["Q4 this year", "90 days", "next fiscal year",
                 "ASAP — audit coming", "no hard deadline"],
    "platform": ["Azure SQL + Power BI", "Snowflake + Tableau",
                 "on-prem SQL Server + SSRS", "Databricks + Looker",
                 "Google BigQuery + Data Studio"],
    "compliance": ["HIPAA", "SOX", "GDPR", "PCI-DSS", "no specific compliance"],
    "volume": ["10GB per day", "500GB per day", "5TB per day",
               "100MB per day", "2TB per week"],
    "budget": ["tight — under $5K/month", "$20K/month",
               "flexible — just prove ROI", "$100K/year total",
               "not discussed yet"],
}


# ---------------------------------------------------------------------------
# Problem parsing (reuse from self-heal.py)
# ---------------------------------------------------------------------------


def _resolve_benchmark_project() -> str | None:
    """Pick a scaffolded project for discovery-mode mapper benchmarking."""
    projects_dir = REPO_ROOT / "_projects"
    if not projects_dir.is_dir():
        return None
    candidates = sorted(p.name for p in projects_dir.iterdir() if p.is_dir())
    return candidates[0] if candidates else None

def parse_problems(path: Path) -> list[dict]:
    """Parse problem-statements.md into [{id, category, text}]."""
    content = path.read_text(encoding="utf-8")
    problems = []
    category = "Uncategorized"
    for line in content.splitlines():
        m = re.match(r"^##\s+(.+)", line)
        if m:
            category = m.group(1).strip()
            continue
        m = re.match(r'^\d+\.\s+"(.+)"', line)
        if m:
            problems.append({
                "id": len(problems) + 1,
                "category": category,
                "text": m.group(1),
            })
    return problems


# ---------------------------------------------------------------------------
# Signal mapper benchmark
# ---------------------------------------------------------------------------

def benchmark_signal_mapper(problems: list[dict]) -> dict:
    """Run signal mapper against all problems and collect metrics."""
    coverage_scores: list[float] = []
    zero_candidates = 0
    lambda_suggested = 0
    ambiguous_count = 0
    total_candidates = 0
    category_coverage: dict[str, list[float]] = {}
    tf_suggestion_counts: Counter = Counter()
    tf_top_counts: Counter = Counter()

    benchmark_project = _resolve_benchmark_project()

    for p in problems:
        cmd = [sys.executable, str(SIGNAL_MAPPER_PATH), "--text", p["text"], "--format", "json"]
        if benchmark_project:
            cmd.extend(["--project", benchmark_project])
        else:
            cmd.append("--intake")
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        try:
            r = subprocess.run(cmd, capture_output=True, text=True,
                               timeout=30, encoding="utf-8", env=env)
            if r.returncode == 0 and r.stdout.strip():
                data = json.loads(r.stdout)
                # Native mapper mode returns full signal objects.
                signals = data.get("signals", [])
                candidates = data.get("task_flow_candidates", [])
                cov = data.get("keyword_coverage", 0)
                # Defensive fallback if intake-shaped payload appears.
                if not signals and data.get("signals_detected"):
                    signals = data.get("signals_detected", [])
                if not cov and signals:
                    conf_scores = {"high": 1.0, "medium": 0.5, "low": 0.2}
                    cov = sum(conf_scores.get(s.get("confidence", "low"), 0.1) for s in signals) / max(len(signals), 1)

                coverage_scores.append(cov)
                category_coverage.setdefault(p["category"], []).append(cov)

                if not candidates and not signals:
                    zero_candidates += 1
                elif candidates:
                    tf_top_counts[candidates[0]["id"]] += 1
                    seen: set[str] = set()
                    for c in candidates:
                        tid = c["id"]
                        if tid not in seen:
                            tf_suggestion_counts[tid] += 1
                            seen.add(tid)
                total_candidates += len(candidates)
                if any(c.get("id") in ("lambda", "event-medallion")
                       for c in candidates):
                    lambda_suggested += 1
                # Check signals for lambda/streaming
                if any("lambda" in s.get("signal", "").lower() or
                       "streaming" in s.get("signal", "").lower()
                       for s in signals):
                    lambda_suggested += 1 if not candidates else 0
                if data.get("ambiguous"):
                    ambiguous_count += 1
            else:
                coverage_scores.append(0)
                zero_candidates += 1
        except Exception as e:
            print(f"⚠ signal-mapper benchmark failed for '{p.get('id', '?')}': {e}", file=sys.stderr)
            coverage_scores.append(0)
            zero_candidates += 1

    avg_coverage = (sum(coverage_scores) / len(coverage_scores)
                    if coverage_scores else 0)
    cat_avgs = {cat: sum(s) / len(s) for cat, s in category_coverage.items()}

    return {
        "avg_coverage": avg_coverage,
        "zero_candidates": zero_candidates,
        "lambda_suggested": lambda_suggested,
        "ambiguous": ambiguous_count,
        "total_problems": len(problems),
        "avg_candidates_per_problem": (total_candidates / len(problems)
                                       if problems else 0),
        "category_coverage": cat_avgs,
        "tf_suggestion_counts": dict(tf_suggestion_counts),
        "tf_top_counts": dict(tf_top_counts),
    }


# ---------------------------------------------------------------------------
# Distribution report
# ---------------------------------------------------------------------------

DEPLOYMENT_REGISTRY = REPO_ROOT / "_shared" / "registry" / "deployment-order.json"
ITEM_TYPE_REGISTRY = REPO_ROOT / "_shared" / "registry" / "item-type-registry.json"
_BAR_CHAR = "\u2588"  # █

FLOW_PATTERN_MAP = {
    "app-backend": "App/API",
    "basic-data-analytics": "Batch",
    "basic-machine-learning-models": "ML",
    "conversational-analytics": "AI/Conversational",
    "data-analytics-sql-endpoint": "Batch",
    "event-analytics": "Streaming",
    "event-medallion": "Hybrid (Batch+Streaming)",
    "lambda": "Hybrid (Batch+Streaming)",
    "medallion": "Batch",
    "semantic-governance": "Governance",
    "sensitive-data-insights": "Governance",
    "translytical": "App/API",
}


def _normalize_item_type(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def _bar_for_pct(pct: float) -> str:
    return _BAR_CHAR * int(pct / 2)


def _print_counter_table(title: str, label: str, counter: Counter,
                         total: int, top_n: int = 12) -> None:
    print(f"\n  {title}  [{total} samples]")
    print(f"  {label:<35} {'Count':>5} {'Rate':>7}  Distribution")
    print(f"  {'-' * 35} {'-' * 5} {'-' * 7}  {'-' * 36}")
    for key, cnt in counter.most_common(top_n):
        pct = cnt / total * 100 if total else 0
        print(f"  {key:<35} {cnt:>5} {pct:>6.1f}%  {_bar_for_pct(pct)}")


def _load_item_type_skillset_map() -> dict[str, list[str]]:
    """Build normalized item-type -> skillset mapping from registry metadata."""
    mapping: dict[str, list[str]] = {}
    try:
        reg = json.loads(ITEM_TYPE_REGISTRY.read_text(encoding="utf-8"))
        for type_key, meta in reg.get("types", {}).items():
            skillset = [str(s) for s in meta.get("skillset", [])]
            names = {type_key, meta.get("display_name", "")}
            names.update(meta.get("aliases", []))
            for n in names:
                if n:
                    mapping[_normalize_item_type(str(n))] = skillset
    except Exception as e:
        print(f"⚠ item-type-registry load failed: {e}", file=sys.stderr)
    return mapping


def _load_item_details() -> dict[str, dict]:
    """Load item/wave/storage details per task flow from deployment registry."""
    details: dict[str, dict] = {}
    skillset_map = _load_item_type_skillset_map()
    try:
        reg = json.loads(DEPLOYMENT_REGISTRY.read_text(encoding="utf-8"))
        for tf_id, tf_data in reg.get("taskFlows", {}).items():
            items = tf_data.get("items", [])
            waves: set[str] = set()
            item_types: list[str] = []
            skillset_counts: Counter = Counter()
            for item in items:
                order = item.get("order", "")
                waves.add(re.sub(r"[a-z]$", "", order))
                item_type = item.get("itemType", "?")
                item_types.append(item_type)
                normalized = _normalize_item_type(item_type)
                for skill in skillset_map.get(normalized, []):
                    skillset_counts[skill] += 1

            if {"LC", "CF"}.issubset(set(skillset_counts.keys())):
                flow_skillset = "Mixed LC/CF"
            elif skillset_counts.get("CF", 0) > 0 and skillset_counts.get("LC", 0) == 0:
                flow_skillset = "Code-First"
            elif skillset_counts.get("LC", 0) > 0 and skillset_counts.get("CF", 0) == 0:
                flow_skillset = "Low-Code"
            elif skillset_counts:
                flow_skillset = "Portal/Auto"
            else:
                flow_skillset = "Unknown"

            details[tf_id] = {
                "items": len(items),
                "waves": len(waves),
                "storage": tf_data.get("primaryStorage", "N/A"),
                "item_types": item_types,
                "skillset_counts": dict(skillset_counts),
                "flow_skillset": flow_skillset,
                "pattern": FLOW_PATTERN_MAP.get(tf_id, "Other"),
            }
    except Exception as e:
        print(f"⚠ deployment-registry load failed: {e}", file=sys.stderr)
    return details


def _build_recommendations(
    total_problems: int,
    agg_suggestion: Counter,
    agg_top: Counter,
    agg_uncovered: Counter,
    results: list[dict],
) -> list[str]:
    """Generate deterministic recommendations from benchmark distributions."""
    recs: list[str] = []
    if total_problems <= 0:
        return ["No benchmark data available — run healer with at least one problem."]

    if agg_top:
        top_flow, top_count = agg_top.most_common(1)[0]
        top_pct = top_count / total_problems
        if top_pct >= 0.60:
            recs.append(
                f"Top-candidate skew is high ({top_flow} at {top_pct:.1%}); add contrasting keywords to improve pattern diversity."
            )

    if agg_suggestion and len(agg_suggestion) < 3:
        recs.append("Only a few task flow patterns are surfacing; expand synonyms for ingestion, velocity, and governance signals.")

    total_zeros = sum(r.get("zero_candidates", 0) for r in results)
    zero_rate = total_zeros / total_problems
    if zero_rate >= 0.10:
        recs.append(
            f"Zero-candidate rate is {zero_rate:.1%}; prioritize adding recurring uncovered terms to reduce unmapped prompts."
        )

    avg_cov = sum(r.get("coverage_before", 0.0) for r in results) / max(len(results), 1)
    if avg_cov < 0.40:
        recs.append(
            f"Average coverage is {avg_cov:.1%}; increase signal keyword breadth for storage, processing, and distribution intent."
        )

    streaming_terms = {"stream", "streaming", "real-time", "event", "telemetry", "kafka"}
    uncovered_tokens = {t.lower() for t, _ in agg_uncovered.most_common(20)}
    if uncovered_tokens & streaming_terms:
        recs.append("Streaming-related terms are frequently uncovered; expand event/streaming keyword aliases for hybrid routing.")

    if not recs:
        recs.append("Coverage and distribution look balanced; continue periodic healing runs and track trends in _heal-loop-results.json.")
    return recs[:5]


def print_distribution_report(
    total_problems: int,
    agg_suggestion: Counter,
    agg_top: Counter,
) -> dict[str, Any]:
    """Print the full task flow distribution report with item details."""
    item_details = _load_item_details()
    pattern_counts: Counter = Counter()
    flow_skillset_counts: Counter = Counter()
    item_skillset_counts: Counter = Counter()

    for tf, cnt in agg_suggestion.items():
        d = item_details.get(tf, {})
        pattern_counts[d.get("pattern", FLOW_PATTERN_MAP.get(tf, "Other"))] += cnt
        flow_skillset_counts[d.get("flow_skillset", "Unknown")] += cnt
        for skill, scount in d.get("skillset_counts", {}).items():
            item_skillset_counts[skill] += scount * cnt

    print(f"\n{'═' * 90}")
    print("  TASK FLOW DISTRIBUTION REPORT")
    print(f"{'═' * 90}")

    # ── Suggestion rate ────────────────────────────────────────────────
    print(f"\n  SUGGESTION RATE (appeared in candidates)  "
          f"[{total_problems} problems]")
    print(f"  {'Task Flow':<35} {'Count':>5} {'Rate':>7}  Distribution")
    print(f"  {'-' * 35} {'-' * 5} {'-' * 7}  {'-' * 36}")
    for tf, cnt in agg_suggestion.most_common():
        pct = cnt / total_problems * 100 if total_problems else 0
        bar = _BAR_CHAR * int(pct / 2)
        print(f"  {tf:<35} {cnt:>5} {pct:>6.1f}%  {bar}")

    # ── Top candidate ──────────────────────────────────────────────────
    print(f"\n  TOP CANDIDATE (highest score per problem)  "
          f"[{total_problems} problems]")
    print(f"  {'Task Flow':<35} {'Count':>5} {'Rate':>7}  Distribution")
    print(f"  {'-' * 35} {'-' * 5} {'-' * 7}  {'-' * 36}")
    for tf, cnt in agg_top.most_common():
        pct = cnt / total_problems * 100 if total_problems else 0
        bar = _bar_for_pct(pct)
        print(f"  {tf:<35} {cnt:>5} {pct:>6.1f}%  {bar}")

    # ── Pattern and skillset distributions ───────────────────────────────
    if pattern_counts:
        pattern_total = sum(pattern_counts.values())
        _print_counter_table(
            "PATTERN CATEGORY DISTRIBUTION (from suggested flows)",
            "Pattern",
            pattern_counts,
            pattern_total,
            top_n=10,
        )
    if flow_skillset_counts:
        flow_skillset_total = sum(flow_skillset_counts.values())
        _print_counter_table(
            "FLOW SKILLSET DISTRIBUTION (from suggested flows)",
            "Flow Skillset",
            flow_skillset_counts,
            flow_skillset_total,
            top_n=8,
        )
    if item_skillset_counts:
        weighted_total = sum(item_skillset_counts.values())
        _print_counter_table(
            "ITEM SKILLSET MIX (weighted by suggestions)",
            "Skillset",
            item_skillset_counts,
            weighted_total,
            top_n=8,
        )

    # ── Item details ───────────────────────────────────────────────────
    suggested_flows = set(agg_suggestion.keys()) | set(agg_top.keys())
    if item_details and suggested_flows:
        print(f"\n  ITEM DETAILS (suggested task flows)")
        print(f"  {'Task Flow':<35} {'Items':>5} {'Waves':>5}  "
              f"Primary Storage")
        print(f"  {'-' * 35} {'-' * 5} {'-' * 5}  {'-' * 36}")
        for tf in sorted(suggested_flows):
            d = item_details.get(tf)
            if d:
                print(f"  {tf:<35} {d['items']:>5} {d['waves']:>5}  "
                      f"{d['storage']}")
            else:
                print(f"  {tf:<35}     ?     ?  (not in registry)")

        # Item type frequency across all suggested flows
        type_counts: Counter = Counter()
        for tf in suggested_flows:
            d = item_details.get(tf)
            if d:
                for it in d["item_types"]:
                    type_counts[it] += 1
        if type_counts:
            print(f"\n  ITEM TYPE FREQUENCY (across suggested task flows)")
            print(f"  {'Item Type':<35} {'Flows':>5}")
            print(f"  {'-' * 35} {'-' * 5}")
            for it, cnt in type_counts.most_common():
                print(f"  {it:<35} {cnt:>5}")

    print(f"\n{'═' * 90}")
    return {
        "pattern_counts": dict(pattern_counts),
        "flow_skillset_counts": dict(flow_skillset_counts),
        "item_skillset_counts": dict(item_skillset_counts),
    }


# ---------------------------------------------------------------------------
# Agent prompt generation
# ---------------------------------------------------------------------------

def generate_prompt(iteration: int, count: int = 25) -> str:
    """Generate Mode 1 prompt for /fabric-heal to create problem statements."""
    cat_idx = iteration % len(CATEGORY_ROTATION)
    categories = CATEGORY_ROTATION[cat_idx]
    per_cat = count // len(categories)

    # Read current signal mapper keywords for context
    sm_content = SIGNAL_MAPPER_PATH.read_text(encoding="utf-8")
    kw_matches = re.findall(r'"([^"]{2,})"', sm_content)
    sample_keywords = sorted(set(kw_matches))[:50]

    return f"""/fabric-heal Mode 1 — Generate Problem Statements

## Iteration {iteration + 1}

Generate {count} novel, fully-formed problem statements for stress-testing the signal mapper.

### Target Categories for This Batch
{', '.join(categories)}

Use {per_cat} problems per category. Each problem should be a realistic enterprise scenario
with specific details: data volumes, team sizes, tool names, compliance requirements,
deadlines, and business constraints.

### Current Signal Mapper Keywords (sample)
{', '.join(sample_keywords[:30])}

Generate problems that use DIFFERENT terminology than these existing keywords to
expose gaps. For example, if "IoT" is a keyword, use "telemetry sensors" or
"connected devices" instead.

### Output
Write directly to `.github/skills/fabric-heal/problem-statements.md` using the exact format:

```
# Problem Statements for Stress Testing

> Auto-generated batch {iteration + 1} — {count} problems for self-healing loop.

## Category Name

1. "Problem text..."

2. "Problem text..."
```

Each problem must be numbered sequentially (1-{count}) and wrapped in double quotes.
"""


def generate_heal_prompt(iteration: int, metrics: dict,
                         uncovered: list[str]) -> str:
    """Generate Mode 2 prompt for /fabric-heal to patch keywords."""
    return f"""/fabric-heal Mode 2 — Analyze Gaps and Patch Keywords

## Iteration {iteration + 1} Benchmark Results

- Avg keyword coverage: {metrics['avg_coverage']:.1%}
- Zero-candidate problems: {metrics['zero_candidates']}/{metrics['total_problems']}
- Lambda suggested: {metrics['lambda_suggested']}/{metrics['total_problems']}
- Ambiguous: {metrics['ambiguous']}/{metrics['total_problems']}

### Per-Category Coverage
{chr(10).join(f'- {cat}: {cov:.1%}' for cat, cov in sorted(metrics['category_coverage'].items()))}

### Top Uncovered Terms
{', '.join(uncovered)}

### Instructions
1. Read `scripts/signal-mapper.py` to see current keyword categories
2. Map each uncovered term to the most appropriate signal category (1-11)
3. Use `edit` to add keywords to the correct category's `keywords` tuple
4. Max 15 new keywords per category
5. Append a healing history entry to `_shared/learnings.md`
"""


# ---------------------------------------------------------------------------
# Fallback problem generation (--no-agent mode)
# ---------------------------------------------------------------------------

def generate_fallback_batch(batch_idx: int, count: int = 25) -> list[dict]:
    """Generate problems from templates when agent is unavailable."""
    import random
    rng = random.Random(42 + batch_idx)
    problems = []
    for i in range(count):
        tmpl_idx = i % len(_FALLBACK_TEMPLATES)
        cat, template = _FALLBACK_TEMPLATES[tmpl_idx]
        fills = {}
        for key, options in _FALLBACK_FILLS.items():
            fills[key] = rng.choice(options)
        text = template.format(**fills)
        problems.append({"cat": cat, "text": text})
    return problems


def write_problems_file(problems: list[dict], batch_idx: int) -> None:
    """Write problems to problem-statements.md."""
    lines = [
        "# Problem Statements for Stress Testing",
        "",
        f"> Auto-generated batch {batch_idx + 1} — {len(problems)} problems "
        f"for self-healing loop.",
        "",
    ]
    current_cat = None
    for i, p in enumerate(problems):
        if p["cat"] != current_cat:
            current_cat = p["cat"]
            lines.append(f"## {current_cat}")
            lines.append("")
        lines.append(f'{i + 1}. "{p["text"]}"')
        lines.append("")

    PROBLEMS_PATH.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log_summary(results: list[dict], dry_run: bool) -> None:
    """Append aggregate results to learnings.md."""
    if dry_run:
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total_problems = sum(r["problems"] for r in results)
    avg_cov = sum(r["coverage_before"] for r in results) / len(results)
    total_zeros = sum(r["zero_candidates"] for r in results)

    # Collect all unique uncovered terms
    all_uncovered: set[str] = set()
    for r in results:
        all_uncovered.update(r.get("uncovered_terms", []))

    entry = (
        f"\n### Heal Orchestrator Run: {timestamp} "
        f"({len(results)} iterations, {total_problems} problems)\n\n"
        f"- Average coverage across all batches: {avg_cov:.1%}\n"
        f"- Total zero-candidate problems: {total_zeros}/{total_problems}\n"
        f"- Coverage range: "
        f"{min(r['coverage_before'] for r in results):.1%} – "
        f"{max(r['coverage_before'] for r in results):.1%}\n"
    )

    if all_uncovered:
        entry += (f"- Uncovered terms across all batches: "
                  f"{', '.join(sorted(all_uncovered)[:20])}\n")

    # Check for improvement across iterations
    if len(results) >= 2:
        first_cov = results[0]["coverage_before"]
        last_cov = results[-1]["coverage_before"]
        entry += (f"- Coverage trend: {first_cov:.1%} (iter 1) → "
                  f"{last_cov:.1%} (iter {len(results)})\n")

    content = LEARNINGS_PATH.read_text(encoding="utf-8")
    content += entry
    LEARNINGS_PATH.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Main orchestration loop
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Self-healing orchestrator — coordinates /fabric-heal "
                    "skill with deterministic benchmarking scripts"
    )
    parser.add_argument("--iterations", type=int, default=10,
                        help="Number of heal iterations (default: 10)")
    parser.add_argument("--problems", type=int, default=25,
                        help="Problems per iteration (default: 25)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Measure only, don't patch keywords or log")
    parser.add_argument("--problems-only", action="store_true",
                        help="Generate problems only, no healing")
    parser.add_argument("--no-agent", action="store_true",
                        help="Fallback: use template generation instead of agent")
    args = parser.parse_args()

    all_results: list[dict] = []
    agg_suggestion: Counter = Counter()
    agg_top: Counter = Counter()
    agg_uncovered: Counter = Counter()

    # Back up original problem statements
    if PROBLEMS_PATH.exists():
        shutil.copy2(PROBLEMS_PATH, BACKUP_PATH)

    print(f"\n{'═' * 70}")
    print(f"  HEAL ORCHESTRATOR — {args.iterations} iterations × "
          f"{args.problems} problems")
    if args.no_agent:
        print("  Mode: Template fallback (no agent)")
    else:
        print("  Mode: Agent-driven (/fabric-heal)")
    print(f"{'═' * 70}")

    stale_iterations = 0  # early-stop if no new gaps found

    for iteration in range(args.iterations):
        categories = CATEGORY_ROTATION[iteration % len(CATEGORY_ROTATION)]
        print(f"\n{'─' * 70}")
        print(f"  ITERATION {iteration + 1}/{args.iterations}")
        print(f"  Categories: {', '.join(categories[:3])}...")
        print(f"{'─' * 70}")

        # ── Step 1: Generate problems ──────────────────────────────────
        if args.no_agent:
            batch = generate_fallback_batch(iteration, args.problems)
            write_problems_file(batch, iteration)
            print(f"  📝 Generated {len(batch)} problems (template fallback)")
        else:
            prompt = generate_prompt(iteration, args.problems)
            print("\n  ┌─────────────────────────────────────────────┐")
            print("  │  AGENT PROMPT — /fabric-heal Mode 1         │")
            print("  │  Paste the prompt below to the agent,       │")
            print("  │  then press Enter when done.                │")
            print("  └─────────────────────────────────────────────┘\n")
            print(prompt)
            print(f"\n  {'─' * 50}")
            input("  ⏎  Press Enter after the agent has written "
                  "problem-statements.md... ")

        # ── Step 2: Parse and benchmark ────────────────────────────────
        problems = parse_problems(PROBLEMS_PATH)
        if not problems:
            print("  ⚠️  No problems parsed — skipping iteration")
            continue

        print(f"  📊 Benchmarking {len(problems)} problems...")
        metrics = benchmark_signal_mapper(problems)
        print(f"     Coverage:      {metrics['avg_coverage']:.1%}")
        print(f"     Zero-cand:     {metrics['zero_candidates']}/{metrics['total_problems']}")
        print(f"     Lambda:        {metrics['lambda_suggested']}/{metrics['total_problems']}")
        print(f"     Ambiguous:     {metrics['ambiguous']}/{metrics['total_problems']}")

        # Aggregate distribution across iterations
        for tf, cnt in metrics["tf_suggestion_counts"].items():
            agg_suggestion[tf] += cnt
        for tf, cnt in metrics["tf_top_counts"].items():
            agg_top[tf] += cnt

        if args.problems_only:
            result = {
                "iteration": iteration + 1,
                "problems": len(problems),
                "coverage_before": metrics["avg_coverage"],
                "zero_candidates": metrics["zero_candidates"],
                "lambda_suggested": metrics["lambda_suggested"],
                "uncovered_terms": [],
            }
            all_results.append(result)
            continue

        # ── Step 3: Find gaps ──────────────────────────────────────────
        uncovered = find_uncovered_keywords(problems, SIGNAL_MAPPER_PATH)
        for term in uncovered:
            agg_uncovered[term] += 1
        if uncovered:
            print(f"  🔍 Top uncovered: {', '.join(uncovered[:8])}")
        else:
            print("  ✅ No significant uncovered terms")
            stale_iterations += 1

        # Early stop check
        if stale_iterations >= 3:
            print("\n  ⏹️  No new gaps for 3 iterations — early stopping")
            result = {
                "iteration": iteration + 1,
                "problems": len(problems),
                "coverage_before": metrics["avg_coverage"],
                "zero_candidates": metrics["zero_candidates"],
                "lambda_suggested": metrics["lambda_suggested"],
                "uncovered_terms": uncovered[:10],
            }
            all_results.append(result)
            break

        # ── Step 4: Heal (patch keywords) ──────────────────────────────
        after_metrics = None
        if not args.dry_run and uncovered:
            if args.no_agent:
                print("  ⏭️  Skipping heal phase (no agent, template mode)")
            else:
                heal_prompt = generate_heal_prompt(iteration, metrics, uncovered)
                print("\n  ┌─────────────────────────────────────────────┐")
                print("  │  AGENT PROMPT — /fabric-heal Mode 2         │")
                print("  │  Paste the prompt below to the agent,       │")
                print("  │  then press Enter when done.                │")
                print("  └─────────────────────────────────────────────┘\n")
                print(heal_prompt)
                print(f"\n  {'─' * 50}")
                input("  ⏎  Press Enter after the agent has patched "
                      "signal-mapper.py... ")

                # ── Step 5: Re-benchmark after healing ─────────────────
                print("  📊 Re-benchmarking after healing...")
                after_metrics = benchmark_signal_mapper(problems)
                delta = after_metrics["avg_coverage"] - metrics["avg_coverage"]
                print(f"     Coverage:  {metrics['avg_coverage']:.1%} → "
                      f"{after_metrics['avg_coverage']:.1%} "
                      f"({'+' if delta >= 0 else ''}{delta:.1%})")
                stale_iterations = 0  # reset since healing happened

        result = {
            "iteration": iteration + 1,
            "problems": len(problems),
            "coverage_before": metrics["avg_coverage"],
            "coverage_after": (after_metrics["avg_coverage"]
                               if after_metrics else None),
            "zero_candidates": metrics["zero_candidates"],
            "lambda_suggested": metrics["lambda_suggested"],
            "uncovered_terms": uncovered[:10],
        }
        all_results.append(result)

    # ── Summary ────────────────────────────────────────────────────────
    print(f"\n{'═' * 70}")
    print(f"  ORCHESTRATOR SUMMARY — {len(all_results)} iterations")
    print(f"{'═' * 70}")
    print(f"  {'Iter':>4}  {'Coverage':>10}  {'Zero-Cand':>10}  "
          f"{'Lambda':>8}  Top Gaps")
    print(f"  {'────':>4}  {'──────────':>10}  {'──────────':>10}  "
          f"{'────────':>8}  ────────")

    for r in all_results:
        gaps = (", ".join(r["uncovered_terms"][:3])
                if r.get("uncovered_terms") else "—")
        cov_str = f"{r['coverage_before']:.1%}"
        if r.get("coverage_after") is not None:
            cov_str += f"→{r['coverage_after']:.1%}"
        print(f"  {r['iteration']:>4}  {cov_str:>10}  "
              f"{r['zero_candidates']:>10}  "
              f"{r['lambda_suggested']:>8}  {gaps}")

    if all_results:
        avg_cov = sum(r["coverage_before"] for r in all_results) / len(all_results)
        total_zeros = sum(r["zero_candidates"] for r in all_results)
        total_problems = sum(r["problems"] for r in all_results)
        print(f"\n  Average coverage: {avg_cov:.1%}")
        print(f"  Total zero-candidate problems: "
              f"{total_zeros}/{total_problems}")

    # ── Distribution report ────────────────────────────────────────────
    distribution_meta: dict[str, Any] = {}
    if all_results and agg_suggestion:
        total_problems = sum(r["problems"] for r in all_results)
        distribution_meta = print_distribution_report(total_problems, agg_suggestion, agg_top)

    # ── Recommendations ─────────────────────────────────────────────────
    recommendations = _build_recommendations(
        total_problems=sum(r["problems"] for r in all_results),
        agg_suggestion=agg_suggestion,
        agg_top=agg_top,
        agg_uncovered=agg_uncovered,
        results=all_results,
    )
    print(f"\n{'═' * 70}")
    print("  RECOMMENDATIONS")
    print(f"{'═' * 70}")
    for idx, rec in enumerate(recommendations, start=1):
        print(f"  {idx}. {rec}")
    if agg_uncovered:
        print("\n  Frequent uncovered terms:")
        for term, cnt in agg_uncovered.most_common(10):
            pct = (cnt / max(len(all_results), 1)) * 100
            print(f"  - {term:<24} {cnt:>2} loops ({pct:>5.1f}%)")

    # Log to learnings.md
    if not args.dry_run:
        log_summary(all_results, args.dry_run)
        print("\n  ✅ Results logged to _shared/learnings.md")

    # Save detailed results (include distribution data)
    output = {
        "iterations": all_results,
        "distribution": {
            "suggestion_counts": dict(agg_suggestion),
            "top_counts": dict(agg_top),
            "uncovered_term_counts": dict(agg_uncovered),
            "pattern_counts": distribution_meta.get("pattern_counts", {}),
            "flow_skillset_counts": distribution_meta.get("flow_skillset_counts", {}),
            "item_skillset_counts": distribution_meta.get("item_skillset_counts", {}),
            "total_problems": sum(r["problems"] for r in all_results)
                             if all_results else 0,
        },
        "recommendations": recommendations,
    }
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"  📁 Detailed results: {RESULTS_PATH}")

    # Restore original problem statements
    if BACKUP_PATH.exists():
        shutil.copy2(BACKUP_PATH, PROBLEMS_PATH)
        BACKUP_PATH.unlink()
        print("  ♻️  Restored original problem-statements.md")

    # Clean up generated files
    _cleanup_generated_files()

    print(f"\n{'═' * 70}\n")


def _cleanup_generated_files() -> None:
    """Remove generated problem-statement batch files after healing loop."""
    cleaned = 0
    for batch_file in SKILL_DIR.glob("problem-statements-batch*.md"):
        batch_file.unlink()
        cleaned += 1
    if cleaned:
        print(f"  🧹 Cleaned up {cleaned} batch file(s)")


if __name__ == "__main__":
    main()
