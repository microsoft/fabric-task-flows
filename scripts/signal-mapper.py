#!/usr/bin/env python3
"""
Deterministic signal mapper for Fabric task-flow discovery.

Pre-processes user problem text and maps keywords to architectural signals
using the same 11-category lookup table the @fabric-advisor uses. Outputs a
draft signal table that the advisor can confirm/adjust instead of discovering
from scratch.

Usage:
    python scripts/signal-mapper.py --text "We need real-time IoT sensor data"
    python scripts/signal-mapper.py --text-file problem.txt
    echo "batch ETL pipeline" | python scripts/signal-mapper.py
    python scripts/signal-mapper.py --text "..." --format json --verbose --top 5
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from typing import TextIO


# ---------------------------------------------------------------------------
# Signal category definitions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SignalCategory:
    id: int
    name: str
    keywords: tuple[str, ...]
    velocity: str
    use_case: str
    task_flow_candidates: tuple[str, ...]


CATEGORIES: tuple[SignalCategory, ...] = (
    SignalCategory(
        id=1,
        name="Real-time / Streaming",
        keywords=(
            "real-time", "streaming", "IoT", "sensors", "alerts", "live",
            "events", "telemetry", "event-driven", "kafka", "event hub",
            "pub/sub", "push notifications", "webhooks", "continuous",
            "GPS", "pings", "clickstream", "traffic", "fraud detection",
            "200ms", "sub-second", "low latency", "live map",
            "smart meters", "SCADA", "vibration", "position monitoring",
            "trading floor", "real-time personalization", "stock updates",
            "outage", "grid operations", "OPC-UA",
            "bid requests", "surge pricing", "real-time ops",
            "delivery events", "cell towers", "dropped call",
            "network congestion", "live dashboard", "live P&L",
            "crowd flow", "turnstile", "ride-sharing",
        ),
        velocity="Real-time",
        use_case="Event analytics",
        task_flow_candidates=("event-analytics", "event-medallion"),
    ),
    SignalCategory(
        id=2,
        name="Batch / Scheduled",
        keywords=(
            "batch", "daily", "weekly", "nightly", "ETL", "historical",
            "reports", "scheduled", "periodic", "cron", "overnight",
            "data warehouse", "monthly", "quarterly", "dashboard",
            "spreadsheets", "flat files", "CSV export", "ERP",
            "self-service analytics", "data-driven", "insights",
            "slow queries", "cloud migration", "modernize",
            "Power BI", "DirectQuery", "Import mode", "Direct Lake",
            "gateway", "refresh", "semantic model", "shared datasets",
            "Redshift", "QuickSight", "dbt", "revenue",
            "P&L", "KPI", "demand forecasting", "trend reports",
            "Synapse", "Data Factory", "Spark notebooks",
            "data strategy", "single source of truth",
            "billing", "analytics platform", "operational dashboards",
            "compliance reporting", "production reports", "analytics",
            "USDA", "FAA", "FDA", "quarterly close",
            "portfolio", "citizen services", "impact dashboard",
            "on-time performance", "usage dashboards",
        ),
        velocity="Batch",
        use_case="Analytics / Reporting",
        task_flow_candidates=("basic-data-analytics", "medallion"),
    ),
    SignalCategory(
        id=3,
        name="Both / Mixed (Lambda)",
        keywords=(
            "both batch and real-time", "historical + live",
            "stream and batch", "hybrid", "lambda",
            "real-time and batch", "hot and cold",
            "speed layer", "batch layer",
            "plus daily", "while also feeding", "and also need",
            "real-time view", "end-of-day", "reconciliation",
            "live and historical", "operational and analytical",
        ),
        velocity="Both",
        use_case="Mixed analytics",
        task_flow_candidates=("lambda", "event-medallion"),
    ),
    SignalCategory(
        id=4,
        name="Machine Learning",
        keywords=(
            "ML", "predict", "train models", "forecast", "scoring",
            "classification", "regression", "neural network",
            "deep learning", "feature engineering", "model", "inference",
            "AI", "machine learning", "churn", "propensity",
            "data prep", "data preparation", "data scientists",
            "anomaly detection", "recommendation", "sentiment",
            "auto-categorize", "predictive", "predictive maintenance",
            "readmission prediction", "demand forecasting",
            "personalization", "ML pipelines", "ML engineers",
            "AI strategy", "AI-powered", "OEE",
            "actuarial", "simulations", "risk scores",
            "at risk", "propensity-to-churn", "engagement",
            "content recommendations", "cohort analysis",
            "funnel analysis", "backtesting", "model drift",
            "A/B test", "retrain", "NLP", "text analytics",
            "extract sentiment", "auto-categorize",
            "digital twin", "route optimization",
        ),
        velocity="Batch (typically)",
        use_case="Machine learning",
        task_flow_candidates=("basic-machine-learning-models",),
    ),
    SignalCategory(
        id=5,
        name="Sensitive Data",
        keywords=(
            "sensitive", "PII", "compliance", "HIPAA", "masking",
            "encryption", "access control", "GDPR", "SOC2", "audit",
            "privacy", "regulated", "classified", "restricted", "PHI",
            "confidential", "clinical data", "patient", "EMR",
            "Epic", "Cerner", "FHIR", "population health",
            "regulatory reporting", "risk analytics", "trading",
            "chain of custody", "e-discovery", "SOX", "PCI-DSS",
            "de-identified", "audit trail", "breach notification",
            "data sovereignty", "tenant isolation",
            "explainable", "data provenance",
        ),
        velocity="Varies",
        use_case="Sensitive data",
        task_flow_candidates=("sensitive-data-insights",),
    ),
    SignalCategory(
        id=6,
        name="Transactional",
        keywords=(
            "writeback", "transactional", "CRUD", "operational",
            "update records", "insert", "delete", "point-of-sale",
            "inventory", "order management", "OLTP",
        ),
        velocity="Real-time",
        use_case="Transactional",
        task_flow_candidates=("translytical",),
    ),
    SignalCategory(
        id=7,
        name="Unstructured / Semi-structured",
        keywords=(
            "unstructured", "semi-structured", "files", "JSON", "Parquet",
            "SQL queries on files", "CSV", "logs", "XML", "nested",
            "schema-on-read", "data lake",
            "documents", "contracts", "text", "reviews",
            "genomic", "sequencing", "content", "images", "videos",
            "user-generated content", "support ticket text",
            "precedents", "key terms", "extract",
        ),
        velocity="Batch",
        use_case="SQL analytics",
        task_flow_candidates=("data-analytics-sql-endpoint",),
    ),
    SignalCategory(
        id=8,
        name="Data Quality / Layered",
        keywords=(
            "data quality", "bronze/silver/gold", "layers", "curated",
            "cleanse", "transform stages", "raw", "refined", "aggregated",
            "medallion", "data governance", "lineage", "data silos",
            "unified catalog", "data catalog", "single source of truth",
            "consolidate", "combine", "centralize",
            "federated", "data mesh", "data products", "global view",
            "conglomerate", "business units", "cross-region",
            "multi-cloud", "AWS", "Azure", "on-prem",
            "different tech stacks", "maturity levels",
            "trust", "different numbers", "who owns",
            "pipelines", "automated", "monitoring",
            "quality checks", "naming standards", "documentation",
            "SSIS packages", "Informatica", "ETL jobs",
            "data contracts", "versioning", "compatibility",
            "standardize", "unified",
        ),
        velocity="Varies",
        use_case="Layered analytics",
        task_flow_candidates=("medallion",),
    ),
    SignalCategory(
        id=9,
        name="Application Backend",
        keywords=(
            "API", "app", "frontend", "mobile", "backend", "GraphQL",
            "REST endpoint", "microservices", "CRUD", "web app",
            "application", "SPA", "full-stack",
            "SaaS", "multi-tenant", "customer-facing",
            "embedded analytics", "self-serve", "drag-and-drop",
            "chatbot", "natural language", "cite sources",
            "knowledge base", "AI-powered search",
        ),
        velocity="Varies",
        use_case="Application backend",
        task_flow_candidates=("app-backend",),
    ),
    SignalCategory(
        id=10,
        name="Document / NoSQL / AI-ready",
        keywords=(
            "document data", "NoSQL", "JSON", "semi-structured",
            "Cosmos DB", "schema-less", "vector search", "embeddings",
            "RAG", "knowledge base", "chatbot data",
        ),
        velocity="Varies",
        use_case="NoSQL / AI-ready apps",
        task_flow_candidates=("app-backend", "translytical"),
    ),
    SignalCategory(
        id=11,
        name="Semantic Governance",
        keywords=(
            "cross-domain", "unified vocabulary", "knowledge graph",
            "enterprise semantics", "ontology", "business terms",
            "data catalog", "glossary", "metadata management",
            "naming standards", "column names", "documentation",
            "searchable catalog", "who owns", "data stewardship",
            "ESG reporting", "sustainability", "carbon emissions",
            "Scope 1", "Scope 2", "Scope 3",
        ),
        velocity="Varies",
        use_case="Semantic governance",
        task_flow_candidates=(),
    ),
)


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
            regex = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
            patterns.append(KeywordPattern(keyword=kw, pattern=regex, category_id=cat.id))
    return patterns


KEYWORD_PATTERNS: list[KeywordPattern] = _build_patterns()


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
    results: dict[int, CategoryResult] = {}
    for cat in CATEGORIES:
        results[cat.id] = CategoryResult(category=cat)

    matched_spans: list[tuple[int, int]] = []

    for kp in KEYWORD_PATTERNS:
        for m in kp.pattern.finditer(text):
            overlap = any(
                m.start() < existing_end and m.end() > existing_start
                for existing_start, existing_end in matched_spans
            )
            if not overlap:
                matched_spans.append((m.start(), m.end()))
                results[kp.category_id].matches.append(
                    KeywordMatch(keyword=kp.keyword, start=m.start(), end=m.end())
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

    # Keyword coverage
    words = re.findall(r"\b\w+\b", text)
    total_words = len(words) if words else 1
    matched_word_positions: set[int] = set()
    for start, end in matched_spans:
        for w_match in re.finditer(r"\b\w+\b", text[start:end]):
            matched_word_positions.add(start + w_match.start())

    input_word_starts = {m.start() for m in re.finditer(r"\b\w+\b", text)}
    covered = len(matched_word_positions & input_word_starts)
    keyword_coverage = round(covered / total_words, 2)

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
                matched_spans.append((m.start(), m.end()))
                cat = next(c for c in CATEGORIES if c.id == kp.category_id)
                details.append({
                    "keyword": kp.keyword,
                    "category": cat.name,
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
        lines.append(f"    source_quotes: []")

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
      - project: project name (or "Unknown" if not provided)
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
        "project": project or "Unknown",
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

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Map problem text to Fabric architectural signals"
    )
    parser.add_argument("--text", type=str, help="Problem description text")
    parser.add_argument("--text-file", type=str, help="Path to file containing problem text")
    parser.add_argument("--project", type=str, help="Project name (used in intake mode)")
    parser.add_argument(
        "--format", choices=["yaml", "json"], default="yaml",
        help="Output format (default: yaml)",
    )
    parser.add_argument("--intake", action="store_true",
                        help="Generate follow-up questions for uncovered dimensions")
    parser.add_argument("--verbose", action="store_true", help="Show every keyword match with position")
    parser.add_argument("--top", type=int, default=3, help="Max task_flow_candidates to show (default: 3)")
    args = parser.parse_args()

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
