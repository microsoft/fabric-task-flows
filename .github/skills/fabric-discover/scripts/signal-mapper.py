#!/usr/bin/env python3
"""
Deterministic signal mapper for Fabric task-flow discovery.

Pre-processes user problem text and maps keywords to architectural signals
using the same 11-category lookup table the @fabric-advisor uses. Outputs a
draft signal table that the advisor can confirm/adjust instead of discovering
from scratch.

Two operating modes:

  DISCOVERY (default) — Requires ``--project`` referencing a scaffolded
  project directory under ``_projects/``.  The project must have been
  created via ``run-pipeline.py start`` first.  This prevents agents from
  bypassing the project-name hard gate.

  STANDALONE ANALYSIS (``--intake``) — No project required.  Useful for
  ad-hoc signal exploration or testing.

Usage:
    python .github/skills/fabric-discover/scripts/signal-mapper.py --project my-project --text "We need real-time IoT sensor data"
    python .github/skills/fabric-discover/scripts/signal-mapper.py --project my-project --text-file problem.txt
    python .github/skills/fabric-discover/scripts/signal-mapper.py --intake --text "batch ETL pipeline"
    python .github/skills/fabric-discover/scripts/signal-mapper.py --project my-project --text "..." --format json --verbose --top 5
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Universal English stop words — excluded from coverage denominator so the
# metric reflects actual tech-content coverage, not natural-language filler.
# Maintained in _shared/registry/stop-words.json — do NOT hardcode here.
_STOP_WORDS_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent / "_shared" / "registry" / "stop-words.json"
STOP_WORDS: frozenset[str] = frozenset(
    json.loads(_STOP_WORDS_PATH.read_text(encoding="utf-8"))["words"]
)


# ---------------------------------------------------------------------------
# Signal category definitions — loaded from _shared/registry/signal-categories.json
# ---------------------------------------------------------------------------

SIGNAL_CATEGORIES_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent / "_shared" / "registry" / "signal-categories.json"

@dataclass(frozen=True)
class SignalCategory:
    id: int
    name: str
    keywords: tuple[str, ...]
    velocity: str
    use_case: str
    task_flow_candidates: tuple[str, ...]
    inference_rules: tuple[dict, ...] = ()


def _load_categories() -> tuple[SignalCategory, ...]:
    """Load signal categories from the shared JSON data file."""
    with open(SIGNAL_CATEGORIES_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return tuple(
        SignalCategory(
            id=cat["id"],
            name=cat["name"],
            keywords=tuple(cat["keywords"]),
            velocity=cat["velocity"],
            use_case=cat["use_case"],
            task_flow_candidates=tuple(cat["task_flow_candidates"]),
            inference_rules=tuple(cat.get("inference_rules", [])),
        )
        for cat in data["categories"]
    )


CATEGORIES: tuple[SignalCategory, ...] = _load_categories()


# ---------------------------------------------------------------------------
# Compiled regex patterns (one per keyword, longest phrases first per category)
# ---------------------------------------------------------------------------

@dataclass
class KeywordPattern:
    keyword: str
    pattern: re.Pattern[str]
    category_id: int


def _build_patterns() -> list[KeywordPattern]:
    patterns: list[KeywordPattern] = []
    for cat in CATEGORIES:
        sorted_kws = sorted(cat.keywords, key=len, reverse=True)
        for kw in sorted_kws:
            escaped = re.escape(kw)
            # Add optional plural 's' for keywords that don't already end in
            # 's' and don't contain regex metacharacters (e.g. "access control"
            # now also matches "access controls").
            if not kw.endswith("s") and not re.search(r"[?*+\[\]()]", kw):
                regex = re.compile(rf"\b{escaped}s?\b", re.IGNORECASE)
            else:
                regex = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
            patterns.append(KeywordPattern(keyword=kw, pattern=regex, category_id=cat.id))
    return patterns


KEYWORD_PATTERNS: list[KeywordPattern] = _build_patterns()


# ---------------------------------------------------------------------------
# Negation detection — suppress keywords that appear in negated context
# ---------------------------------------------------------------------------

# Window (in characters) before a keyword match to scan for negation cues.
_NEGATION_WINDOW = 60

# Patterns that negate a following keyword.  Each regex is tested against the
# text window *immediately preceding* the keyword match.  Order doesn't matter
# — any hit means the keyword is negated.
_NEGATION_CUES: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bno\b",
        r"\bnot\b",
        r"\bnor\b",
        r"\bnever\b",
        r"\bdon['\u2019]?t\b",
        r"\bdo\s+not\b",
        r"\bdoes\s+not\b",
        r"\bdoesn['\u2019]?t\b",
        r"\bwon['\u2019]?t\b",
        r"\bwithout\b",
        r"\bno\s+need\s+for\b",
        r"\bnot\s+looking\s+for\b",
        r"\bnot\s+interested\s+in\b",
        r"\bdon['\u2019]?t\s+(?:need|want|require|use)\b",
        r"\bdo\s+not\s+(?:need|want|require|use)\b",
        r"\bnot\s+(?:need|want|require|requir\w+|use|using)\b",
        r"\beliminate\b",
        r"\bexclude\b",
        r"\bavoid\b",
        r"\bskip\b",
        r"\bno\s+(?:need|interest|requirement|desire)\b",
    )
]

# Affirmation patterns that *cancel* a preceding negation when they appear
# between the negation cue and the keyword — e.g. "not just dashboards, but
# also real-time alerts" should NOT suppress "real-time".
_AFFIRMATION_OVERRIDES: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bbut\s+also\b",
        r"\bbut\s+rather\b",
        r"\binstead\b",
        r"\bhowever\b",
    )
]


def _is_negated(text: str, match_start: int) -> bool:
    """Return True if the keyword at *match_start* is preceded by a negation cue
    within the look-back window **and** the same sentence, with no affirmation
    override in between."""
    window_start = max(0, match_start - _NEGATION_WINDOW)
    window = text[window_start:match_start]

    # Restrict to the current sentence — negation doesn't cross sentence
    # boundaries (e.g. "We do NOT need dashboards. We want real-time..." should
    # NOT negate "real-time").
    for sep in (".  ", ". ", "! ", "? ", ";\n", ".\n"):
        last_boundary = window.rfind(sep)
        if last_boundary != -1:
            window = window[last_boundary + len(sep):]

    for cue in _NEGATION_CUES:
        m = cue.search(window)
        if m:
            # Check whether an affirmation override sits between the negation
            # cue and the keyword, which would cancel the negation.
            between = window[m.end():]
            if any(aff.search(between) for aff in _AFFIRMATION_OVERRIDES):
                continue
            return True
    return False


# ---------------------------------------------------------------------------
# Compiled inference patterns — detect architectural intent from NL phrases
# ---------------------------------------------------------------------------

@dataclass
class InferencePattern:
    pattern: re.Pattern[str]
    label: str
    weight: int
    category_id: int


def _build_inference_patterns() -> list[InferencePattern]:
    patterns: list[InferencePattern] = []
    for cat in CATEGORIES:
        for rule in cat.inference_rules:
            try:
                regex = re.compile(rule["pattern"], re.IGNORECASE)
                patterns.append(InferencePattern(
                    pattern=regex,
                    label=rule["label"],
                    weight=rule.get("weight", 1),
                    category_id=cat.id,
                ))
            except re.error:
                pass  # Skip invalid patterns
    return patterns


INFERENCE_PATTERNS: list[InferencePattern] = _build_inference_patterns()


# ---------------------------------------------------------------------------
# Match result types
# ---------------------------------------------------------------------------

@dataclass
class KeywordMatch:
    keyword: str
    start: int
    end: int


@dataclass
class CategoryResult:
    category: SignalCategory
    matches: list[KeywordMatch] = field(default_factory=list)

    @property
    def hit_count(self) -> int:
        return len(self.matches)

    @property
    def confidence(self) -> str:
        if self.hit_count >= 3:
            return "high"
        if self.hit_count == 2:
            return "medium"
        return "low"

    @property
    def matched_keywords(self) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for m in self.matches:
            if m.keyword not in seen:
                seen.add(m.keyword)
                result.append(m.keyword)
        return result


# ---------------------------------------------------------------------------
# Core mapping function
# ---------------------------------------------------------------------------

def map_signals(text: str) -> dict:
    """Map problem text to architectural signals.

    Returns a dict with keys: signals, task_flow_candidates,
    primary_velocity, ambiguous, keyword_coverage.

    Example:
        >>> result = map_signals("We need real-time IoT sensor data for ML")
        >>> result["primary_velocity"]
        'real-time'
    """
    # Normalize unicode characters for consistent regex matching
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2014", "--").replace("\u2013", "-")
    results: dict[int, CategoryResult] = {}
    for cat in CATEGORIES:
        results[cat.id] = CategoryResult(category=cat)

    matched_spans: list[tuple[int, int]] = []

    negated_spans: list[tuple[int, int]] = []

    for kp in KEYWORD_PATTERNS:
        for m in kp.pattern.finditer(text):
            overlap = any(
                m.start() < existing_end and m.end() > existing_start
                for existing_start, existing_end in matched_spans
            )
            if not overlap:
                if _is_negated(text, m.start()):
                    negated_spans.append((m.start(), m.end()))
                    continue
                matched_spans.append((m.start(), m.end()))
                results[kp.category_id].matches.append(
                    KeywordMatch(keyword=kp.keyword, start=m.start(), end=m.end())
                )

    # ── Inference pass: detect architectural intent from natural language ──
    for ip in INFERENCE_PATTERNS:
        if ip.pattern.search(text):
            for _ in range(ip.weight):
                results[ip.category_id].matches.append(
                    KeywordMatch(
                        keyword=f"(inferred: {ip.label})",
                        start=-1,
                        end=-1,
                    )
                )

    active: dict[int, CategoryResult] = {
        cid: r for cid, r in results.items() if r.hit_count > 0
    }

    # Boost Cat 3 if both Cat 1 and Cat 2 also match
    cat3 = results[3]
    if 1 in active and 2 in active and 3 not in active:
        # Synthesize lambda signal — both batch and real-time detected
        cat3.matches.append(
            KeywordMatch(keyword="(inferred: batch+real-time → lambda)", start=-1, end=-1)
        )
    elif 1 in active and 2 in active and 3 in active:
        if cat3.confidence != "high":
            cat3.matches.append(
                KeywordMatch(keyword="(inferred: batch+real-time)", start=-1, end=-1)
            )

    active = {cid: r for cid, r in results.items() if r.hit_count > 0}

    # Build signals list
    signals: list[dict] = []
    for cid in sorted(active):
        r = active[cid]
        signals.append({
            "signal": r.category.name,
            "value": r.category.use_case,
            "velocity": r.category.velocity,
            "confidence": r.confidence,
            "source_keywords": r.matched_keywords,
            "source_quotes": [],
        })

    # Build task flow candidates with scores
    tf_scores: dict[str, dict] = {}
    for cid, r in active.items():
        for tf in r.category.task_flow_candidates:
            if tf not in tf_scores:
                tf_scores[tf] = {"score": 0, "signals": []}
            tf_scores[tf]["score"] += r.hit_count
            tf_scores[tf]["signals"].append(r.category.name)

    candidates = [
        {"id": tf_id, "score": info["score"], "signals": info["signals"]}
        for tf_id, info in tf_scores.items()
    ]
    candidates.sort(key=lambda c: c["score"], reverse=True)

    # Primary velocity
    velocity_candidates: list[tuple[str, str]] = []
    for cid in sorted(active):
        r = active[cid]
        if r.category.velocity not in ("Varies",):
            velocity_candidates.append((r.confidence, r.category.velocity))

    confidence_rank = {"high": 3, "medium": 2, "low": 1}
    velocity_candidates.sort(key=lambda v: confidence_rank.get(v[0], 0), reverse=True)
    primary_velocity = velocity_candidates[0][1].lower() if velocity_candidates else "unknown"

    # Ambiguity check
    ambiguous = 1 in active and 2 in active and 3 not in active

    # Keyword coverage — stop words excluded from denominator so the metric
    # reflects tech-content coverage, not natural-language filler.
    words = re.findall(r"\b\w+\b", text)
    meaningful_words = [w for w in words if w.lower() not in STOP_WORDS]
    total_words = len(meaningful_words) if meaningful_words else 1
    matched_word_positions: set[int] = set()
    for start, end in matched_spans:
        for w_match in re.finditer(r"\b\w+\b", text[start:end]):
            matched_word_positions.add(start + w_match.start())

    input_word_starts = {m.start() for m in re.finditer(r"\b\w+\b", text)}
    covered = len(matched_word_positions & input_word_starts)

    # Keyword coverage uses only direct keyword matches.
    # Inference hits are structural pattern matches (not keyword-based),
    # so they must NOT inflate keyword_coverage.
    keyword_coverage = round(min(covered / total_words, 1.0), 2)

    return {
        "signals": signals,
        "task_flow_candidates": candidates,
        "primary_velocity": primary_velocity,
        "ambiguous": ambiguous,
        "keyword_coverage": keyword_coverage,
    }


# ---------------------------------------------------------------------------
# Verbose match details
# ---------------------------------------------------------------------------

def _verbose_matches(text: str) -> list[dict]:
    details: list[dict] = []
    matched_spans: list[tuple[int, int]] = []

    for kp in KEYWORD_PATTERNS:
        for m in kp.pattern.finditer(text):
            overlap = any(
                m.start() < ee and m.end() > es
                for es, ee in matched_spans
            )
            if not overlap:
                if _is_negated(text, m.start()):
                    cat = next(c for c in CATEGORIES if c.id == kp.category_id)
                    details.append({
                        "keyword": kp.keyword,
                        "category": cat.name,
                        "position": f"{m.start()}-{m.end()}",
                        "context": text[max(0, m.start() - 20):m.end() + 20].strip(),
                        "negated": True,
                    })
                    continue
                matched_spans.append((m.start(), m.end()))
                cat = next(c for c in CATEGORIES if c.id == kp.category_id)
                details.append({
                    "keyword": kp.keyword,
                    "category": cat.name,
                    "position": f"{m.start()}-{m.end()}",
                    "context": text[max(0, m.start() - 20):m.end() + 20].strip(),
                })

    # Add inference matches
    for ip in INFERENCE_PATTERNS:
        m = ip.pattern.search(text)
        if m:
            details.append({
                "keyword": f"(inferred: {ip.label})",
                "category": next(c.name for c in CATEGORIES if c.id == ip.category_id),
                "position": f"{m.start()}-{m.end()}",
                "context": text[max(0, m.start() - 20):m.end() + 20].strip(),
            })

    return details


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def _to_yaml(data: dict) -> str:
    lines: list[str] = []

    lines.append("signals:")
    for s in data["signals"]:
        lines.append(f"  - signal: {s['signal']}")
        lines.append(f"    value: {s['value']}")
        lines.append(f"    velocity: {s['velocity']}")
        lines.append(f"    confidence: {s['confidence']}")
        lines.append(f"    source_keywords: {json.dumps(s['source_keywords'])}")
        lines.append("    source_quotes: []")

    lines.append("")
    lines.append("task_flow_candidates:")
    for c in data["task_flow_candidates"]:
        lines.append(f"  - id: {c['id']}")
        lines.append(f"    score: {c['score']}")
        lines.append(f"    signals: {json.dumps(c['signals'])}")

    lines.append("")
    lines.append(f"primary_velocity: {data['primary_velocity']}")
    lines.append(f"ambiguous: {'true' if data['ambiguous'] else 'false'}")
    lines.append(f"keyword_coverage: {data['keyword_coverage']}")

    return "\n".join(lines) + "\n"


def _to_json(data: dict) -> str:
    return json.dumps(data, indent=2) + "\n"


# ---------------------------------------------------------------------------
# Intake: generate follow-up questions based on signal gaps
# ---------------------------------------------------------------------------

# Critical architecture dimensions and which signal categories address them
_DIMENSION_COVERAGE: dict[str, set[int]] = {
    "data_velocity": {1, 2, 3},      # real-time, batch, lambda
    "data_sensitivity": {5},          # sensitive data
    "data_structure": {7, 10},        # unstructured/semi, document/NoSQL
    "data_quality": {8},              # quality / layered
    "use_case_ml": {4},               # ML
    "use_case_transactional": {6},    # transactional
    "use_case_app": {9},              # app backend
}

_DIMENSION_QUESTIONS: dict[str, str] = {
    "data_velocity": (
        "How quickly does data need to be available after it's generated? "
        "(e.g., real-time/seconds, near-real-time/minutes, batch/nightly)"
    ),
    "data_sensitivity": (
        "Does the data include sensitive information like PII, financial records, "
        "or regulated data (HIPAA, GDPR, SOC2)?"
    ),
    "data_structure": (
        "What format is the source data? (e.g., relational/SQL, JSON/semi-structured, "
        "files/CSV/Parquet, unstructured logs)"
    ),
    "data_quality": (
        "Do you need a multi-layered approach to progressively clean and refine data "
        "(bronze/silver/gold), or is a simpler staging approach sufficient?"
    ),
    "use_case_ml": (
        "Are there machine learning, predictive analytics, or AI model training "
        "requirements now or planned?"
    ),
    "use_case_transactional": (
        "Does the solution need write-back / transactional capabilities "
        "(e.g., CRUD operations, inventory updates)?"
    ),
    "use_case_app": (
        "Will applications or APIs consume data directly from this platform "
        "(e.g., mobile apps, web frontends, microservices)?"
    ),
}


def generate_intake(result: dict, project: str | None = None) -> dict:
    """Analyze signal mapping results and generate follow-up questions.

    Returns a dict with:
      - project: project name (or "(no project name provided)" if not provided)
      - signals_detected: summary of what was found
      - follow_up_questions: list of questions to ask the user
      - ambiguity_questions: list if velocity is ambiguous
      - confidence_gaps: low-confidence signals that need confirmation
    """
    active_category_ids: set[int] = set()
    for sig in result.get("signals", []):
        for cat in CATEGORIES:
            if cat.name == sig.get("signal"):
                active_category_ids.add(cat.id)

    # Find uncovered dimensions
    follow_ups: list[dict[str, str]] = []
    for dim, cat_ids in _DIMENSION_COVERAGE.items():
        if not (active_category_ids & cat_ids):
            follow_ups.append({
                "dimension": dim,
                "question": _DIMENSION_QUESTIONS[dim],
                "reason": "Not mentioned in problem statement",
            })

    # Ambiguity questions
    ambiguity_qs: list[dict[str, str]] = []
    if result.get("ambiguous"):
        ambiguity_qs.append({
            "dimension": "data_velocity",
            "question": (
                "Your description mentions both real-time and batch patterns. "
                "Is this a mixed workload (some data real-time, some batch), "
                "or primarily one with occasional use of the other?"
            ),
            "reason": "Both real-time and batch signals detected without explicit lambda/hybrid mention",
        })

    # Low-confidence signals that need confirmation
    confidence_gaps: list[dict[str, str]] = []
    for sig in result.get("signals", []):
        if sig.get("confidence") == "low":
            confidence_gaps.append({
                "signal": sig["signal"],
                "question": (
                    f"You briefly mentioned keywords related to '{sig['signal']}'. "
                    f"Is this a core requirement or just context?"
                ),
                "matched_keywords": sig.get("source_keywords", []),
            })

    # Candidate tie-breaking
    candidates = result.get("task_flow_candidates", [])
    tie_qs: list[dict[str, str]] = []
    if len(candidates) >= 2 and candidates[0].get("score") == candidates[1].get("score"):
        names = [c["id"] for c in candidates[:3]]
        tie_qs.append({
            "dimension": "task_flow_selection",
            "question": (
                f"Based on your description, these patterns fit equally well: "
                f"{', '.join(names)}. Which resonates most with your goals?"
            ),
            "reason": "Multiple task flow candidates tied on score",
        })

    return {
        "project": project or "(no project name provided)",
        "signals_detected": [
            {"signal": s["signal"], "confidence": s["confidence"]}
            for s in result.get("signals", [])
        ],
        "follow_up_questions": follow_ups,
        "ambiguity_questions": ambiguity_qs,
        "confidence_gaps": confidence_gaps,
        "candidate_tie_questions": tie_qs,
        "total_questions": (
            len(follow_ups) + len(ambiguity_qs) +
            len(confidence_gaps) + len(tie_qs)
        ),
    }


def _intake_to_yaml(intake: dict) -> str:
    lines: list[str] = []
    lines.append(f"project: \"{intake['project']}\"")
    lines.append("")

    lines.append("signals_detected:")
    for s in intake["signals_detected"]:
        lines.append(f"  - signal: \"{s['signal']}\"")
        lines.append(f"    confidence: {s['confidence']}")

    for section, label in (
        ("follow_up_questions", "Follow-up questions (uncovered dimensions)"),
        ("ambiguity_questions", "Ambiguity questions"),
        ("confidence_gaps", "Low-confidence signals to confirm"),
        ("candidate_tie_questions", "Task flow tie-breaking"),
    ):
        items = intake.get(section, [])
        if items:
            lines.append("")
            lines.append(f"# {label}")
            lines.append(f"{section}:")
            for item in items:
                first_key = next(iter(item))
                lines.append(f"  - {first_key}: \"{item[first_key]}\"")
                for k, v in item.items():
                    if k != first_key:
                        if isinstance(v, list):
                            lines.append(f"    {k}: {json.dumps(v)}")
                        else:
                            lines.append(f"    {k}: \"{v}\"")

    lines.append("")
    lines.append(f"total_questions: {intake['total_questions']}")
    return "\n".join(lines) + "\n"

def _read_input(args: argparse.Namespace) -> str:
    if args.text:
        return args.text
    if args.text_file:
        with open(args.text_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    print("Error: provide --text, --text-file, or pipe text via stdin", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _resolve_repo_root() -> Path:
    """Walk up from this script to find the repo root (contains _projects/)."""
    candidate = Path(__file__).resolve().parent
    for _ in range(10):
        if (candidate / "_projects").is_dir():
            return candidate
        candidate = candidate.parent
    return Path(__file__).resolve().parent


def _validate_project_context(project: str | None, intake: bool) -> None:
    """Enforce project-name hard gate in discovery mode.

    In discovery mode (the default), --project is required and the project
    directory must already exist (scaffolded via ``run-pipeline.py start``).
    In intake/analysis mode (``--intake``), --project is optional so the
    mapper can be used for standalone signal exploration.
    """
    if intake:
        return  # standalone analysis — no project required

    if not project:
        print(
            "ERROR: --project is required in discovery mode.\n"
            "       The project must be scaffolded first:\n"
            "         python _shared/scripts/run-pipeline.py start "
            '"Project Name" --problem "..."\n'
            "       For standalone signal analysis, use --intake.",
            file=sys.stderr,
        )
        sys.exit(1)

    repo_root = _resolve_repo_root()
    project_dir = repo_root / "_projects" / project
    if not project_dir.is_dir():
        print(
            f"ERROR: Project '{project}' not found at {project_dir}.\n"
            "       Run 'run-pipeline.py start' to scaffold the project first.",
            file=sys.stderr,
        )
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Map problem text to Fabric architectural signals"
    )
    parser.add_argument("--text", type=str, help="Problem description text")
    parser.add_argument("--text-file", type=str, help="Path to file containing problem text")
    parser.add_argument("--project", type=str,
                        help="Project name (required in discovery mode; "
                             "must reference a scaffolded project)")
    parser.add_argument(
        "--format", choices=["yaml", "json"], default="yaml",
        help="Output format (default: yaml)",
    )
    parser.add_argument("--intake", action="store_true",
                        help="Standalone analysis mode — allows running "
                             "without a scaffolded project")
    parser.add_argument("--verbose", action="store_true", help="Show every keyword match with position")
    parser.add_argument("--top", type=int, default=3, help="Max task_flow_candidates to show (default: 3)")
    args = parser.parse_args()

    _validate_project_context(args.project, args.intake)

    text = _read_input(args)
    result = map_signals(text)

    result["task_flow_candidates"] = result["task_flow_candidates"][:args.top]

    # Intake mode: generate follow-up questions instead of raw signals
    if args.intake:
        intake = generate_intake(result, project=args.project)
        if args.format == "json":
            sys.stdout.write(json.dumps(intake, indent=2) + "\n")
        else:
            sys.stdout.write(_intake_to_yaml(intake))
        sys.exit(0)

    # Add project to output if provided
    if args.project:
        result["project"] = args.project

    if args.verbose:
        details = _verbose_matches(text)
        if args.format == "json":
            result["verbose_matches"] = details
        else:
            print("# Verbose keyword matches:", file=sys.stderr)
            for d in details:
                print(
                    f"#   [{d['category']}] \"{d['keyword']}\" "
                    f"at {d['position']}  ...{d['context']}...",
                    file=sys.stderr,
                )
            print("#", file=sys.stderr)

    if args.format == "json":
        sys.stdout.write(_to_json(result))
    else:
        sys.stdout.write(_to_yaml(result))

    sys.exit(0 if result["signals"] else 1)


if __name__ == "__main__":
    main()
