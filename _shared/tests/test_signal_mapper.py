"""Tests for signal-mapper.py — verifies keyword matching, candidate ranking,
ambiguity detection, and intake question generation."""

import importlib.util
import sys
from pathlib import Path

SHARED_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SHARED_DIR.parent
DISCOVER_SKILL = REPO_ROOT / ".github" / "skills" / "fabric-discover"
SCRIPT_PATH = DISCOVER_SKILL / "scripts" / "signal-mapper.py"


def _load_module():
    """Dynamically load signal-mapper.py (hyphenated name requires importlib)."""
    spec = importlib.util.spec_from_file_location("signal_mapper", str(SCRIPT_PATH))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["signal_mapper"] = mod
    spec.loader.exec_module(mod)
    return mod


sm = _load_module()


# ── Module-level sanity ──────────────────────────────────────────────────


def test_categories_loaded():
    """Signal categories load from JSON and are non-empty."""
    assert len(sm.CATEGORIES) >= 10, "Expected at least 10 signal categories"
    has_candidates = 0
    for cat in sm.CATEGORIES:
        assert cat.id > 0
        assert cat.name
        assert len(cat.keywords) > 0, f"Category {cat.id} has no keywords"
        if len(cat.task_flow_candidates) > 0:
            has_candidates += 1
    assert has_candidates >= 10, "Most categories should have task flow candidates"


def test_keyword_patterns_built():
    """Compiled keyword patterns should be non-empty and cover all categories."""
    assert len(sm.KEYWORD_PATTERNS) > 0
    cat_ids_in_patterns = {kp.category_id for kp in sm.KEYWORD_PATTERNS}
    cat_ids_in_categories = {c.id for c in sm.CATEGORIES}
    assert cat_ids_in_patterns == cat_ids_in_categories, "Patterns should cover every category"


# ── CategoryResult dataclass ─────────────────────────────────────────────


def test_category_result_hit_count():
    """hit_count returns the number of matches."""
    cat = sm.CATEGORIES[0]
    cr = sm.CategoryResult(category=cat)
    assert cr.hit_count == 0
    cr.matches.append(sm.KeywordMatch(keyword="test", start=0, end=4))
    assert cr.hit_count == 1


def test_category_result_confidence_low():
    """1 match → low confidence."""
    cat = sm.CATEGORIES[0]
    cr = sm.CategoryResult(category=cat, matches=[
        sm.KeywordMatch(keyword="a", start=0, end=1),
    ])
    assert cr.confidence == "low"


def test_category_result_confidence_medium():
    """2 matches → medium confidence."""
    cat = sm.CATEGORIES[0]
    cr = sm.CategoryResult(category=cat, matches=[
        sm.KeywordMatch(keyword="a", start=0, end=1),
        sm.KeywordMatch(keyword="b", start=2, end=3),
    ])
    assert cr.confidence == "medium"


def test_category_result_confidence_high():
    """3+ matches → high confidence."""
    cat = sm.CATEGORIES[0]
    cr = sm.CategoryResult(category=cat, matches=[
        sm.KeywordMatch(keyword="a", start=0, end=1),
        sm.KeywordMatch(keyword="b", start=2, end=3),
        sm.KeywordMatch(keyword="c", start=4, end=5),
    ])
    assert cr.confidence == "high"


def test_category_result_matched_keywords_deduplicates():
    """matched_keywords de-duplicates while preserving order."""
    cat = sm.CATEGORIES[0]
    cr = sm.CategoryResult(category=cat, matches=[
        sm.KeywordMatch(keyword="streaming", start=0, end=9),
        sm.KeywordMatch(keyword="kafka", start=10, end=15),
        sm.KeywordMatch(keyword="streaming", start=20, end=29),
    ])
    assert cr.matched_keywords == ["streaming", "kafka"]


# ── map_signals: return structure ────────────────────────────────────────


def test_map_signals_returns_required_keys():
    """map_signals always returns the five documented keys."""
    result = sm.map_signals("anything")
    for key in ("signals", "task_flow_candidates", "primary_velocity", "ambiguous", "keyword_coverage"):
        assert key in result, f"Missing key: {key}"


def test_map_signals_signals_structure():
    """Each signal dict has the expected fields."""
    result = sm.map_signals("real-time streaming kafka sensors")
    assert len(result["signals"]) > 0
    sig = result["signals"][0]
    for field in ("signal", "value", "velocity", "confidence", "source_keywords", "source_quotes"):
        assert field in sig, f"Signal missing field: {field}"


# ── map_signals: empty / no-match input ──────────────────────────────────


def test_map_signals_empty_string():
    """Empty input produces no signals."""
    result = sm.map_signals("")
    assert result["signals"] == []
    assert result["task_flow_candidates"] == []
    assert result["primary_velocity"] == "unknown"
    assert result["ambiguous"] is False


def test_map_signals_no_matches():
    """Gibberish input produces no signals."""
    result = sm.map_signals("xyzzy plugh quux")
    assert result["signals"] == []
    assert result["task_flow_candidates"] == []
    assert result["primary_velocity"] == "unknown"


# ── map_signals: single strong match ─────────────────────────────────────


def test_map_signals_streaming_keywords():
    """Real-time keywords map to streaming/event-analytics signal."""
    result = sm.map_signals("real-time streaming IoT sensors alert monitoring")
    signal_names = [s["signal"] for s in result["signals"]]
    assert "Real-time / Streaming" in signal_names
    # Should have event-analytics as a candidate
    candidate_ids = [c["id"] for c in result["task_flow_candidates"]]
    assert "event-analytics" in candidate_ids


def test_map_signals_batch_keywords():
    """Batch keywords map to batch/scheduled signal."""
    result = sm.map_signals("daily batch ETL pipeline with reports dashboard")
    signal_names = [s["signal"] for s in result["signals"]]
    assert "Batch / Scheduled" in signal_names
    assert result["primary_velocity"] == "batch"


def test_map_signals_ml_keywords():
    """ML keywords trigger machine learning signal."""
    result = sm.map_signals("train models predict forecast classification")
    signal_names = [s["signal"] for s in result["signals"]]
    assert "Machine Learning" in signal_names
    candidate_ids = [c["id"] for c in result["task_flow_candidates"]]
    assert any("machine-learning" in cid or "ml" in cid.lower() for cid in candidate_ids), \
        f"Expected ML-related candidate in {candidate_ids}"


def test_map_signals_sensitive_data_keywords():
    """Sensitive data keywords trigger the compliance signal."""
    result = sm.map_signals("PII HIPAA compliance encryption patient data")
    signal_names = [s["signal"] for s in result["signals"]]
    assert "Sensitive Data" in signal_names


def test_map_signals_medallion_keywords():
    """Data quality / layered keywords trigger medallion signal."""
    result = sm.map_signals("bronze silver gold medallion data quality curated")
    signal_names = [s["signal"] for s in result["signals"]]
    assert "Data Quality / Layered" in signal_names
    candidate_ids = [c["id"] for c in result["task_flow_candidates"]]
    assert "medallion" in candidate_ids


# ── map_signals: ambiguity detection ─────────────────────────────────────


def test_ambiguity_resolved_by_lambda_synthesis():
    """When both Cat 1 (real-time) and Cat 2 (batch) match, lambda synthesis
    fires automatically, adding Cat 3 — so ambiguous is always False."""
    result = sm.map_signals("streaming data and also daily batch ETL reports")
    # Lambda synthesis resolves ambiguity by adding Cat 3
    assert result["ambiguous"] is False
    signal_names = [s["signal"] for s in result["signals"]]
    assert "Both / Mixed (Lambda)" in signal_names


def test_no_ambiguity_with_lambda_keyword():
    """Explicit lambda keyword resolves ambiguity (Cat 3 active)."""
    result = sm.map_signals("lambda architecture with streaming and batch layer")
    assert result["ambiguous"] is False


def test_no_ambiguity_single_velocity():
    """Single velocity signal is never ambiguous."""
    result = sm.map_signals("daily batch ETL pipeline")
    assert result["ambiguous"] is False


# ── map_signals: lambda synthesis ────────────────────────────────────────


def test_lambda_synthesis_when_cat1_and_cat2():
    """Cat 3 (Lambda) is synthesized when both Cat 1 and Cat 2 match."""
    result = sm.map_signals("streaming real-time sensors and also batch ETL reports")
    signal_names = [s["signal"] for s in result["signals"]]
    assert "Both / Mixed (Lambda)" in signal_names, \
        f"Expected lambda synthesis, got: {signal_names}"


# ── map_signals: candidate ranking ───────────────────────────────────────


def test_candidates_sorted_by_score():
    """Task flow candidates are returned sorted by score descending."""
    result = sm.map_signals("streaming kafka IoT sensors batch ETL medallion")
    candidates = result["task_flow_candidates"]
    for i in range(len(candidates) - 1):
        assert candidates[i]["score"] >= candidates[i + 1]["score"], \
            f"Candidates not sorted: {candidates[i]} before {candidates[i + 1]}"


def test_candidates_have_required_fields():
    """Each candidate has id, score, and signals fields."""
    result = sm.map_signals("real-time streaming kafka")
    for c in result["task_flow_candidates"]:
        assert "id" in c
        assert "score" in c
        assert "signals" in c
        assert isinstance(c["score"], int)
        assert isinstance(c["signals"], list)


# ── map_signals: keyword coverage ────────────────────────────────────────


def test_keyword_coverage_range():
    """keyword_coverage is between 0.0 and 1.0."""
    result = sm.map_signals("batch ETL pipeline with some random words mixed in")
    assert 0.0 <= result["keyword_coverage"] <= 1.0


def test_keyword_coverage_zero_for_no_matches():
    """Coverage is 0 when no keywords match."""
    result = sm.map_signals("xyzzy plugh quux")
    assert result["keyword_coverage"] == 0.0


def test_keyword_coverage_higher_with_more_keywords():
    """Text dominated by keywords has higher coverage than mostly unmatched text."""
    sparse = sm.map_signals("the quick brown fox uses batch ETL maybe")
    dense = sm.map_signals("batch ETL daily reports dashboard data warehouse")
    assert dense["keyword_coverage"] >= sparse["keyword_coverage"]


# ── map_signals: overlap avoidance ───────────────────────────────────────


def test_overlap_avoidance():
    """Overlapping keyword matches are prevented (longer phrase wins)."""
    # "real-time" is a keyword; ensure it doesn't double-count with sub-matches
    result = sm.map_signals("real-time scoring")
    all_keywords = []
    for sig in result["signals"]:
        all_keywords.extend(sig["source_keywords"])
    # Should not have both "real-time" and "time" matching overlapping spans
    assert len(all_keywords) == len(set(all_keywords)), \
        f"Duplicate keywords in matches: {all_keywords}"


# ── map_signals: primary velocity ────────────────────────────────────────


def test_primary_velocity_realtime():
    """Strong real-time signal → primary_velocity = 'real-time'."""
    result = sm.map_signals("real-time streaming IoT sensors")
    assert result["primary_velocity"] == "real-time"


def test_primary_velocity_unknown_for_varies_only():
    """Signals with only 'Varies' velocity produce 'unknown' primary_velocity."""
    result = sm.map_signals("PII HIPAA compliance")
    # Sensitive Data has velocity "Varies", so if it's the only match
    # primary_velocity should be "unknown"
    if all(s["velocity"] == "Varies" for s in result["signals"]):
        assert result["primary_velocity"] == "unknown"


# ── _verbose_matches ─────────────────────────────────────────────────────


def test_verbose_matches_returns_details():
    """_verbose_matches returns match details with keyword, category, position."""
    details = sm._verbose_matches("real-time streaming kafka")
    assert len(details) > 0
    for d in details:
        assert "keyword" in d
        assert "category" in d
        assert "position" in d
        assert "context" in d


def test_verbose_matches_empty_input():
    """_verbose_matches on empty string returns empty list."""
    assert sm._verbose_matches("") == []


# ── generate_intake ──────────────────────────────────────────────────────


def test_generate_intake_returns_required_keys():
    """generate_intake returns all documented keys."""
    result = sm.map_signals("batch ETL pipeline")
    intake = sm.generate_intake(result, project="test-project")
    for key in ("project", "signals_detected", "follow_up_questions",
                "ambiguity_questions", "confidence_gaps",
                "candidate_tie_questions", "total_questions"):
        assert key in intake, f"Missing intake key: {key}"


def test_generate_intake_project_name():
    """Project name is reflected in output."""
    result = sm.map_signals("batch ETL")
    intake = sm.generate_intake(result, project="my-project")
    assert intake["project"] == "my-project"


def test_generate_intake_default_project():
    """Default project name is 'Unknown'."""
    result = sm.map_signals("batch ETL")
    intake = sm.generate_intake(result)
    assert intake["project"] == "Unknown"


def test_generate_intake_uncovered_dimensions():
    """Dimensions not mentioned in problem text generate follow-up questions."""
    # Batch-only text doesn't mention ML, transactional, app, etc.
    result = sm.map_signals("daily batch ETL pipeline reports")
    intake = sm.generate_intake(result)
    dims_with_questions = [q["dimension"] for q in intake["follow_up_questions"]]
    # ML, transactional, and app backend should be uncovered
    assert "use_case_ml" in dims_with_questions
    assert "use_case_transactional" in dims_with_questions
    assert "use_case_app" in dims_with_questions


def test_generate_intake_ambiguity_questions_with_synthetic_result():
    """Ambiguity questions are generated when ambiguous flag is True."""
    # Since lambda synthesis always resolves ambiguity in map_signals,
    # test with a synthetic result that has ambiguous=True
    fake_result = {
        "signals": [
            {"signal": "Real-time / Streaming", "confidence": "medium",
             "source_keywords": ["streaming"]},
            {"signal": "Batch / Scheduled", "confidence": "medium",
             "source_keywords": ["batch"]},
        ],
        "task_flow_candidates": [
            {"id": "event-analytics", "score": 2, "signals": ["Real-time / Streaming"]},
        ],
        "primary_velocity": "real-time",
        "ambiguous": True,
        "keyword_coverage": 0.5,
    }
    intake = sm.generate_intake(fake_result)
    assert len(intake["ambiguity_questions"]) > 0
    assert intake["ambiguity_questions"][0]["dimension"] == "data_velocity"


def test_generate_intake_no_ambiguity_questions_when_clear():
    """Non-ambiguous result produces no ambiguity questions."""
    result = sm.map_signals("daily batch ETL pipeline")
    assert result["ambiguous"] is False
    intake = sm.generate_intake(result)
    assert intake["ambiguity_questions"] == []


def test_generate_intake_confidence_gaps():
    """Low-confidence signals generate confirmation questions."""
    result = sm.map_signals("batch ETL")
    intake = sm.generate_intake(result)
    # With few keywords, some signals may have low confidence
    for gap in intake["confidence_gaps"]:
        assert "signal" in gap
        assert "question" in gap


def test_generate_intake_total_questions_sum():
    """total_questions equals sum of all question lists."""
    result = sm.map_signals("streaming and batch ETL pipeline PII data")
    intake = sm.generate_intake(result)
    expected = (
        len(intake["follow_up_questions"]) +
        len(intake["ambiguity_questions"]) +
        len(intake["confidence_gaps"]) +
        len(intake["candidate_tie_questions"])
    )
    assert intake["total_questions"] == expected


def test_generate_intake_candidate_tie_questions():
    """Tied candidates generate tie-breaking questions."""
    # Build a synthetic result with two tied candidates
    fake_result = {
        "signals": [
            {"signal": "Batch / Scheduled", "confidence": "low",
             "source_keywords": ["batch"]},
        ],
        "task_flow_candidates": [
            {"id": "flow-a", "score": 5, "signals": ["A"]},
            {"id": "flow-b", "score": 5, "signals": ["B"]},
        ],
        "primary_velocity": "batch",
        "ambiguous": False,
        "keyword_coverage": 0.5,
    }
    intake = sm.generate_intake(fake_result)
    assert len(intake["candidate_tie_questions"]) > 0
    assert "flow-a" in intake["candidate_tie_questions"][0]["question"]
    assert "flow-b" in intake["candidate_tie_questions"][0]["question"]


def test_generate_intake_no_tie_when_clear_winner():
    """No tie-breaking questions when top candidate has a higher score."""
    fake_result = {
        "signals": [],
        "task_flow_candidates": [
            {"id": "flow-a", "score": 10, "signals": ["A"]},
            {"id": "flow-b", "score": 3, "signals": ["B"]},
        ],
        "primary_velocity": "batch",
        "ambiguous": False,
        "keyword_coverage": 0.5,
    }
    intake = sm.generate_intake(fake_result)
    assert intake["candidate_tie_questions"] == []


# ── Output formatting ────────────────────────────────────────────────────


def test_to_yaml_produces_string():
    """_to_yaml returns a non-empty YAML string."""
    result = sm.map_signals("batch ETL pipeline")
    yaml_out = sm._to_yaml(result)
    assert isinstance(yaml_out, str)
    assert "signals:" in yaml_out
    assert "task_flow_candidates:" in yaml_out
    assert "primary_velocity:" in yaml_out


def test_to_json_produces_valid_json():
    """_to_json returns valid JSON."""
    import json
    result = sm.map_signals("batch ETL pipeline")
    json_out = sm._to_json(result)
    parsed = json.loads(json_out)
    assert "signals" in parsed
    assert "task_flow_candidates" in parsed


# ── Integration: realistic problem statements ────────────────────────────


def test_integration_iot_problem():
    """Realistic IoT problem statement maps to streaming + event-analytics."""
    text = (
        "We have thousands of IoT sensors deployed across our manufacturing floor "
        "generating telemetry data every second. We need real-time monitoring, "
        "alerts when machines go out of spec, and a dashboard for shift supervisors."
    )
    result = sm.map_signals(text)
    signal_names = [s["signal"] for s in result["signals"]]
    assert "Real-time / Streaming" in signal_names
    candidate_ids = [c["id"] for c in result["task_flow_candidates"]]
    assert "event-analytics" in candidate_ids
    assert result["primary_velocity"] == "real-time"


def test_integration_data_warehouse_problem():
    """Realistic data warehouse problem maps to batch + medallion."""
    text = (
        "We want to build a central data warehouse consolidating data from "
        "SAP, Salesforce, and our CRM. Nightly batch loads with bronze, silver, "
        "and gold layers. Reports and Power BI dashboards for executives."
    )
    result = sm.map_signals(text)
    signal_names = [s["signal"] for s in result["signals"]]
    assert "Batch / Scheduled" in signal_names
    assert "Data Quality / Layered" in signal_names
    candidate_ids = [c["id"] for c in result["task_flow_candidates"]]
    assert "medallion" in candidate_ids


def test_integration_compliance_problem():
    """Problem with compliance keywords triggers sensitive data signal."""
    text = (
        "Our healthcare platform processes patient records with PHI and PII. "
        "We must comply with HIPAA regulations and need encryption at rest "
        "and data masking for non-privileged users."
    )
    result = sm.map_signals(text)
    signal_names = [s["signal"] for s in result["signals"]]
    assert "Sensitive Data" in signal_names
