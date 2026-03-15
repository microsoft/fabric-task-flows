#!/usr/bin/env python3
"""
Deterministic decision resolver for Fabric task-flow architectures.

Resolves all 7 architectural decisions from signal inputs using the same
logic encoded in the YAML frontmatter quick_decision fields of the
decision guides in decisions/*.md.  Output defaults to JSON.

Usage:
    # Inline signals (JSON)
    python .github/skills/fabric-design/scripts/decision-resolver.py --signals '{
        "skillset": "python",
        "velocity": "batch",
        "volume": "large",
        "query_language": "spark",
        "environment_count": 1
    }'

    # Signals from a file (JSON or key: value format)
    python .github/skills/fabric-design/scripts/decision-resolver.py --signals-file signals.json

    # Extract signals from a discovery brief (markdown)
    python .github/skills/fabric-design/scripts/decision-resolver.py --discovery-brief _projects/my-project/docs/discovery-brief.md

    # YAML output instead of JSON
    python .github/skills/fabric-design/scripts/decision-resolver.py --signals '{"skillset": "python"}' --format yaml

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

Confidence = Literal["high", "default", "ambiguous", "na"]


@dataclass
class Decision:
    choice: str | None
    confidence: Confidence
    rule_matched: str | None
    guide: str
    rationale: str = ""
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


def _match(decision_id: str, rule: str, choice: str, rationale: str = "") -> Decision:
    _log(f"  ✓ {decision_id}: matched \"{rule}\"")
    return Decision(choice=choice, confidence="high", rule_matched=rule,
                    guide=f"decisions/{decision_id}.md", rationale=rationale)


def _ambiguous(decision_id: str, candidates: list[str], reason: str, rationale: str = "") -> Decision:
    _log(f"  ? {decision_id}: ambiguous — {reason}")
    return Decision(choice=None, confidence="ambiguous", rule_matched=None,
                    guide=f"decisions/{decision_id}.md", rationale=rationale or reason,
                    note=reason, candidates=candidates)


def _default(decision_id: str, choice: str, source: str, rationale: str = "") -> Decision:
    _log(f"  ⊙ {decision_id}: defaulted to \"{choice}\" ({source})")
    return Decision(choice=choice, confidence="default", rule_matched=f"Default: {source}",
                    guide=f"decisions/{decision_id}.md", rationale=rationale)


def _skip(decision_id: str, note: str, rationale: str = "") -> Decision:
    _log(f"  – {decision_id}: skipped — {note}")
    return Decision(choice=None, confidence="na", rule_matched=None,
                    guide=f"decisions/{decision_id}.md", rationale=rationale or note, note=note)


def resolve_storage(signals: dict) -> Decision:
    _log("storage-selection:")
    ql = _norm(signals.get("query_language"))
    sk = _norm(signals.get("skillset"))
    uc = _norm(signals.get("use_case"))
    vel = _norm(signals.get("velocity"))

    if _any_of(ql, "spark") or _any_of(sk, "spark", "pyspark"):
        return _match("storage-selection", "Spark/Python → Lakehouse", "Lakehouse",
                      rationale="Spark/Python skillset is best served by Lakehouse with Delta Lake format and native Spark compute")
    if _any_of(sk, "python") and not _any_of(ql, "t-sql", "tsql", "kql", "nosql", "postgres"):
        return _match("storage-selection", "Spark/Python → Lakehouse", "Lakehouse",
                      rationale="Spark/Python skillset is best served by Lakehouse with Delta Lake format and native Spark compute")
    if _any_of(ql, "kql", "kusto") or _any_of(uc, "time-series", "timeseries", "iot", "telemetry", "logs"):
        return _match("storage-selection", "KQL time-series → Eventhouse", "Eventhouse",
                      rationale="KQL/time-series use case requires Eventhouse for optimized time-series queries and KQL analytics")
    if _any_of(vel, "real-time", "realtime", "streaming", "stream"):
        return _match("storage-selection", "Real-time streaming → Eventhouse", "Eventhouse",
                      rationale="Real-time streaming velocity requires Eventhouse for sub-second ingestion and hot-path analytics")
    if _any_of(vel, "both"):
        # Batch-primary with streaming supplement — Lakehouse handles both
        # via Eventstream → bronze lakehouse + batch transformations
        return _match("storage-selection", "Batch + streaming → Lakehouse", "Lakehouse",
                      rationale="Batch-primary with streaming supplement is best served by Lakehouse — Eventstream feeds bronze layer while batch pipelines handle the primary workload")
    if _any_of(ql, "t-sql", "tsql", "sql"):
        if _any_of(uc, "transactional", "oltp", "operational", "writeback", "app"):
            return _match("storage-selection", "T-SQL transactional → SQL Database", "SQL Database",
                          rationale="T-SQL transactional workload needs SQL Database for OLTP operations with full read/write support")
        if _any_of(uc, "analytics", "reporting", "warehouse", "dw", "bi"):
            return _match("storage-selection", "T-SQL analytics → Warehouse", "Warehouse",
                          rationale="T-SQL analytics workload is best served by Warehouse with optimized query engine for BI reporting")
        # T-SQL with no clear use-case leans analytics
        return _ambiguous("storage-selection",
                          ["Warehouse", "SQL Database"],
                          "T-SQL detected but use_case unclear — set use_case to 'analytics' or 'transactional'",
                          rationale="T-SQL detected but use case unclear — could be analytics (Warehouse) or transactional (SQL Database)")
    if _any_of(ql, "nosql") or _any_of(uc, "document", "nosql", "json", "vector", "cosmos"):
        return _match("storage-selection", "NoSQL/document → Cosmos DB", "Cosmos DB",
                      rationale="NoSQL/document data pattern requires Cosmos DB for schema-flexible JSON storage and vector search")
    if _any_of(ql, "postgres") or _any_of(sk, "postgres"):
        return _match("storage-selection", "PostgreSQL → PostgreSQL", "PostgreSQL",
                      rationale="PostgreSQL skillset maps directly to Fabric PostgreSQL for familiar tooling and compatibility")
    if _any_of(sk, "sql") and not ql:
        return _ambiguous("storage-selection",
                          ["Warehouse", "SQL Database", "Lakehouse"],
                          "SQL skillset without query_language — specify query_language or use_case",
                          rationale="SQL skillset detected but no query language specified — need more context to choose between Lakehouse, Warehouse, and SQL Database")

    # Batch analytics without a specific query language → Lakehouse
    # Lakehouse supports both SQL and Spark access, making it the safe default
    # for mixed or low-code teams doing analytics workloads.
    if _any_of(uc, "analytics", "reporting", "warehouse", "dw", "bi"):
        return _default("storage-selection", "Lakehouse", "batch analytics",
                        rationale="Analytics use case without a specific query language defaults to Lakehouse — "
                        "it supports both SQL endpoint and Spark, making it the most flexible choice")

    return _skip("storage-selection", "No storage signals detected — provide query_language, skillset, or use_case",
                 rationale="No storage signals found in discovery brief — architect should specify query language, skillset, or use case")


def resolve_ingestion(signals: dict) -> Decision:
    _log("ingestion-selection:")
    vel = _norm(signals.get("velocity"))
    vol = _norm(signals.get("volume"))
    sk = _norm(signals.get("skillset"))
    dp = _norm(signals.get("data_pattern"))

    if _any_of(vel, "stream", "real-time", "realtime") and not _any_of(vel, "both"):
        return _match("ingestion-selection", "Real-time streaming → Eventstream", "Eventstream",
                      rationale="Real-time/streaming velocity requires Eventstream for continuous data ingestion")
    if _any_of(dp, "stream", "real-time", "realtime") and not _any_of(vel, "both", "batch"):
        return _match("ingestion-selection", "Real-time streaming → Eventstream", "Eventstream",
                      rationale="Real-time/streaming data pattern requires Eventstream for continuous data ingestion")
    if _any_of(dp, "cdc", "replication", "mirror"):
        return _match("ingestion-selection", "Database replication (CDC) → Mirroring", "Mirroring",
                      rationale="CDC/replication pattern maps to Mirroring for near-real-time database synchronization")
    if _any_of(dp, "complex orchestration", "multi-step", "conditional"):
        return _match("ingestion-selection", "Complex orchestration (any volume) → Pipeline", "Pipeline",
                      rationale="Complex multi-step orchestration requires Pipeline for conditional logic and sequencing")

    is_large = _any_of(vol, "large", "big", "massive", "high")
    is_small_med = _any_of(vol, "small", "medium", "low", "moderate") or not is_large
    is_code_first = _any_of(sk, "python", "spark", "code", "engineer", "pyspark", "scala")
    needs_transforms = _any_of(dp, "transform", "cleanse", "clean", "etl", "prep")

    if is_large:
        if is_code_first:
            return _match("ingestion-selection", "Large + code-first team → Pipeline + Notebook",
                          "Pipeline + Notebook",
                          rationale="Large volume with code-first team benefits from Pipeline orchestration with Notebook-based Spark transformations")
        return _match("ingestion-selection", "Large + orchestration needed → Pipeline (Copy activity)",
                      "Pipeline (Copy activity)",
                      rationale="Large data volume requires Pipeline with Copy activity for high-throughput bulk data movement")

    if is_small_med and vol:
        if needs_transforms or _any_of(sk, "low-code", "power query", "business", "analyst"):
            return _match("ingestion-selection", "Small-medium + transforms needed → Dataflow Gen2",
                          "Dataflow Gen2",
                          rationale="Small-medium volume with transformation needs suits Dataflow Gen2 for visual Power Query-based ETL")
        if _any_of(dp, "copy", "no transform", "as-is", "simple"):
            return _match("ingestion-selection", "Small-medium + no transforms → Copy Job", "Copy Job",
                          rationale="Small-medium volume with no transformations maps to Copy Job for simple point-to-point data movement")
        if is_code_first:
            return _match("ingestion-selection", "Large + code-first team → Pipeline + Notebook",
                          "Pipeline + Notebook",
                          rationale="Code-first team benefits from Pipeline orchestration with Notebook-based Spark transformations")
        return _ambiguous("ingestion-selection",
                          ["Dataflow Gen2", "Copy Job"],
                          "Small-medium volume but unclear if transforms needed — set data_pattern",
                          rationale="Small-medium volume detected but transformation requirements unclear — specify data_pattern to choose between Dataflow Gen2 and Copy Job")

    if not vol and not vel and not dp:
        return _skip("ingestion-selection",
                      "No ingestion signals detected — provide velocity, volume, or data_pattern",
                      rationale="No ingestion signals found in discovery brief — architect should specify velocity, volume, or data_pattern")

    if is_code_first:
        return _match("ingestion-selection", "Large + code-first team → Pipeline + Notebook",
                      "Pipeline + Notebook",
                      rationale="Code-first team benefits from Pipeline orchestration with Notebook-based Spark transformations")
    return _ambiguous("ingestion-selection",
                      ["Dataflow Gen2", "Copy Job", "Pipeline"],
                      "Insufficient signals to resolve — provide volume and data_pattern",
                      rationale="Insufficient ingestion signals to resolve — provide volume and data_pattern to determine the right ingestion tool")


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
            return _match("processing-selection", "Interactive + Python/Spark → Notebook", "Notebook",
                          rationale="Interactive Spark/Python workload best served by Notebook for exploratory development and iterative analysis")
        if is_kql:
            return _match("processing-selection", "Interactive + KQL → KQL Queryset", "KQL Queryset",
                          rationale="Interactive KQL workload maps to KQL Queryset for ad-hoc log and time-series exploration")
        if is_visual:
            return _match("processing-selection", "Interactive + visual/no-code → Dataflow Gen2",
                          "Dataflow Gen2",
                          rationale="Interactive visual/low-code preference maps to Dataflow Gen2 for Power Query-based data preparation")
        if is_tsql:
            return _match("processing-selection", "Interactive + Python/Spark → Notebook", "Notebook",
                          rationale="Interactive T-SQL workload maps to Notebook for ad-hoc query development and exploration")
        return _ambiguous("processing-selection",
                          ["Notebook", "KQL Queryset", "Dataflow Gen2"],
                          "Interactive mode but skillset unclear — provide skillset or query_language",
                          rationale="Interactive mode detected but skillset unclear — specify skillset or query_language to choose the right processing tool")

    if is_production:
        if is_spark and has_cicd:
            return _match("processing-selection", "Production Spark + CI/CD → Spark Job Definition",
                          "Spark Job Definition",
                          rationale="Production Spark with CI/CD requirements maps to Spark Job Definition for automated, version-controlled job execution")
        if is_spark:
            return _match("processing-selection",
                          "Production Spark + simple schedule → Notebook (via Pipeline)",
                          "Notebook (via Pipeline)",
                          rationale="Production Spark without CI/CD maps to Notebook orchestrated via Pipeline for scheduled execution")
        if is_tsql:
            return _match("processing-selection", "Production T-SQL → Stored Procedures",
                          "Stored Procedures",
                          rationale="Production T-SQL workload maps to Stored Procedures for optimized, reusable server-side logic")
        if is_kql:
            return _match("processing-selection",
                          "Production KQL → KQL Queryset (update policies)",
                          "KQL Queryset (update policies)",
                          rationale="Production KQL workload maps to KQL Queryset with update policies for automated data transformation on ingestion")
        if is_visual:
            return _match("processing-selection", "Production Power Query → Dataflow Gen2",
                          "Dataflow Gen2",
                          rationale="Production Power Query workload maps to Dataflow Gen2 for scheduled visual ETL pipelines")
        return _ambiguous("processing-selection",
                          ["Notebook (via Pipeline)", "Spark Job Definition", "Stored Procedures"],
                          "Production mode but skillset unclear — provide skillset or query_language",
                          rationale="Production mode detected but skillset unclear — specify skillset or query_language to choose the right processing tool")

    # No mode specified — infer from other signals
    if is_spark:
        return _match("processing-selection", "Interactive + Python/Spark → Notebook", "Notebook",
                      rationale="Spark/Python skillset defaults to Notebook for exploratory development and iterative analysis")
    if is_kql:
        return _match("processing-selection", "Interactive + KQL → KQL Queryset", "KQL Queryset",
                      rationale="KQL skillset defaults to KQL Queryset for ad-hoc log and time-series exploration")
    if is_visual:
        return _match("processing-selection", "Interactive + visual/no-code → Dataflow Gen2",
                      "Dataflow Gen2",
                      rationale="Visual/low-code preference defaults to Dataflow Gen2 for Power Query-based data preparation")
    if is_tsql:
        return _match("processing-selection", "Production T-SQL → Stored Procedures",
                      "Stored Procedures",
                      rationale="T-SQL skillset defaults to Stored Procedures for optimized, reusable server-side logic")

    return _skip("processing-selection",
                  "No processing signals detected — provide skillset, query_language, or mode",
                  rationale="No processing signals found in discovery brief — architect should specify skillset, query_language, or mode")


def resolve_visualization(signals: dict) -> Decision:
    _log("visualization-selection:")
    inter = _norm(signals.get("interactivity"))
    vel = _norm(signals.get("velocity"))
    uc = _norm(signals.get("use_case"))

    if _any_of(uc, "geospatial", "location", "fleet", "map", "gps"):
        return _match("visualization-selection",
                      "Live geospatial/location data → Real-Time Map", "Real-Time Map",
                      rationale="Geospatial/location data requires Real-Time Map for live fleet and asset tracking visualization")
    # App/API-backend projects typically don't need Fabric visualization —
    # don't let velocity push them into Real-Time Dashboard
    is_app_backend = _any_of(uc, "app", "api", "backend", "integration")
    if _any_of(vel, "stream", "real-time", "realtime", "sub-second") and not is_app_backend:
        return _match("visualization-selection",
                      "Live streaming data (sub-second) → Real-Time Dashboard",
                      "Real-Time Dashboard",
                      rationale="Sub-second streaming data requires Real-Time Dashboard for live operational monitoring")
    if _any_of(uc, "kpi", "goal", "okr", "scorecard", "metric"):
        return _match("visualization-selection",
                      "Goal/KPI tracking + check-ins → Metrics Scorecard",
                      "Metrics Scorecard",
                      rationale="KPI/goal tracking use case maps to Metrics Scorecard for structured check-in workflows")
    if _any_of(uc, "pixel", "print", "paginated", "invoice", "regulated", "multi-page"):
        return _match("visualization-selection",
                      "Pixel-perfect / printable / multi-page → Paginated Report",
                      "Paginated Report",
                      rationale="Pixel-perfect/printable requirements map to Paginated Report for regulated or multi-page output")
    if _any_of(inter, "high", "interactive", "filter", "slicer", "drill", "explore", "exploration"):
        return _match("visualization-selection",
                      "Interactive exploration + filters → Power BI Report",
                      "Power BI Report",
                      rationale="Interactive exploration with filters and slicers maps to Power BI Report for self-service analytics")
    if _any_of(uc, "report", "dashboard", "bi", "analytics", "analysis"):
        return _match("visualization-selection",
                      "Interactive exploration + filters → Power BI Report",
                      "Power BI Report",
                      rationale="Interactive exploration with filters and slicers maps to Power BI Report for self-service analytics")

    # Default: most projects need a Power BI report
    if inter or uc:
        return _ambiguous("visualization-selection",
                          ["Power BI Report", "Paginated Report", "Real-Time Dashboard"],
                          "Visualization signals present but no clear match — refine interactivity or use_case",
                          rationale="Visualization signals present but no clear match — refine interactivity or use_case to determine the right report type")
    return _skip("visualization-selection",
                  "No visualization signals detected — provide interactivity or use_case",
                  rationale="No visualization signals found in discovery brief — architect should specify interactivity or use_case")


def resolve_skillset(signals: dict) -> Decision:
    _log("skillset-selection:")
    sk = _norm(signals.get("skillset"))
    tc = _norm(signals.get("team_composition"))

    if _any_of(tc, "mixed", "hybrid", "both"):
        return _match("skillset-selection",
                      "Mixed team (engineers + analysts) → Hybrid [LC/CF]", "Hybrid [LC/CF]",
                      rationale="Mixed team composition (engineers + analysts) requires Hybrid approach supporting both code-first and low-code tools")
    if _any_of(sk, "power query", "business", "analyst", "low-code", "no-code", "citizen"):
        return _match("skillset-selection",
                      "Business Analysts + Power Query → Low-Code [LC]", "Low-Code [LC]",
                      rationale="Business analyst / Power Query skillset maps to Low-Code tools for visual, no-code data preparation")
    if _any_of(sk, "python", "spark", "pyspark", "scala", "kql", "code-first") or \
       (_any_of(sk, "sql") and _any_of(tc, "engineer")):
        if _any_of(sk, "visual", "prefer visual"):
            return _match("skillset-selection",
                          "Engineers + prefer visual tools → Low-Code [LC]", "Low-Code [LC]",
                          rationale="Engineers who prefer visual tools can use Low-Code approach for accelerated development")
        return _match("skillset-selection",
                      "Engineers + Python/Spark/SQL → Code-First [CF]", "Code-First [CF]",
                      rationale="Engineering team with Python/Spark/SQL skills maps to Code-First tools for full programmatic control")
    if _any_of(tc, "engineer", "developer"):
        return _match("skillset-selection",
                      "Engineers + Python/Spark/SQL → Code-First [CF]", "Code-First [CF]",
                      rationale="Engineering team composition maps to Code-First tools for full programmatic control")
    if _any_of(tc, "analyst", "business"):
        return _match("skillset-selection",
                      "Business Analysts + Power Query → Low-Code [LC]", "Low-Code [LC]",
                      rationale="Business analyst team composition maps to Low-Code tools for visual, no-code data preparation")
    if _any_of(sk, "sql") and not tc:
        return _ambiguous("skillset-selection",
                          ["Code-First [CF]", "Hybrid [LC/CF]"],
                          "SQL skillset detected but team_composition unknown — engineers or analysts?",
                          rationale="SQL skillset detected but team composition unknown — need to know if team is engineers or analysts")

    return _skip("skillset-selection",
                  "No skillset signals detected — provide skillset or team_composition",
                  rationale="No skillset signals found in discovery brief — architect should specify skillset or team_composition")


def resolve_parameterization(signals: dict) -> Decision:
    _log("parameterization-selection:")
    env_count = signals.get("environment_count")
    dt = _norm(signals.get("deployment_tool"))
    vol = _norm(signals.get("volume"))

    if env_count is not None:
        try:
            env_count = int(env_count)
        except (ValueError, TypeError):
            env_count = None

    # Infer single-environment for small volume / small team projects
    if env_count is None and _any_of(vol, "small", "low", "handful", "single"):
        env_count = 1

    if env_count is not None and env_count <= 1:
        return _match("parameterization-selection",
                      "Single environment → Environment Variables (or skip)",
                      "Environment Variables",
                      rationale="Single environment requires only Environment Variables for simple key-value configuration")

    is_multi = env_count is not None and env_count > 1

    if is_multi:
        if _any_of(dt, "fabric git", "git integration", "fabric-git"):
            return _match("parameterization-selection",
                          "Multi-env + Fabric Git → Variable Library", "Variable Library",
                          rationale="Multi-environment with Fabric Git Integration maps to Variable Library for workspace-scoped parameter management")
        if _any_of(dt, "fabric-cicd", "cicd library"):
            return _match("parameterization-selection",
                          "Multi-env + fabric-cicd → parameter.yml", "parameter.yml",
                          rationale="Multi-environment with fabric-cicd maps to parameter.yml for declarative, version-controlled configuration")
        if _any_of(dt, "fab", "fab cli"):
            return _match("parameterization-selection",
                          "Multi-env + fab CLI → Environment Variables or Variable Library",
                          "Environment Variables or Variable Library",
                          rationale="Multi-environment with fab CLI maps to Environment Variables or Variable Library depending on complexity")
        return _ambiguous("parameterization-selection",
                          ["Variable Library", "parameter.yml", "Environment Variables"],
                          "Multiple environments but deployment_tool not specified",
                          rationale="Multiple environments detected but deployment tool not specified — need deployment_tool to choose parameterization strategy")

    if dt:
        if _any_of(dt, "fabric-cicd", "cicd library"):
            return _match("parameterization-selection",
                          "Multi-env + fabric-cicd → parameter.yml", "parameter.yml",
                          rationale="fabric-cicd deployment tool maps to parameter.yml for declarative, version-controlled configuration")
        if _any_of(dt, "fabric git", "git integration", "fabric-git"):
            return _match("parameterization-selection",
                          "Multi-env + Fabric Git → Variable Library", "Variable Library",
                          rationale="Fabric Git Integration deployment tool maps to Variable Library for workspace-scoped parameter management")
        if _any_of(dt, "fab", "fab cli"):
            return _match("parameterization-selection",
                          "Single environment → Environment Variables (or skip)",
                          "Environment Variables",
                          rationale="fab CLI without multi-environment maps to Environment Variables for simple key-value configuration")

    return _skip("parameterization-selection",
                  "No parameterization signals detected — provide environment_count and deployment_tool",
                  rationale="No parameterization signals found in discovery brief — architect should specify environment_count and deployment_tool")


def resolve_api(signals: dict) -> Decision:
    _log("api-selection:")
    uc = _norm(signals.get("use_case"))
    api = _norm(signals.get("api_needs"))

    has_api_signal = bool(api) or _any_of(uc, "api", "graphql", "rest", "frontend", "app-backend",
                                          "crud", "function", "endpoint")
    if not has_api_signal:
        return _skip("api-selection",
                      "N/A — no API layer needed for this task flow",
                      rationale="No API signals detected — this task flow does not require an API backend")

    needs_reads = _any_of(api, "read", "query", "flexible", "graphql", "fetch")
    needs_writes = _any_of(api, "write", "logic", "function", "custom", "mutation", "writeback")
    needs_crud = _any_of(api, "crud", "simple", "direct", "internal")

    if _any_of(uc, "crud") or needs_crud:
        return _match("api-selection",
                      "Simple CRUD from internal tools → Direct Connection",
                      "Direct Connection",
                      rationale="Simple CRUD from internal tools maps to Direct Connection for zero-code database access")
    if needs_reads and needs_writes:
        return _match("api-selection",
                      "Both reads AND logic → GraphQL API + User Data Functions",
                      "GraphQL API + User Data Functions",
                      rationale="Both read queries and custom write logic require GraphQL API for flexible reads plus User Data Functions for business logic")
    if needs_reads or _any_of(uc, "graphql"):
        return _match("api-selection",
                      "Flexible read queries → GraphQL API", "GraphQL API",
                      rationale="Flexible read query requirements map to GraphQL API for client-driven data fetching")
    if needs_writes or _any_of(uc, "function", "rest", "custom logic"):
        return _match("api-selection",
                      "Custom business logic/writes → User Data Functions",
                      "User Data Functions",
                      rationale="Custom business logic and write operations map to User Data Functions for server-side processing")

    return _ambiguous("api-selection",
                      ["GraphQL API", "User Data Functions", "Direct Connection"],
                      "API signals present but needs unclear — specify api_needs (read/write/crud)",
                      rationale="API signals present but needs unclear — specify api_needs to determine the right API approach")


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


def _enrich_query_language(signals: dict, storage_choice: str | None) -> None:
    """Inject query_language from the item-type registry when storage is known.

    Only enriches if query_language is not already set in signals and the
    storage item exists in the registry with a query_language field.
    """
    if not storage_choice or signals.get("query_language"):
        return
    try:
        import pathlib
        registry_path = (
            pathlib.Path(__file__).resolve().parents[4]
            / "_shared" / "registry" / "item-type-registry.json"
        )
        with open(registry_path, encoding="utf-8") as f:
            registry = json.load(f)
        item = registry.get("types", {}).get(storage_choice, {})
        langs = item.get("query_language")
        if langs and isinstance(langs, list) and langs:
            signals["query_language"] = langs[0]
            _log(f"  ↳ enriched query_language={langs[0]} from {storage_choice}")
    except (FileNotFoundError, json.JSONDecodeError):
        pass  # Registry unavailable — proceed without enrichment


def _load_task_flow_defaults(task_flow: str) -> dict[str, str]:
    """Load default choices from a task flow template's primaryStorage and first alternativeGroup items.

    Returns a mapping from decision category to default choice, e.g.:
        {"storage": "Lakehouse", "ingestion": "Copy Job", "processing": "Notebook"}
    """
    import pathlib
    registry_path = (
        pathlib.Path(__file__).resolve().parents[4]
        / "_shared" / "registry" / "deployment-order.json"
    )
    try:
        with open(registry_path, encoding="utf-8") as f:
            registry = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

    tf_data = registry.get("taskFlows", {}).get(task_flow, {})
    if not tf_data:
        return {}

    defaults: dict[str, str] = {}

    # Extract primary storage from template metadata
    ps = tf_data.get("primaryStorage", "")
    if "lakehouse" in ps.lower():
        defaults["storage"] = "Lakehouse"
    elif "warehouse" in ps.lower():
        defaults["storage"] = "Warehouse"
    elif "eventhouse" in ps.lower():
        defaults["storage"] = "Eventhouse"

    # Extract first item from each alternative group as the default
    _GROUP_TO_DECISION = {
        "gold-layer": "storage",
        "ingestion": "ingestion",
        "transformation": "processing",
    }
    seen_groups: set[str] = set()
    for item in tf_data.get("items", []):
        group = item.get("alternativeGroup")
        if not group or group in seen_groups:
            continue
        seen_groups.add(group)
        dec_key = _GROUP_TO_DECISION.get(group)
        if dec_key and dec_key not in defaults:
            # Use the item type as the default choice
            defaults[dec_key] = item["itemType"]

    return defaults


def resolve_all(signals: dict, *, task_flow: str | None = None) -> dict:
    """Resolve all 7 architectural decisions from signal inputs.

    Storage is resolved first. If the chosen storage item has a known
    ``query_language`` in the item-type registry and the caller did not
    supply one, the primary language is injected into signals so that
    downstream decisions (especially processing) can benefit.

    When *task_flow* is provided, any decisions that resolve as "na" (no
    signals) are replaced with a default from the task flow template.

    Args:
        signals: Dict with keys like skillset, velocity, volume, query_language,
                 use_case, environment_count, deployment_tool, interactivity,
                 data_pattern, mode, team_composition, api_needs.
        task_flow: Optional task flow name for default fallbacks.

    Returns:
        Dict with 'decisions', 'ambiguous', and 'unresolved' keys.
    """
    VERBOSE_LOG.clear()
    signals = dict(signals)  # shallow copy — don't mutate caller's dict
    decisions: dict[str, dict] = {}
    ambiguous: list[str] = []
    unresolved: list[str] = []

    # Load task flow defaults if available
    tf_defaults = _load_task_flow_defaults(task_flow) if task_flow else {}

    # --- Phase 1: resolve storage first for enrichment --------------------
    _, storage_resolver = RESOLVERS["storage"]
    storage_result = storage_resolver(signals)

    # Apply task-flow default if storage is unresolved
    if storage_result.confidence == "na" and storage_result.choice is None and "storage" in tf_defaults:
        storage_result = _default("storage-selection", tf_defaults["storage"], f"{task_flow} template",
                                  rationale=f"No storage signals detected — defaulting to {tf_defaults['storage']} "
                                  f"based on {task_flow} task flow template primary storage")
    _enrich_query_language(signals, storage_result.choice)

    # --- Phase 2: resolve all (storage result already cached) -------------
    for key, (_guide_id, resolver) in RESOLVERS.items():
        result = storage_result if key == "storage" else resolver(signals)

        # Apply task-flow default if unresolved
        if result.confidence == "na" and result.choice is None and key in tf_defaults:
            result = _default(_guide_id, tf_defaults[key], f"{task_flow} template",
                              rationale=f"No {key} signals detected — defaulting to {tf_defaults[key]} "
                              f"based on {task_flow} task flow template")

        entry: dict = {
            "choice": result.choice,
            "confidence": result.confidence,
            "rule_matched": result.rule_matched,
            "guide": result.guide,
            "rationale": result.rationale,
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
# Discovery brief markdown parser
# ---------------------------------------------------------------------------

# Maps discovery brief signal names to resolver signal keys/values.
_SIGNAL_MAP: dict[str, dict[str, str]] = {
    "batch / scheduled":        {"velocity": "batch"},
    "real-time / streaming":    {"velocity": "real-time"},
    "both / mixed (lambda)":    {"velocity": "both"},
    "machine learning":         {"use_case": "ml"},
    "sensitive data":           {"use_case": "compliance"},
    "transactional":            {"use_case": "transactional"},
    "unstructured / semi-structured": {"data_pattern": "unstructured"},
    "data quality / layered":   {"data_pattern": "layered"},
    "application backend":      {"use_case": "app"},
    "document / nosql / ai-ready": {"query_language": "nosql"},
    "semantic governance":      {},  # informational only
}

# Maps 4V names to resolver keys.
_V_MAP: dict[str, str] = {
    "volume": "volume",
    "velocity": "velocity",
    "variety": "variety",
    "versatility": "versatility",
}

# Extracts skillset and query_language from versatility values.
_VERSATILITY_KEYWORDS: dict[str, dict[str, str]] = {
    "code-first": {"skillset": "code-first"},
    "code first": {"skillset": "code-first"},
    "low-code":   {"skillset": "low-code"},
    "low code":   {"skillset": "low-code"},
    "python":     {"skillset": "python"},
    "spark":      {"skillset": "spark", "query_language": "spark"},
    "pyspark":    {"skillset": "pyspark", "query_language": "spark"},
    "sql":        {"query_language": "t-sql"},
    "t-sql":      {"query_language": "t-sql"},
    "kql":        {"query_language": "kql"},
    "nosql":      {"query_language": "nosql"},
}


def _parse_md_table(lines: list[str], start: int) -> list[list[str]]:
    """Parse a markdown table starting at the header row index.

    Returns a list of row-cells (list of stripped strings), skipping
    the header and separator rows.
    """
    rows: list[list[str]] = []
    i = start
    # Skip header row
    if i < len(lines) and "|" in lines[i]:
        i += 1
    # Skip separator row (|---|---|...)
    if i < len(lines) and "|" in lines[i] and "-" in lines[i]:
        i += 1
    # Parse data rows
    while i < len(lines):
        line = lines[i].strip()
        if not line or "|" not in line:
            break
        cells = [c.strip() for c in line.split("|")]
        # Remove empty leading/trailing cells from | col1 | col2 |
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        rows.append(cells)
        i += 1
    return rows


def _extract_confidence(text: str) -> str:
    """Extract confidence level from a cell like '**High**' or 'Medium'."""
    clean = text.replace("*", "").strip().lower()
    if clean in ("high", "medium", "low"):
        return clean
    return "low"


def _extract_signals_from_brief(path: str) -> dict:
    """Extract resolver signal keys from a discovery brief markdown file.

    Parses the '### Inferred Signals' and '### 4 V\\'s Assessment' tables
    and maps their values to the flat signal dict expected by resolve_all().
    """
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    lines = [l.rstrip("\n") for l in lines]
    signals: dict = {}

    # Find and parse the Inferred Signals table
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("### inferred signals"):
            # Find the table header (next line with |)
            for j in range(i + 1, min(i + 5, len(lines))):
                if "|" in lines[j] and "signal" in lines[j].lower():
                    rows = _parse_md_table(lines, j)
                    for row in rows:
                        if len(row) < 3:
                            continue
                        signal_name = row[0].replace("*", "").strip().lower()
                        confidence = _extract_confidence(row[2]) if len(row) > 2 else "low"
                        # Skip low-confidence signals
                        if confidence == "low":
                            continue
                        # Map signal name to resolver keys
                        for pattern, key_vals in _SIGNAL_MAP.items():
                            if pattern in signal_name:
                                for k, v in key_vals.items():
                                    # velocity: prefer "both" over single values
                                    if k == "velocity" and signals.get("velocity") == "both":
                                        continue
                                    # use_case: accumulate multiple values
                                    if k == "use_case" and k in signals:
                                        signals[k] = signals[k] + "+" + v
                                    else:
                                        signals[k] = v
                                break
                    break

    # Find and parse the 4 V's Assessment table
    for i, line in enumerate(lines):
        stripped = line.strip().lower()
        if "### 4 v" in stripped and "assessment" in stripped:
            for j in range(i + 1, min(i + 5, len(lines))):
                if "|" in lines[j] and ("v" in lines[j].lower() or "value" in lines[j].lower()):
                    rows = _parse_md_table(lines, j)
                    for row in rows:
                        if len(row) < 3:
                            continue
                        v_name = row[0].replace("*", "").strip().lower()
                        v_value = row[1].replace("*", "").strip().lower()
                        confidence = _extract_confidence(row[2]) if len(row) > 2 else "low"
                        if confidence == "low":
                            continue

                        resolver_key = _V_MAP.get(v_name)
                        if not resolver_key:
                            continue

                        if resolver_key == "volume":
                            # Normalize volume: look for size indicators
                            if any(t in v_value for t in ("tb", "terabyte", "massive", "huge", "million", "billion", "10+")):
                                signals["volume"] = "large"
                            elif any(t in v_value for t in ("gb", "thousand", "small", "moderate")):
                                signals["volume"] = "small"
                            else:
                                signals["volume"] = v_value

                        elif resolver_key == "velocity":
                            # 4V velocity overrides signal-inferred velocity.
                            # Check compound values FIRST — "batch primary,
                            # near-real-time secondary" must map to "both", not
                            # match "real-time" as a substring of "near-real-time".
                            has_batch = "batch" in v_value
                            has_rt = any(t in v_value for t in ("real-time", "realtime", "streaming", "stream"))
                            if has_batch and has_rt:
                                signals["velocity"] = "both"
                            elif any(t in v_value for t in ("both", "batch + real", "batch+real", "mixed")):
                                signals["velocity"] = "both"
                            elif has_rt and not has_batch:
                                signals["velocity"] = "real-time"
                            elif has_batch:
                                signals["velocity"] = "batch"

                        elif resolver_key == "versatility":
                            # Extract skillset and query_language from versatility
                            for keyword, kv in _VERSATILITY_KEYWORDS.items():
                                if keyword in v_value:
                                    signals.update(kv)

                        elif resolver_key == "variety":
                            signals["variety"] = v_value
                            # Extract use_case signals from variety descriptions
                            _VARIETY_USE_CASES = {
                                "iot": "iot", "sensor": "iot", "telemetry": "iot",
                                "time-series": "time-series", "timeseries": "time-series",
                                "pos": "transactional", "point of sale": "transactional",
                                "social": "social", "social media": "social",
                                "log": "logs", "logs": "logs",
                            }
                            for keyword, uc_val in _VARIETY_USE_CASES.items():
                                if keyword in v_value:
                                    existing_uc = signals.get("use_case", "")
                                    if uc_val not in existing_uc:
                                        signals["use_case"] = (existing_uc + "+" + uc_val).lstrip("+") if existing_uc else uc_val

                    break

    # If versatility gave us skillset=code-first but no query_language,
    # and we have sql in the raw value, set it
    if signals.get("skillset") == "code-first" and "query_language" not in signals:
        # Re-scan for versatility row to check for sql
        for i, line in enumerate(lines):
            stripped = line.strip().lower()
            if "### 4 v" in stripped and "assessment" in stripped:
                for j in range(i + 1, min(i + 5, len(lines))):
                    if "|" in lines[j]:
                        rows = _parse_md_table(lines, j)
                        for row in rows:
                            if len(row) >= 2 and row[0].strip().lower() == "versatility":
                                if "sql" in row[1].lower():
                                    signals["query_language"] = "t-sql"
                        break

    # Default use_case to analytics if not set and batch/both velocity
    if signals.get("velocity") in ("batch", "both"):
        existing = signals.get("use_case", "")
        if "analytics" not in existing:
            signals["use_case"] = (existing + "+analytics").lstrip("+") if existing else "analytics"

    # Infer query_language from use_case when not explicitly set
    uc = signals.get("use_case", "")
    if "query_language" not in signals:
        if any(t in uc for t in ("iot", "time-series", "telemetry", "logs")):
            signals["query_language"] = "kql"

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
                       help="Path to a signals file (JSON or key: value format)")
    group.add_argument("--discovery-brief", type=str,
                       help="Path to a discovery brief markdown file")
    parser.add_argument("--format", choices=["yaml", "json"], default="json",
                        help="Output format (default: json)")
    parser.add_argument("--task-flow", type=str, default=None,
                        help="Task flow name (e.g., medallion) for default fallbacks")
    parser.add_argument("--verbose", action="store_true",
                        help="Print rule evaluation trace to stderr")
    args = parser.parse_args()

    if args.signals:
        try:
            signals = json.loads(args.signals)
        except json.JSONDecodeError as e:
            print(f"Error: invalid JSON in --signals: {e}", file=sys.stderr)
            sys.exit(2)
    elif args.signals_file:
        try:
            signals = _load_yaml_signals(args.signals_file)
        except FileNotFoundError:
            print(f"Error: file not found: {args.signals_file}", file=sys.stderr)
            sys.exit(2)
        except Exception as e:
            print(f"Error reading signals file: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        try:
            signals = _extract_signals_from_brief(args.discovery_brief)
        except FileNotFoundError:
            print(f"Error: file not found: {args.discovery_brief}", file=sys.stderr)
            sys.exit(2)
        except Exception as e:
            print(f"Error reading discovery brief: {e}", file=sys.stderr)
            sys.exit(2)

    result = resolve_all(signals, task_flow=args.task_flow)

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
