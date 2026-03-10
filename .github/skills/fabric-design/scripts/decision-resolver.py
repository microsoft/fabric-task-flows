#!/usr/bin/env python3
"""
Deterministic decision resolver for Fabric task-flow architectures.

Resolves all 7 architectural decisions from signal inputs using the same
logic encoded in the YAML frontmatter quick_decision fields of the
decision guides in decisions/*.md.

Usage:
    # Inline signals (JSON)
    python .github/skills/fabric-design/scripts/decision-resolver.py --signals '{
        "skillset": "python",
        "velocity": "batch",
        "volume": "large",
        "query_language": "spark",
        "environment_count": 1
    }'

    # Signals from a YAML file
    python .github/skills/fabric-design/scripts/decision-resolver.py --signals-file signals.yaml

    # JSON output instead of YAML
    python .github/skills/fabric-design/scripts/decision-resolver.py --signals '{"skillset": "python"}' --format json

    # Verbose mode (prints rule evaluation trace)
    python .github/skills/fabric-design/scripts/decision-resolver.py --signals '{"skillset": "python"}' --verbose

Importable:
    from decision_resolver import resolve_all
    result = resolve_all({"skillset": "python", "velocity": "batch"})

Exit codes:
    0 — all decisions resolved with high confidence
    1 — some decisions are ambiguous or unresolved
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from typing import Literal

Confidence = Literal["high", "ambiguous", "na"]


@dataclass
class Decision:
    choice: str | None
    confidence: Confidence
    rule_matched: str | None
    guide: str
    note: str | None = None
    candidates: list[str] = field(default_factory=list)


def _norm(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip().lower()


def _any_of(signal: str | None, *terms: str) -> bool:
    s = _norm(signal)
    return any(t in s for t in terms)


# ---------------------------------------------------------------------------
# Individual decision resolvers
# ---------------------------------------------------------------------------

VERBOSE_LOG: list[str] = []


def _log(msg: str) -> None:
    VERBOSE_LOG.append(msg)


def _match(decision_id: str, rule: str, choice: str) -> Decision:
    _log(f"  ✓ {decision_id}: matched \"{rule}\"")
    return Decision(choice=choice, confidence="high", rule_matched=rule,
                    guide=f"decisions/{decision_id}.md")


def _ambiguous(decision_id: str, candidates: list[str], reason: str) -> Decision:
    _log(f"  ? {decision_id}: ambiguous — {reason}")
    return Decision(choice=None, confidence="ambiguous", rule_matched=None,
                    guide=f"decisions/{decision_id}.md",
                    note=reason, candidates=candidates)


def _skip(decision_id: str, note: str) -> Decision:
    _log(f"  – {decision_id}: skipped — {note}")
    return Decision(choice=None, confidence="na", rule_matched=None,
                    guide=f"decisions/{decision_id}.md", note=note)


def resolve_storage(signals: dict) -> Decision:
    _log("storage-selection:")
    ql = _norm(signals.get("query_language"))
    sk = _norm(signals.get("skillset"))
    uc = _norm(signals.get("use_case"))

    if _any_of(ql, "spark") or _any_of(sk, "spark", "pyspark"):
        return _match("storage-selection", "Spark/Python → Lakehouse", "Lakehouse")
    if _any_of(sk, "python") and not _any_of(ql, "t-sql", "tsql", "kql", "nosql", "postgres"):
        return _match("storage-selection", "Spark/Python → Lakehouse", "Lakehouse")
    if _any_of(ql, "kql", "kusto") or _any_of(uc, "time-series", "timeseries", "iot", "telemetry", "logs"):
        return _match("storage-selection", "KQL time-series → Eventhouse", "Eventhouse")
    if _any_of(ql, "t-sql", "tsql", "sql"):
        if _any_of(uc, "transactional", "oltp", "operational", "writeback", "app"):
            return _match("storage-selection", "T-SQL transactional → SQL Database", "SQL Database")
        if _any_of(uc, "analytics", "reporting", "warehouse", "dw", "bi"):
            return _match("storage-selection", "T-SQL analytics → Warehouse", "Warehouse")
        # T-SQL with no clear use-case leans analytics
        return _ambiguous("storage-selection",
                          ["Warehouse", "SQL Database"],
                          "T-SQL detected but use_case unclear — set use_case to 'analytics' or 'transactional'")
    if _any_of(ql, "nosql") or _any_of(uc, "document", "nosql", "json", "vector", "cosmos"):
        return _match("storage-selection", "NoSQL/document → Cosmos DB", "Cosmos DB")
    if _any_of(ql, "postgres") or _any_of(sk, "postgres"):
        return _match("storage-selection", "PostgreSQL → PostgreSQL", "PostgreSQL")
    if _any_of(sk, "sql") and not ql:
        return _ambiguous("storage-selection",
                          ["Warehouse", "SQL Database", "Lakehouse"],
                          "SQL skillset without query_language — specify query_language or use_case")

    return _skip("storage-selection", "No storage signals detected — provide query_language, skillset, or use_case")


def resolve_ingestion(signals: dict) -> Decision:
    _log("ingestion-selection:")
    vel = _norm(signals.get("velocity"))
    vol = _norm(signals.get("volume"))
    sk = _norm(signals.get("skillset"))
    dp = _norm(signals.get("data_pattern"))

    if _any_of(vel, "stream", "real-time", "realtime") or _any_of(dp, "stream", "real-time", "realtime"):
        return _match("ingestion-selection", "Real-time streaming → Eventstream", "Eventstream")
    if _any_of(dp, "cdc", "replication", "mirror"):
        return _match("ingestion-selection", "Database replication (CDC) → Mirroring", "Mirroring")
    if _any_of(dp, "complex orchestration", "multi-step", "conditional"):
        return _match("ingestion-selection", "Complex orchestration (any volume) → Pipeline", "Pipeline")

    is_large = _any_of(vol, "large", "big", "massive", "high")
    is_small_med = _any_of(vol, "small", "medium", "low", "moderate") or not is_large
    is_code_first = _any_of(sk, "python", "spark", "code", "engineer", "pyspark", "scala")
    needs_transforms = _any_of(dp, "transform", "cleanse", "clean", "etl", "prep")

    if is_large:
        if is_code_first:
            return _match("ingestion-selection", "Large + code-first team → Pipeline + Notebook",
                          "Pipeline + Notebook")
        return _match("ingestion-selection", "Large + orchestration needed → Pipeline (Copy activity)",
                      "Pipeline (Copy activity)")

    if is_small_med and vol:
        if needs_transforms or _any_of(sk, "low-code", "power query", "business", "analyst"):
            return _match("ingestion-selection", "Small-medium + transforms needed → Dataflow Gen2",
                          "Dataflow Gen2")
        if _any_of(dp, "copy", "no transform", "as-is", "simple"):
            return _match("ingestion-selection", "Small-medium + no transforms → Copy Job", "Copy Job")
        if is_code_first:
            return _match("ingestion-selection", "Large + code-first team → Pipeline + Notebook",
                          "Pipeline + Notebook")
        return _ambiguous("ingestion-selection",
                          ["Dataflow Gen2", "Copy Job"],
                          "Small-medium volume but unclear if transforms needed — set data_pattern")

    if not vol and not vel and not dp:
        return _skip("ingestion-selection",
                      "No ingestion signals detected — provide velocity, volume, or data_pattern")

    if is_code_first:
        return _match("ingestion-selection", "Large + code-first team → Pipeline + Notebook",
                      "Pipeline + Notebook")
    return _ambiguous("ingestion-selection",
                      ["Dataflow Gen2", "Copy Job", "Pipeline"],
                      "Insufficient signals to resolve — provide volume and data_pattern")


def resolve_processing(signals: dict) -> Decision:
    _log("processing-selection:")
    sk = _norm(signals.get("skillset"))
    ql = _norm(signals.get("query_language"))
    mode = _norm(signals.get("mode"))

    is_interactive = _any_of(mode, "interactive", "explore", "ad-hoc", "development")
    is_production = _any_of(mode, "production", "scheduled", "prod", "cicd", "ci/cd")
    is_spark = _any_of(sk, "python", "spark", "pyspark", "scala") or _any_of(ql, "spark")
    is_kql = _any_of(ql, "kql", "kusto") or _any_of(sk, "kql")
    is_tsql = _any_of(ql, "t-sql", "tsql") or (_any_of(sk, "sql") and not is_spark and not is_kql)
    is_visual = _any_of(sk, "low-code", "no-code", "power query", "visual", "business", "analyst")
    has_cicd = _any_of(signals.get("deployment_tool", ""), "cicd", "ci/cd", "devops", "github actions", "fabric-cicd")

    if is_interactive:
        if is_spark:
            return _match("processing-selection", "Interactive + Python/Spark → Notebook", "Notebook")
        if is_kql:
            return _match("processing-selection", "Interactive + KQL → KQL Queryset", "KQL Queryset")
        if is_visual:
            return _match("processing-selection", "Interactive + visual/no-code → Dataflow Gen2",
                          "Dataflow Gen2")
        if is_tsql:
            return _match("processing-selection", "Interactive + Python/Spark → Notebook", "Notebook")
        return _ambiguous("processing-selection",
                          ["Notebook", "KQL Queryset", "Dataflow Gen2"],
                          "Interactive mode but skillset unclear — provide skillset or query_language")

    if is_production:
        if is_spark and has_cicd:
            return _match("processing-selection", "Production Spark + CI/CD → Spark Job Definition",
                          "Spark Job Definition")
        if is_spark:
            return _match("processing-selection",
                          "Production Spark + simple schedule → Notebook (via Pipeline)",
                          "Notebook (via Pipeline)")
        if is_tsql:
            return _match("processing-selection", "Production T-SQL → Stored Procedures",
                          "Stored Procedures")
        if is_kql:
            return _match("processing-selection",
                          "Production KQL → KQL Queryset (update policies)",
                          "KQL Queryset (update policies)")
        if is_visual:
            return _match("processing-selection", "Production Power Query → Dataflow Gen2",
                          "Dataflow Gen2")
        return _ambiguous("processing-selection",
                          ["Notebook (via Pipeline)", "Spark Job Definition", "Stored Procedures"],
                          "Production mode but skillset unclear — provide skillset or query_language")

    # No mode specified — infer from other signals
    if is_spark:
        return _match("processing-selection", "Interactive + Python/Spark → Notebook", "Notebook")
    if is_kql:
        return _match("processing-selection", "Interactive + KQL → KQL Queryset", "KQL Queryset")
    if is_visual:
        return _match("processing-selection", "Interactive + visual/no-code → Dataflow Gen2",
                      "Dataflow Gen2")
    if is_tsql:
        return _match("processing-selection", "Production T-SQL → Stored Procedures",
                      "Stored Procedures")

    return _skip("processing-selection",
                  "No processing signals detected — provide skillset, query_language, or mode")


def resolve_visualization(signals: dict) -> Decision:
    _log("visualization-selection:")
    inter = _norm(signals.get("interactivity"))
    vel = _norm(signals.get("velocity"))
    uc = _norm(signals.get("use_case"))

    if _any_of(uc, "geospatial", "location", "fleet", "map", "gps"):
        return _match("visualization-selection",
                      "Live geospatial/location data → Real-Time Map", "Real-Time Map")
    if _any_of(vel, "stream", "real-time", "realtime", "sub-second"):
        return _match("visualization-selection",
                      "Live streaming data (sub-second) → Real-Time Dashboard",
                      "Real-Time Dashboard")
    if _any_of(uc, "kpi", "goal", "okr", "scorecard", "metric"):
        return _match("visualization-selection",
                      "Goal/KPI tracking + check-ins → Metrics Scorecard",
                      "Metrics Scorecard")
    if _any_of(uc, "pixel", "print", "paginated", "invoice", "regulated", "multi-page"):
        return _match("visualization-selection",
                      "Pixel-perfect / printable / multi-page → Paginated Report",
                      "Paginated Report")
    if _any_of(inter, "high", "interactive", "filter", "slicer", "drill", "explore", "exploration"):
        return _match("visualization-selection",
                      "Interactive exploration + filters → Power BI Report",
                      "Power BI Report")
    if _any_of(uc, "report", "dashboard", "bi", "analytics", "analysis"):
        return _match("visualization-selection",
                      "Interactive exploration + filters → Power BI Report",
                      "Power BI Report")

    # Default: most projects need a Power BI report
    if inter or uc:
        return _ambiguous("visualization-selection",
                          ["Power BI Report", "Paginated Report", "Real-Time Dashboard"],
                          "Visualization signals present but no clear match — refine interactivity or use_case")
    return _skip("visualization-selection",
                  "No visualization signals detected — provide interactivity or use_case")


def resolve_skillset(signals: dict) -> Decision:
    _log("skillset-selection:")
    sk = _norm(signals.get("skillset"))
    tc = _norm(signals.get("team_composition"))

    if _any_of(tc, "mixed", "hybrid", "both"):
        return _match("skillset-selection",
                      "Mixed team (engineers + analysts) → Hybrid [LC/CF]", "Hybrid [LC/CF]")
    if _any_of(sk, "python", "spark", "pyspark", "scala", "kql", "code") or \
       (_any_of(sk, "sql") and _any_of(tc, "engineer")):
        if _any_of(sk, "visual", "low-code", "prefer visual"):
            return _match("skillset-selection",
                          "Engineers + prefer visual tools → Low-Code [LC]", "Low-Code [LC]")
        return _match("skillset-selection",
                      "Engineers + Python/Spark/SQL → Code-First [CF]", "Code-First [CF]")
    if _any_of(sk, "power query", "business", "analyst", "low-code", "no-code", "citizen"):
        return _match("skillset-selection",
                      "Business Analysts + Power Query → Low-Code [LC]", "Low-Code [LC]")
    if _any_of(tc, "engineer", "developer"):
        return _match("skillset-selection",
                      "Engineers + Python/Spark/SQL → Code-First [CF]", "Code-First [CF]")
    if _any_of(tc, "analyst", "business"):
        return _match("skillset-selection",
                      "Business Analysts + Power Query → Low-Code [LC]", "Low-Code [LC]")
    if _any_of(sk, "sql") and not tc:
        return _ambiguous("skillset-selection",
                          ["Code-First [CF]", "Hybrid [LC/CF]"],
                          "SQL skillset detected but team_composition unknown — engineers or analysts?")

    return _skip("skillset-selection",
                  "No skillset signals detected — provide skillset or team_composition")


def resolve_parameterization(signals: dict) -> Decision:
    _log("parameterization-selection:")
    env_count = signals.get("environment_count")
    dt = _norm(signals.get("deployment_tool"))

    if env_count is not None:
        try:
            env_count = int(env_count)
        except (ValueError, TypeError):
            env_count = None

    if env_count is not None and env_count <= 1:
        return _match("parameterization-selection",
                      "Single environment → Environment Variables (or skip)",
                      "Environment Variables")

    is_multi = env_count is not None and env_count > 1

    if is_multi:
        if _any_of(dt, "fabric git", "git integration", "fabric-git"):
            return _match("parameterization-selection",
                          "Multi-env + Fabric Git → Variable Library", "Variable Library")
        if _any_of(dt, "fabric-cicd", "cicd library"):
            return _match("parameterization-selection",
                          "Multi-env + fabric-cicd → parameter.yml", "parameter.yml")
        if _any_of(dt, "fab", "fab cli"):
            return _match("parameterization-selection",
                          "Multi-env + fab CLI → Environment Variables or Variable Library",
                          "Environment Variables or Variable Library")
        return _ambiguous("parameterization-selection",
                          ["Variable Library", "parameter.yml", "Environment Variables"],
                          "Multiple environments but deployment_tool not specified")

    if dt:
        if _any_of(dt, "fabric-cicd", "cicd library"):
            return _match("parameterization-selection",
                          "Multi-env + fabric-cicd → parameter.yml", "parameter.yml")
        if _any_of(dt, "fabric git", "git integration", "fabric-git"):
            return _match("parameterization-selection",
                          "Multi-env + Fabric Git → Variable Library", "Variable Library")
        if _any_of(dt, "fab", "fab cli"):
            return _match("parameterization-selection",
                          "Single environment → Environment Variables (or skip)",
                          "Environment Variables")

    return _skip("parameterization-selection",
                  "No parameterization signals detected — provide environment_count and deployment_tool")


def resolve_api(signals: dict) -> Decision:
    _log("api-selection:")
    uc = _norm(signals.get("use_case"))
    api = _norm(signals.get("api_needs"))

    has_api_signal = bool(api) or _any_of(uc, "api", "graphql", "rest", "frontend", "app-backend",
                                          "crud", "function", "endpoint")
    if not has_api_signal:
        return _skip("api-selection",
                      "No API signals detected — skip unless app-backend task flow")

    needs_reads = _any_of(api, "read", "query", "flexible", "graphql", "fetch")
    needs_writes = _any_of(api, "write", "logic", "function", "custom", "mutation", "writeback")
    needs_crud = _any_of(api, "crud", "simple", "direct", "internal")

    if _any_of(uc, "crud") or needs_crud:
        return _match("api-selection",
                      "Simple CRUD from internal tools → Direct Connection",
                      "Direct Connection")
    if needs_reads and needs_writes:
        return _match("api-selection",
                      "Both reads AND logic → GraphQL API + User Data Functions",
                      "GraphQL API + User Data Functions")
    if needs_reads or _any_of(uc, "graphql"):
        return _match("api-selection",
                      "Flexible read queries → GraphQL API", "GraphQL API")
    if needs_writes or _any_of(uc, "function", "rest", "custom logic"):
        return _match("api-selection",
                      "Custom business logic/writes → User Data Functions",
                      "User Data Functions")

    return _ambiguous("api-selection",
                      ["GraphQL API", "User Data Functions", "Direct Connection"],
                      "API signals present but needs unclear — specify api_needs (read/write/crud)")


# ---------------------------------------------------------------------------
# Top-level resolver
# ---------------------------------------------------------------------------

RESOLVERS: dict[str, tuple[str, type]] = {
    "storage":          ("storage-selection",          resolve_storage),
    "ingestion":        ("ingestion-selection",        resolve_ingestion),
    "processing":       ("processing-selection",       resolve_processing),
    "visualization":    ("visualization-selection",    resolve_visualization),
    "skillset":         ("skillset-selection",         resolve_skillset),
    "parameterization": ("parameterization-selection", resolve_parameterization),
    "api":              ("api-selection",              resolve_api),
}


def resolve_all(signals: dict) -> dict:
    """Resolve all 7 architectural decisions from signal inputs.

    Args:
        signals: Dict with keys like skillset, velocity, volume, query_language,
                 use_case, environment_count, deployment_tool, interactivity,
                 data_pattern, mode, team_composition, api_needs.

    Returns:
        Dict with 'decisions', 'ambiguous', and 'unresolved' keys.
    """
    VERBOSE_LOG.clear()
    decisions: dict[str, dict] = {}
    ambiguous: list[str] = []
    unresolved: list[str] = []

    for key, (_guide_id, resolver) in RESOLVERS.items():
        result = resolver(signals)
        entry: dict = {
            "choice": result.choice,
            "confidence": result.confidence,
            "rule_matched": result.rule_matched,
            "guide": result.guide,
        }
        if result.note:
            entry["note"] = result.note
        if result.candidates:
            entry["candidates"] = result.candidates
        decisions[key] = entry

        if result.confidence == "ambiguous":
            ambiguous.append(key)
        elif result.confidence == "na" and result.choice is None:
            unresolved.append(key)

    return {
        "decisions": decisions,
        "ambiguous": ambiguous,
        "unresolved": unresolved,
    }


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def _yaml_scalar(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        if any(c in value for c in ":#{}[]|>&*!%@`,?") or value in ("null", "true", "false"):
            return f'"{value}"'
        if value.startswith('"') or value.startswith("'"):
            return f'"{value}"'
        return value
    return str(value)


def _to_yaml(result: dict) -> str:
    lines: list[str] = []
    lines.append("decisions:")
    for key, decision in result["decisions"].items():
        lines.append(f"  {key}:")
        for dk, dv in decision.items():
            if isinstance(dv, list):
                if dv:
                    lines.append(f"    {dk}:")
                    for item in dv:
                        lines.append(f"      - {_yaml_scalar(item)}")
                else:
                    lines.append(f"    {dk}: []")
            else:
                lines.append(f"    {dk}: {_yaml_scalar(dv)}")
    lines.append("")
    lines.append(f"ambiguous: {json.dumps(result['ambiguous'])}")
    lines.append(f"unresolved: {json.dumps(result['unresolved'])}")
    lines.append("")
    return "\n".join(lines)


def _to_json(result: dict) -> str:
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# YAML signal file loader (minimal, no PyYAML dependency)
# ---------------------------------------------------------------------------

def _load_yaml_signals(path: str) -> dict:
    """Load a flat key: value YAML file without requiring PyYAML."""
    signals: dict = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if value.lower() == "null" or value == "":
                value = None
            elif value.isdigit():
                value = int(value)
            signals[key] = value
    return signals


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deterministic decision resolver for Fabric task-flow architectures"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--signals", type=str,
                       help="JSON string of signal inputs")
    group.add_argument("--signals-file", type=str,
                       help="Path to a YAML file with signal inputs")
    parser.add_argument("--format", choices=["yaml", "json"], default="yaml",
                        help="Output format (default: yaml)")
    parser.add_argument("--verbose", action="store_true",
                        help="Print rule evaluation trace to stderr")
    args = parser.parse_args()

    if args.signals:
        try:
            signals = json.loads(args.signals)
        except json.JSONDecodeError as e:
            print(f"Error: invalid JSON in --signals: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        try:
            signals = _load_yaml_signals(args.signals_file)
        except FileNotFoundError:
            print(f"Error: file not found: {args.signals_file}", file=sys.stderr)
            sys.exit(2)
        except Exception as e:
            print(f"Error reading signals file: {e}", file=sys.stderr)
            sys.exit(2)

    result = resolve_all(signals)

    if args.verbose:
        for line in VERBOSE_LOG:
            print(line, file=sys.stderr)
        print(file=sys.stderr)

    if args.format == "json":
        print(_to_json(result))
    else:
        print(_to_yaml(result))

    if result["ambiguous"]:
        print(f"⚠ Ambiguous decisions: {', '.join(result['ambiguous'])}", file=sys.stderr)
        sys.exit(1)
    elif result["unresolved"]:
        # Unresolved (na) with no signals is informational, not an error
        sys.exit(0)


if __name__ == "__main__":
    main()
