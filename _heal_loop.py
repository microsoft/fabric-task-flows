#!/usr/bin/env python3
"""Fast healing loop analysis - imports signal_mapper directly."""

import importlib.util
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
SIGNAL_MAPPER = REPO / ".github" / "skills" / "fabric-discover" / "scripts" / "signal-mapper.py"
PROBLEMS_FILE = REPO / ".github" / "skills" / "fabric-heal" / "problem-statements.md"
REGISTRY = REPO / "_shared" / "registry" / "signal-categories.json"

# Add shared lib to path
sys.path.insert(0, str(REPO / "_shared"))
sys.path.insert(0, str(REPO / "_shared" / "lib"))

# Import signal_mapper via importlib (hyphenated filename)
spec = importlib.util.spec_from_file_location("signal_mapper", SIGNAL_MAPPER)
sm = importlib.util.module_from_spec(spec)
sys.modules["signal_mapper"] = sm
spec.loader.exec_module(sm)


def parse_problems(path):
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
            problems.append({"id": len(problems) + 1, "category": category, "text": m.group(1)})
    return problems


def run_benchmark():
    problems = parse_problems(PROBLEMS_FILE)
    print(f"\n{'='*70}")
    print(f"  SIGNAL MAPPER BENCHMARK — {len(problems)} problems")
    print(f"{'='*70}")

    results = []
    cat_coverage = {}
    zero_candidates = 0
    for p in problems:
        r = sm.map_signals(p["text"])
        cov = r.get("keyword_coverage", 0)
        candidates = r.get("task_flow_candidates", [])
        signals = r.get("signals", [])
        velocity = r.get("primary_velocity", "none")

        if not candidates:
            zero_candidates += 1

        cat_coverage.setdefault(p["category"], []).append(cov)
        results.append({
            "id": p["id"],
            "category": p["category"],
            "coverage": cov,
            "velocity": velocity,
            "num_candidates": len(candidates),
            "top_candidate": candidates[0]["id"] if candidates else "NONE",
            "signals": [s["signal"] for s in signals],
            "text_preview": p["text"][:80],
        })

    avg_cov = sum(r["coverage"] for r in results) / len(results) if results else 0

    # Summary
    print(f"\n  Avg coverage:       {avg_cov:.1%}")
    print(f"  Zero candidates:    {zero_candidates}/{len(results)}")

    # Per-category breakdown (DISABLED - industry analysis violates core principle)
    # The mapper detects TECH patterns, not industries
    
    # Signal distribution (what matters)
    print(f"\n  SIGNAL DISTRIBUTION:")
    signal_counts = {}
    for r in results:
        for s in r["signals"]:
            signal_counts[s] = signal_counts.get(s, 0) + 1
    for sig, cnt in sorted(signal_counts.items(), key=lambda x: -x[1]):
        pct = cnt / len(results) * 100
        bar = "█" * int(pct / 2)
        print(f"    {sig:<40} {cnt:>3}/{len(results)} ({pct:.0f}%) {bar}")

    # Zero-candidate problems — analyze by TECH INTENT missed
    zero_probs = [r for r in results if r["num_candidates"] == 0]
    if zero_probs:
        print(f"\n  ZERO-CANDIDATE PROBLEMS ({len(zero_probs)}) — tech intent not detected:")
        for r in zero_probs:
            print(f"    #{r['id']:>2}: \"{r['text_preview']}...\"")

    # Bottom 10 weakest problems
    results.sort(key=lambda x: x["coverage"])
    print(f"\n  BOTTOM 10 (lowest coverage):")
    print(f"  {'#':>3} {'Cov':>6} {'Velocity':<12} {'Top Candidate':<20} {'Preview'}")
    print(f"  {'-'*3} {'-'*6} {'-'*12} {'-'*20} {'-'*40}")
    for r in results[:10]:
        print(f"  {r['id']:>3} {r['coverage']:>5.1%} {r['velocity']:<12} {r['top_candidate']:<20} {r['text_preview']}")

    # Count current registry
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    total_kw = sum(len(c.get("keywords", [])) for c in reg["categories"])
    total_ir = sum(len(c.get("inference_rules", [])) for c in reg["categories"])
    print(f"\n  Registry: {total_kw} keywords, {total_ir} inference rules")
    print(f"{'='*70}\n")

    return {
        "avg_coverage": avg_cov,
        "zero_candidates": zero_candidates,
        "total": len(results),
        "results": results,
        "signal_counts": signal_counts,
        "total_kw": total_kw,
        "total_ir": total_ir,
    }


if __name__ == "__main__":
    run_benchmark()
