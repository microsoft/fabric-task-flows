#!/usr/bin/env python3
"""
File size and character count audit for the task-flows repo.

Scans all agent-consumed files (.md, .json, .py, .yml/.yaml), categorises them
by their agent-context role, and prints a console report highlighting
oversized / monolithic files that waste context-window tokens.

Usage:
    # Full report — top 10 per category, default thresholds
    python _shared/scripts/file-audit.py

    # Top 5 per category, custom thresholds
    python _shared/scripts/file-audit.py --top 5 --threshold-kb 20 --threshold-chars 20000

    # Only skill instructions category
    python _shared/scripts/file-audit.py --category skill-instructions

    # Summary totals only
    python _shared/scripts/file-audit.py --summary-only

    # Machine-readable JSON output
    python _shared/scripts/file-audit.py --json

Importable:
    from file_audit import scan_repo, categorize, FileMetrics
"""

from __future__ import annotations

import argparse
import json as json_mod
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

sys.path.insert(0, str(REPO_ROOT / "_shared" / "lib"))
from banner import print_banner  # noqa: E402

# ── Defaults ─────────────────────────────────────────────────────────────────

DEFAULT_EXTENSIONS = {".md", ".json", ".py", ".yml", ".yaml"}
DEFAULT_THRESHOLD_KB = 15
DEFAULT_THRESHOLD_CHARS = 15_000
DEFAULT_TOP_N = 10

# Per-category thresholds for context-sensitive warnings
CATEGORY_CHAR_THRESHOLDS: dict[str, int] = {
    "project-docs": 20_000,
    "registry-data": 15_000,
    "diagrams": 15_000,
    "workflow-guide": 15_000,
}

# ── Data model ───────────────────────────────────────────────────────────────


@dataclass
class FileMetrics:
    """Metrics for a single file."""

    path: str  # relative to repo root
    size_bytes: int
    chars: int
    lines: int
    category: str

    @property
    def size_kb(self) -> float:
        return round(self.size_bytes / 1024, 1)


# ── Categorisation ───────────────────────────────────────────────────────────

# Order matters — first match wins.
_CATEGORY_RULES: list[tuple[str, ...]] = [
    # (category_id, *path_fragments_or_globs)
    ("copilot-instructions", ".github", "copilot-instructions.md"),
    ("agent-instructions", ".github", "agents"),
    ("skill-instructions", ".github", "skills", "SKILL.md"),
    ("skill-references", ".github", "skills", "references"),
    ("skill-schemas", ".github", "skills", "schemas"),
    ("skill-scripts", ".github", "skills", "scripts"),
    ("decision-guides", "decisions"),
    ("diagrams", "diagrams"),
    ("registry-data", "_shared", "registry"),
    ("workflow-guide", "_shared", "workflow-guide.md"),
    ("shared-lib", "_shared", "lib"),
    ("shared-scripts", "_shared", "scripts"),
    ("shared-tests", "_shared", "tests"),
    ("project-docs", "_projects"),
    ("heal-batches", ".github", "skills", "fabric-heal", "problem-statements"),
]

CATEGORY_LABELS: dict[str, str] = {
    "copilot-instructions": "Copilot Instructions (loaded every conversation)",
    "agent-instructions": "Agent Instructions (loaded every conversation)",
    "skill-instructions": "Skill Instructions (loaded on activation)",
    "skill-references": "Skill References (bundled with skill context)",
    "skill-schemas": "Skill Schemas (bundled with skill context)",
    "skill-scripts": "Skill Scripts (executed, not read as context)",
    "decision-guides": "Decision Guides (read during design)",
    "diagrams": "Deployment Diagrams (read during design/deploy)",
    "registry-data": "Registry Data (should use tools, not raw read)",
    "workflow-guide": "Workflow Guide (read by orchestrator)",
    "shared-lib": "Shared Library (imported by scripts)",
    "shared-scripts": "Shared Scripts (executed by pipeline)",
    "shared-tests": "Tests",
    "project-docs": "Project Documents (read during active projects)",
    "heal-batches": "Heal Problem Statements",
    "other": "Other",
}


def categorize_path(rel_path: str) -> str:
    """Return the category ID for a file based on its relative path."""
    normalised = rel_path.replace("\\", "/")
    for rule in _CATEGORY_RULES:
        cat_id = rule[0]
        fragments = rule[1:]
        if all(f in normalised for f in fragments):
            return cat_id
    return "other"


# ── Scanning ─────────────────────────────────────────────────────────────────


def scan_repo(
    root: Path,
    extensions: set[str] | None = None,
) -> list[FileMetrics]:
    """Walk *root* and collect metrics for files matching *extensions*."""
    if extensions is None:
        extensions = DEFAULT_EXTENSIONS

    results: list[FileMetrics] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip hidden/internal dirs (but keep .github)
        dirnames[:] = [
            d
            for d in dirnames
            if d == ".github" or not d.startswith(".")
        ]
        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in extensions:
                continue
            full = Path(dirpath) / fname
            try:
                size = full.stat().st_size
                content = full.read_text(encoding="utf-8", errors="replace")
            except (OSError, PermissionError):
                continue
            rel = str(full.relative_to(root))
            results.append(
                FileMetrics(
                    path=rel,
                    size_bytes=size,
                    chars=len(content),
                    lines=content.count("\n") + (1 if content and not content.endswith("\n") else 0),
                    category=categorize_path(rel),
                )
            )
    return results


def categorize(
    metrics: list[FileMetrics],
) -> dict[str, list[FileMetrics]]:
    """Group *metrics* by category, each list sorted by size descending."""
    groups: dict[str, list[FileMetrics]] = {}
    for m in metrics:
        groups.setdefault(m.category, []).append(m)
    for files in groups.values():
        files.sort(key=lambda f: f.size_bytes, reverse=True)
    return groups


# ── Reporting ────────────────────────────────────────────────────────────────


def _flag(m: FileMetrics, kb_thresh: float, char_thresh: int) -> str:
    """Return a warning flag if thresholds are exceeded."""
    flags = []
    if m.size_kb >= kb_thresh:
        flags.append("size")
    if m.chars >= char_thresh:
        flags.append("chars")
    if flags:
        return " ⚠️  " + "+".join(flags)
    return ""


def _print_table(
    files: list[FileMetrics],
    top_n: int,
    kb_thresh: float,
    char_thresh: int,
) -> None:
    """Print a fixed-width table of file metrics."""
    shown = files[:top_n]
    if not shown:
        print("  (no files)")
        return

    # Column widths
    path_w = min(max(len(f.path) for f in shown), 80)
    header = f"  {'#':>3}  {'Path':<{path_w}}  {'Size KB':>8}  {'Chars':>8}  {'Lines':>6}  Flag"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for i, f in enumerate(shown, 1):
        flag = _flag(f, kb_thresh, char_thresh)
        path_display = f.path if len(f.path) <= path_w else "..." + f.path[-(path_w - 3) :]
        print(
            f"  {i:>3}  {path_display:<{path_w}}  {f.size_kb:>8}  {f.chars:>8}  {f.lines:>6}{flag}"
        )
    remaining = len(files) - top_n
    if remaining > 0:
        print(f"  ... and {remaining} more file(s)")


def print_summary(
    by_ext: dict[str, list[FileMetrics]],
) -> None:
    """Print a one-line-per-extension summary table."""
    print("Extension Summary")
    print("-" * 60)
    print(f"  {'Ext':<8}  {'Files':>6}  {'Total KB':>10}  {'Total Chars':>12}")
    print("  " + "-" * 50)
    total_files = 0
    total_kb = 0.0
    total_chars = 0
    for ext in sorted(by_ext):
        files = by_ext[ext]
        count = len(files)
        kb = round(sum(f.size_bytes for f in files) / 1024, 1)
        chars = sum(f.chars for f in files)
        print(f"  {ext:<8}  {count:>6}  {kb:>10}  {chars:>12}")
        total_files += count
        total_kb += kb
        total_chars += chars
    print("  " + "-" * 50)
    print(f"  {'TOTAL':<8}  {total_files:>6}  {round(total_kb, 1):>10}  {total_chars:>12}")
    print()


def print_threshold_warnings(
    all_files: list[FileMetrics],
    kb_thresh: float,
    char_thresh: int,
) -> None:
    """Print a consolidated list of files exceeding thresholds."""
    flagged = [
        f for f in all_files if f.size_kb >= kb_thresh or f.chars >= char_thresh
    ]
    if not flagged:
        print("✅ No files exceed thresholds.")
        return
    flagged.sort(key=lambda f: f.size_bytes, reverse=True)
    print(f"⚠️  {len(flagged)} file(s) exceed thresholds (≥{kb_thresh} KB or ≥{char_thresh:,} chars):")
    print()
    for f in flagged:
        reasons = []
        if f.size_kb >= kb_thresh:
            reasons.append(f"{f.size_kb} KB")
        if f.chars >= char_thresh:
            reasons.append(f"{f.chars:,} chars")
        print(f"  {f.path}")
        print(f"    → {' | '.join(reasons)}  [{f.category}]")
    print()


def print_context_bloat_warnings(
    all_files: list[FileMetrics],
) -> None:
    """Print warnings for files that exceed per-category context thresholds."""
    flagged = [
        f
        for f in all_files
        if f.category in CATEGORY_CHAR_THRESHOLDS
        and f.chars >= CATEGORY_CHAR_THRESHOLDS[f.category]
    ]
    if not flagged:
        return
    flagged.sort(key=lambda f: f.chars, reverse=True)
    print(f"🧠 {len(flagged)} file(s) exceed context-bloat thresholds (per-category):")
    print()
    for f in flagged:
        thresh = CATEGORY_CHAR_THRESHOLDS[f.category]
        print(f"  {f.path}")
        print(f"    → {f.chars:,} chars (limit: {thresh:,})  [{f.category}]")
    print()


def print_full_report(
    all_files: list[FileMetrics],
    top_n: int,
    kb_thresh: float,
    char_thresh: int,
    category_filter: str | None = None,
) -> None:
    """Print the complete audit report."""
    # Extension summary
    by_ext: dict[str, list[FileMetrics]] = {}
    for f in all_files:
        ext = os.path.splitext(f.path)[1].lower()
        by_ext.setdefault(ext, []).append(f)
    print_summary(by_ext)

    # Per-category tables
    by_cat = categorize(all_files)

    # Deterministic category order
    cat_order = [r[0] for r in _CATEGORY_RULES] + ["other"]
    for cat_id in cat_order:
        if cat_id not in by_cat:
            continue
        if category_filter and cat_id != category_filter:
            continue
        label = CATEGORY_LABELS.get(cat_id, cat_id)
        print(f"── {label} ──")
        _print_table(by_cat[cat_id], top_n, kb_thresh, char_thresh)
        print()

    # Threshold warnings
    print("=" * 60)
    print_threshold_warnings(all_files, kb_thresh, char_thresh)
    print_context_bloat_warnings(all_files)


def to_json(all_files: list[FileMetrics]) -> str:
    """Serialise metrics to JSON."""
    return json_mod.dumps(
        [asdict(f) | {"size_kb": f.size_kb} for f in all_files],
        indent=2,
    )


# ── CLI ──────────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Audit file sizes and character counts in the task-flows repo.",
    )
    p.add_argument(
        "--top",
        type=int,
        default=DEFAULT_TOP_N,
        help=f"Files to show per category (default: {DEFAULT_TOP_N})",
    )
    p.add_argument(
        "--threshold-kb",
        type=float,
        default=DEFAULT_THRESHOLD_KB,
        help=f"Flag files ≥ this size in KB (default: {DEFAULT_THRESHOLD_KB})",
    )
    p.add_argument(
        "--threshold-chars",
        type=int,
        default=DEFAULT_THRESHOLD_CHARS,
        help=f"Flag files ≥ this character count (default: {DEFAULT_THRESHOLD_CHARS:,})",
    )
    p.add_argument(
        "--extensions",
        type=str,
        default=",".join(sorted(DEFAULT_EXTENSIONS)),
        help="Comma-separated extensions to scan (default: %(default)s)",
    )
    p.add_argument(
        "--category",
        type=str,
        default=None,
        help="Show only this category (e.g. skill-instructions)",
    )
    p.add_argument(
        "--summary-only",
        action="store_true",
        help="Print only the extension summary, skip per-category tables",
    )
    p.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    extensions = {
        ext.strip() if ext.strip().startswith(".") else f".{ext.strip()}"
        for ext in args.extensions.split(",")
    }

    print_banner()

    all_files = scan_repo(REPO_ROOT, extensions=extensions)

    if args.json_output:
        print(to_json(all_files))
        return

    if args.summary_only:
        by_ext: dict[str, list[FileMetrics]] = {}
        for f in all_files:
            ext = os.path.splitext(f.path)[1].lower()
            by_ext.setdefault(ext, []).append(f)
        print_summary(by_ext)
        print_threshold_warnings(all_files, args.threshold_kb, args.threshold_chars)
        print_context_bloat_warnings(all_files)
        return

    print_full_report(
        all_files,
        top_n=args.top,
        kb_thresh=args.threshold_kb,
        char_thresh=args.threshold_chars,
        category_filter=args.category,
    )


if __name__ == "__main__":
    main()
