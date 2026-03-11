"""Tests for decision-resolver.py — verifies deterministic decision resolution."""

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

SHARED_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SHARED_DIR / "lib"))
sys.path.insert(0, str(SHARED_DIR / "scripts"))

REPO_ROOT = SHARED_DIR.parent
DESIGN_SKILL = REPO_ROOT / ".github" / "skills" / "fabric-design"

# Import the module via importlib since it lives under .github/skills/
spec = importlib.util.spec_from_file_location(
    "decision_resolver",
    str(DESIGN_SKILL / "scripts" / "decision-resolver.py"),
)
mod = importlib.util.module_from_spec(spec)
sys.modules["decision_resolver"] = mod
spec.loader.exec_module(mod)

_norm = mod._norm
_any_of = mod._any_of
Decision = mod.Decision
resolve_storage = mod.resolve_storage
resolve_ingestion = mod.resolve_ingestion
resolve_processing = mod.resolve_processing
resolve_visualization = mod.resolve_visualization
resolve_skillset = mod.resolve_skillset
resolve_parameterization = mod.resolve_parameterization
resolve_api = mod.resolve_api
resolve_all = mod.resolve_all
_load_yaml_signals = mod._load_yaml_signals
_to_yaml = mod._to_yaml
_to_json = mod._to_json
VERBOSE_LOG = mod.VERBOSE_LOG


# ── _norm helper ─────────────────────────────────────────────────────────

def test_norm_lowercases_and_strips():
    assert _norm("  Python  ") == "python"


def test_norm_none_returns_empty():
    assert _norm(None) == ""


def test_norm_empty_string():
    assert _norm("") == ""


def test_norm_already_lowercase():
    assert _norm("spark") == "spark"


# ── _any_of helper ───────────────────────────────────────────────────────

def test_any_of_matches_substring():
    assert _any_of("pyspark", "spark") is True


def test_any_of_matches_exact():
    assert _any_of("python", "python") is True


def test_any_of_no_match():
    assert _any_of("python", "sql", "kql") is False


def test_any_of_none_signal():
    assert _any_of(None, "spark") is False


def test_any_of_empty_signal():
    assert _any_of("", "spark") is False


def test_any_of_case_insensitive():
    assert _any_of("PySpark", "spark") is True


def test_any_of_multiple_terms():
    assert _any_of("t-sql", "t-sql", "tsql") is True


# ── Decision dataclass ───────────────────────────────────────────────────

def test_decision_defaults():
    d = Decision(choice="Lakehouse", confidence="high", rule_matched="test",
                 guide="decisions/storage-selection.md")
    assert d.note is None
    assert d.candidates == []


def test_decision_with_candidates():
    d = Decision(choice=None, confidence="ambiguous", rule_matched=None,
                 guide="decisions/test.md", note="unclear",
                 candidates=["A", "B"])
    assert d.candidates == ["A", "B"]
    assert d.note == "unclear"


# ── resolve_storage ──────────────────────────────────────────────────────

def test_storage_spark_query_language():
    d = resolve_storage({"query_language": "Spark"})
    assert d.choice == "Lakehouse"
    assert d.confidence == "high"


def test_storage_python_skillset():
    d = resolve_storage({"skillset": "python"})
    assert d.choice == "Lakehouse"
    assert d.confidence == "high"


def test_storage_kql_query_language():
    d = resolve_storage({"query_language": "KQL"})
    assert d.choice == "Eventhouse"
    assert d.confidence == "high"


def test_storage_iot_use_case():
    d = resolve_storage({"use_case": "IoT"})
    assert d.choice == "Eventhouse"


def test_storage_tsql_analytics():
    d = resolve_storage({"query_language": "T-SQL", "use_case": "analytics"})
    assert d.choice == "Warehouse"
    assert d.confidence == "high"


def test_storage_tsql_transactional():
    d = resolve_storage({"query_language": "T-SQL", "use_case": "transactional"})
    assert d.choice == "SQL Database"


def test_storage_tsql_ambiguous():
    d = resolve_storage({"query_language": "T-SQL"})
    assert d.confidence == "ambiguous"
    assert "Warehouse" in d.candidates
    assert "SQL Database" in d.candidates


def test_storage_nosql_use_case():
    d = resolve_storage({"use_case": "document"})
    assert d.choice == "Cosmos DB"


def test_storage_postgres():
    d = resolve_storage({"query_language": "postgres"})
    assert d.choice == "PostgreSQL"


def test_storage_no_signals():
    d = resolve_storage({})
    assert d.confidence == "na"
    assert d.choice is None


def test_storage_sql_skillset_no_query_language():
    d = resolve_storage({"skillset": "sql"})
    assert d.confidence == "ambiguous"


# ── resolve_ingestion ────────────────────────────────────────────────────

def test_ingestion_streaming():
    d = resolve_ingestion({"velocity": "real-time"})
    assert d.choice == "Eventstream"
    assert d.confidence == "high"


def test_ingestion_cdc():
    d = resolve_ingestion({"data_pattern": "CDC"})
    assert d.choice == "Mirroring"


def test_ingestion_complex_orchestration():
    d = resolve_ingestion({"data_pattern": "complex orchestration"})
    assert d.choice == "Pipeline"


def test_ingestion_large_code_first():
    d = resolve_ingestion({"volume": "large", "skillset": "python"})
    assert d.choice == "Pipeline + Notebook"


def test_ingestion_large_no_code():
    d = resolve_ingestion({"volume": "large"})
    assert d.choice == "Pipeline (Copy activity)"


def test_ingestion_small_transforms():
    d = resolve_ingestion({"volume": "small", "data_pattern": "transform"})
    assert d.choice == "Dataflow Gen2"


def test_ingestion_small_no_transforms():
    d = resolve_ingestion({"volume": "small", "data_pattern": "as-is"})
    assert d.choice == "Copy Job"


def test_ingestion_small_ambiguous():
    d = resolve_ingestion({"volume": "small"})
    assert d.confidence == "ambiguous"
    assert "Dataflow Gen2" in d.candidates


def test_ingestion_no_signals():
    d = resolve_ingestion({})
    assert d.confidence == "na"
    assert d.choice is None


# ── resolve_processing ───────────────────────────────────────────────────

def test_processing_interactive_spark():
    d = resolve_processing({"mode": "interactive", "skillset": "python"})
    assert d.choice == "Notebook"


def test_processing_interactive_kql():
    d = resolve_processing({"mode": "interactive", "query_language": "KQL"})
    assert d.choice == "KQL Queryset"


def test_processing_interactive_visual():
    d = resolve_processing({"mode": "interactive", "skillset": "low-code"})
    assert d.choice == "Dataflow Gen2"


def test_processing_production_spark_cicd():
    d = resolve_processing({
        "mode": "production", "skillset": "spark",
        "deployment_tool": "fabric-cicd",
    })
    assert d.choice == "Spark Job Definition"


def test_processing_production_spark_simple():
    d = resolve_processing({"mode": "production", "skillset": "spark"})
    assert d.choice == "Notebook (via Pipeline)"


def test_processing_production_tsql():
    d = resolve_processing({"mode": "production", "query_language": "T-SQL"})
    assert d.choice == "Stored Procedures"


def test_processing_no_mode_spark():
    d = resolve_processing({"skillset": "python"})
    assert d.choice == "Notebook"


def test_processing_no_signals():
    d = resolve_processing({})
    assert d.confidence == "na"


# ── resolve_visualization ────────────────────────────────────────────────

def test_visualization_geospatial():
    d = resolve_visualization({"use_case": "geospatial"})
    assert d.choice == "Real-Time Map"


def test_visualization_streaming():
    d = resolve_visualization({"velocity": "real-time"})
    assert d.choice == "Real-Time Dashboard"


def test_visualization_kpi():
    d = resolve_visualization({"use_case": "KPI"})
    assert d.choice == "Metrics Scorecard"


def test_visualization_paginated():
    d = resolve_visualization({"use_case": "paginated"})
    assert d.choice == "Paginated Report"


def test_visualization_interactive():
    d = resolve_visualization({"interactivity": "high"})
    assert d.choice == "Power BI Report"


def test_visualization_analytics_use_case():
    d = resolve_visualization({"use_case": "analytics"})
    assert d.choice == "Power BI Report"


def test_visualization_no_signals():
    d = resolve_visualization({})
    assert d.confidence == "na"


# ── resolve_skillset ─────────────────────────────────────────────────────

def test_skillset_mixed_team():
    d = resolve_skillset({"team_composition": "mixed"})
    assert d.choice == "Hybrid [LC/CF]"


def test_skillset_python():
    d = resolve_skillset({"skillset": "python"})
    assert d.choice == "Code-First [CF]"


def test_skillset_low_code():
    d = resolve_skillset({"skillset": "low-code"})
    assert d.choice == "Low-Code [LC]"


def test_skillset_engineer_team():
    d = resolve_skillset({"team_composition": "engineer"})
    assert d.choice == "Code-First [CF]"


def test_skillset_analyst_team():
    d = resolve_skillset({"team_composition": "analyst"})
    assert d.choice == "Low-Code [LC]"


def test_skillset_sql_ambiguous():
    d = resolve_skillset({"skillset": "sql"})
    assert d.confidence == "ambiguous"


def test_skillset_no_signals():
    d = resolve_skillset({})
    assert d.confidence == "na"


# ── resolve_parameterization ─────────────────────────────────────────────

def test_param_single_env():
    d = resolve_parameterization({"environment_count": 1})
    assert d.choice == "Environment Variables"


def test_param_multi_env_fabric_git():
    d = resolve_parameterization({
        "environment_count": 3, "deployment_tool": "Fabric Git",
    })
    assert d.choice == "Variable Library"


def test_param_multi_env_fabric_cicd():
    d = resolve_parameterization({
        "environment_count": 2, "deployment_tool": "fabric-cicd",
    })
    assert d.choice == "parameter.yml"


def test_param_multi_env_no_tool():
    d = resolve_parameterization({"environment_count": 2})
    assert d.confidence == "ambiguous"


def test_param_no_signals():
    d = resolve_parameterization({})
    assert d.confidence == "na"


def test_param_env_count_string_parseable():
    d = resolve_parameterization({"environment_count": "1"})
    assert d.choice == "Environment Variables"


def test_param_env_count_invalid():
    d = resolve_parameterization({"environment_count": "abc"})
    assert d.confidence != "high" or d.choice is None


# ── resolve_api ──────────────────────────────────────────────────────────

def test_api_crud():
    d = resolve_api({"use_case": "crud"})
    assert d.choice == "Direct Connection"


def test_api_read_queries():
    d = resolve_api({"api_needs": "read", "use_case": "api"})
    assert d.choice == "GraphQL API"


def test_api_write_logic():
    d = resolve_api({"api_needs": "write", "use_case": "api"})
    assert d.choice == "User Data Functions"


def test_api_both_read_write():
    d = resolve_api({"api_needs": "read and write", "use_case": "api"})
    assert d.choice == "GraphQL API + User Data Functions"


def test_api_no_signals():
    d = resolve_api({})
    assert d.confidence == "na"


def test_api_graphql_use_case():
    d = resolve_api({"use_case": "graphql"})
    assert d.choice == "GraphQL API"


# ── resolve_all integration ──────────────────────────────────────────────

def test_resolve_all_returns_all_seven_decisions():
    result = resolve_all({"skillset": "python", "velocity": "batch"})
    assert "decisions" in result
    assert "ambiguous" in result
    assert "unresolved" in result
    assert len(result["decisions"]) == 7
    expected_keys = {
        "storage", "ingestion", "processing", "visualization",
        "skillset", "parameterization", "api",
    }
    assert set(result["decisions"].keys()) == expected_keys


def test_resolve_all_decision_fields():
    result = resolve_all({"skillset": "python"})
    for key, decision in result["decisions"].items():
        assert "choice" in decision
        assert "confidence" in decision
        assert "rule_matched" in decision
        assert "guide" in decision
        assert decision["guide"].startswith("decisions/")
        assert decision["guide"].endswith(".md")


def test_resolve_all_high_confidence_scenario():
    signals = {
        "skillset": "python",
        "query_language": "Spark",
        "velocity": "batch",
        "volume": "large",
        "mode": "interactive",
        "interactivity": "high",
        "team_composition": "engineer",
        "environment_count": 1,
    }
    result = resolve_all(signals)
    assert result["decisions"]["storage"]["choice"] == "Lakehouse"
    assert result["decisions"]["storage"]["confidence"] == "high"
    assert result["decisions"]["processing"]["choice"] == "Notebook"
    assert result["decisions"]["skillset"]["choice"] == "Code-First [CF]"
    assert result["decisions"]["parameterization"]["choice"] == "Environment Variables"
    assert result["decisions"]["visualization"]["choice"] == "Power BI Report"


def test_resolve_all_empty_signals():
    result = resolve_all({})
    assert len(result["unresolved"]) > 0
    for key, decision in result["decisions"].items():
        assert decision["confidence"] in ("high", "ambiguous", "na")


def test_resolve_all_ambiguous_tracked():
    result = resolve_all({"query_language": "T-SQL"})
    assert "storage" in result["ambiguous"]


def test_resolve_all_clears_verbose_log():
    """Verify VERBOSE_LOG is cleared between calls."""
    resolve_all({"skillset": "python"})
    first_log_len = len(VERBOSE_LOG)
    resolve_all({"skillset": "python"})
    assert len(VERBOSE_LOG) == first_log_len


# ── _load_yaml_signals ───────────────────────────────────────────────────

def test_load_yaml_signals_basic():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False,
                                     encoding="utf-8") as f:
        f.write("skillset: python\nvolume: large\n")
        f.flush()
        signals = _load_yaml_signals(f.name)
    assert signals["skillset"] == "python"
    assert signals["volume"] == "large"
    Path(f.name).unlink()


def test_load_yaml_signals_integer():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False,
                                     encoding="utf-8") as f:
        f.write("environment_count: 3\n")
        f.flush()
        signals = _load_yaml_signals(f.name)
    assert signals["environment_count"] == 3
    Path(f.name).unlink()


def test_load_yaml_signals_null():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False,
                                     encoding="utf-8") as f:
        f.write("api_needs: null\n")
        f.flush()
        signals = _load_yaml_signals(f.name)
    assert signals["api_needs"] is None
    Path(f.name).unlink()


def test_load_yaml_signals_comments_and_blanks():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False,
                                     encoding="utf-8") as f:
        f.write("# comment\n\nskillset: python\n# another\nvolume: small\n")
        f.flush()
        signals = _load_yaml_signals(f.name)
    assert len(signals) == 2
    assert signals["skillset"] == "python"
    Path(f.name).unlink()


def test_load_yaml_signals_quoted_value():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False,
                                     encoding="utf-8") as f:
        f.write('skillset: "python"\n')
        f.flush()
        signals = _load_yaml_signals(f.name)
    assert signals["skillset"] == "python"
    Path(f.name).unlink()


def test_load_yaml_signals_empty_value():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False,
                                     encoding="utf-8") as f:
        f.write("skillset:\n")
        f.flush()
        signals = _load_yaml_signals(f.name)
    assert signals["skillset"] is None
    Path(f.name).unlink()


# ── Output formatting ────────────────────────────────────────────────────

def test_to_yaml_output():
    result = resolve_all({"skillset": "python"})
    output = _to_yaml(result)
    assert output.startswith("decisions:")
    assert "storage:" in output
    assert "ambiguous:" in output
    assert "unresolved:" in output


def test_to_json_output():
    result = resolve_all({"skillset": "python"})
    output = _to_json(result)
    parsed = json.loads(output)
    assert "decisions" in parsed
    assert "ambiguous" in parsed
    assert "unresolved" in parsed


def test_to_json_roundtrip():
    result = resolve_all({"skillset": "python", "velocity": "batch"})
    output = _to_json(result)
    parsed = json.loads(output)
    assert parsed["decisions"]["storage"]["choice"] == result["decisions"]["storage"]["choice"]


# ── Edge cases ───────────────────────────────────────────────────────────

def test_signals_with_none_values():
    """Signals dict with explicit None values should not crash."""
    result = resolve_all({
        "skillset": None,
        "velocity": None,
        "volume": None,
    })
    assert "decisions" in result


def test_signals_with_empty_strings():
    """Signals dict with empty string values should be treated as absent."""
    result = resolve_all({
        "skillset": "",
        "velocity": "",
    })
    for key in result["decisions"]:
        assert result["decisions"][key]["confidence"] in ("high", "ambiguous", "na")


def test_signals_with_extra_unknown_keys():
    """Extra signal keys should be silently ignored."""
    result = resolve_all({
        "skillset": "python",
        "unknown_field": "whatever",
        "another_extra": 42,
    })
    assert result["decisions"]["storage"]["choice"] == "Lakehouse"


def test_pyspark_skillset_resolves_lakehouse():
    """PySpark is a Spark variant — should resolve to Lakehouse."""
    d = resolve_storage({"skillset": "pyspark"})
    assert d.choice == "Lakehouse"


def test_guide_paths_use_decision_id():
    """Every decision guide path should match 'decisions/{id}.md'."""
    result = resolve_all({})
    for key, decision in result["decisions"].items():
        assert decision["guide"] == f"decisions/{key}-selection.md"


def test_stream_data_pattern_triggers_eventstream():
    d = resolve_ingestion({"data_pattern": "streaming"})
    assert d.choice == "Eventstream"


def test_visualization_ambiguous_when_signal_present_but_unclear():
    d = resolve_visualization({"interactivity": "medium"})
    assert d.confidence == "ambiguous"


# ── _extract_signals_from_brief ──────────────────────────────────────────

_extract_signals_from_brief = mod._extract_signals_from_brief


def test_extract_brief_velocity_both():
    brief = _write_brief(signals=[
        ("Both / Mixed (Lambda)", "Batch + real-time", "**High**", "user confirmed"),
    ])
    result = _extract_signals_from_brief(brief)
    assert result["velocity"] == "both"


def test_extract_brief_velocity_batch():
    brief = _write_brief(signals=[
        ("Batch / Scheduled", "Analytics", "**High**", "reporting"),
    ])
    result = _extract_signals_from_brief(brief)
    assert result["velocity"] == "batch"


def test_extract_brief_velocity_realtime():
    brief = _write_brief(signals=[
        ("Real-time / Streaming", "Event analytics", "**High**", "IoT"),
    ])
    result = _extract_signals_from_brief(brief)
    assert result["velocity"] == "real-time"


def test_extract_brief_skips_low_confidence():
    brief = _write_brief(signals=[
        ("Machine Learning", "ML models", "**Low**", "mentioned once"),
    ])
    result = _extract_signals_from_brief(brief)
    assert "use_case" not in result or "ml" not in result.get("use_case", "")


def test_extract_brief_ml_signal():
    brief = _write_brief(signals=[
        ("Machine Learning", "Predictive models", "**High**", "AI-first"),
    ])
    result = _extract_signals_from_brief(brief)
    assert "ml" in result.get("use_case", "")


def test_extract_brief_sensitive_data():
    brief = _write_brief(signals=[
        ("Sensitive Data", "Patient data", "**High**", "HIPAA"),
    ])
    result = _extract_signals_from_brief(brief)
    assert "compliance" in result.get("use_case", "")


def test_extract_brief_4vs_volume_small():
    brief = _write_brief(vs=[
        ("Volume", "GBs — thousands of records", "**High**", "user confirmed"),
    ])
    result = _extract_signals_from_brief(brief)
    assert result["volume"] == "small"


def test_extract_brief_4vs_volume_large():
    brief = _write_brief(vs=[
        ("Volume", "TBs — millions of records", "**High**", "user confirmed"),
    ])
    result = _extract_signals_from_brief(brief)
    assert result["volume"] == "large"


def test_extract_brief_4vs_versatility_sql():
    brief = _write_brief(vs=[
        ("Versatility", "Code-first (SQL)", "**High**", "user confirmed"),
    ])
    result = _extract_signals_from_brief(brief)
    assert result["skillset"] == "code-first"
    assert result["query_language"] == "t-sql"


def test_extract_brief_4vs_versatility_python():
    brief = _write_brief(vs=[
        ("Versatility", "Python and Spark", "**High**", "user confirmed"),
    ])
    result = _extract_signals_from_brief(brief)
    assert result["skillset"] == "spark"
    assert result["query_language"] == "spark"


def test_extract_brief_analytics_default_for_batch():
    brief = _write_brief(signals=[
        ("Batch / Scheduled", "Reporting", "**High**", "metrics"),
    ])
    result = _extract_signals_from_brief(brief)
    assert "analytics" in result.get("use_case", "")


def test_extract_brief_no_analytics_default_for_realtime():
    brief = _write_brief(signals=[
        ("Real-time / Streaming", "Event analytics", "**High**", "IoT"),
    ])
    result = _extract_signals_from_brief(brief)
    # Should not force analytics for pure real-time
    uc = result.get("use_case", "")
    assert "analytics" not in uc or uc == ""


def test_extract_brief_end_to_end_resolves():
    """Full discovery brief produces resolvable signals."""
    brief = _write_brief(
        signals=[
            ("Batch / Scheduled", "Analytics", "**High**", "metrics"),
            ("Real-time / Streaming", "Events", "**High**", "IoT"),
            ("Both / Mixed (Lambda)", "Combined", "**High**", "confirmed"),
        ],
        vs=[
            ("Volume", "GBs data", "**High**", "confirmed"),
            ("Velocity", "Both batch + real-time", "**High**", "confirmed"),
            ("Variety", "SQL DBs, files, APIs", "**High**", "confirmed"),
            ("Versatility", "Code-first (SQL)", "**High**", "confirmed"),
        ],
    )
    signals = _extract_signals_from_brief(brief)
    result = resolve_all(signals)
    # At least storage, ingestion, skillset should resolve
    assert result["decisions"]["storage"]["confidence"] == "high"
    assert result["decisions"]["skillset"]["confidence"] == "high"


def test_extract_brief_real_file():
    """Test with the actual patient-insight-hub discovery brief if it exists."""
    brief_path = str(REPO_ROOT / "_projects" / "patient-insight-hub" / "prd" / "discovery-brief.md")
    try:
        signals = _extract_signals_from_brief(brief_path)
    except FileNotFoundError:
        return  # skip if project doesn't exist
    result = resolve_all(signals)
    assert result["decisions"]["storage"]["confidence"] == "high"
    assert result["decisions"]["skillset"]["confidence"] == "high"


# ── Helper to create test discovery briefs ───────────────────────────────

def _write_brief(signals=None, vs=None):
    """Write a temporary discovery brief and return its path."""
    lines = ["## Discovery Brief\n", "\n", "**Project:** test-project\n", "\n"]

    if signals:
        lines.append("### Inferred Signals\n")
        lines.append("\n")
        lines.append("| Signal | Value | Confidence | Source |\n")
        lines.append("|--------|-------|------------|--------|\n")
        for row in signals:
            lines.append(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |\n")
        lines.append("\n")

    if vs:
        lines.append("### 4 V's Assessment\n")
        lines.append("\n")
        lines.append("| V | Value | Confidence | Source |\n")
        lines.append("|---|-------|------------|--------|\n")
        for row in vs:
            lines.append(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |\n")
        lines.append("\n")

    f = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8")
    f.writelines(lines)
    f.close()
    return f.name
