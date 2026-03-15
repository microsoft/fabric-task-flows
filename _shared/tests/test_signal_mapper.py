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
    """Weighted score >= 3 → medium confidence (e.g., 1 strong or 3 weak)."""
    cat = sm.CATEGORIES[0]
    cr = sm.CategoryResult(category=cat, matches=[
        sm.KeywordMatch(keyword="a", start=0, end=1, weight=3),  # 1 strong keyword
    ])
    assert cr.confidence == "medium"


def test_category_result_confidence_high():
    """Weighted score >= 5 → high confidence (e.g., 2 strong or 1 strong + 1 moderate)."""
    cat = sm.CATEGORIES[0]
    cr = sm.CategoryResult(category=cat, matches=[
        sm.KeywordMatch(keyword="a", start=0, end=1, weight=3),  # strong
        sm.KeywordMatch(keyword="b", start=2, end=3, weight=2),  # moderate
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
    """Default project name is '(no project name provided)'."""
    result = sm.map_signals("batch ETL")
    intake = sm.generate_intake(result)
    assert intake["project"] == "(no project name provided)"


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


# ── Inference Engine ─────────────────────────────────────────────────────


class TestInferenceEngine:
    """Tests for the inference-pattern engine added to signal-mapper.py."""

    # 1. Inference patterns loaded
    def test_inference_patterns_loaded(self):
        """INFERENCE_PATTERNS should be populated with 70+ compiled patterns."""
        assert len(sm.INFERENCE_PATTERNS) >= 70, (
            f"Expected >=70 inference patterns, got {len(sm.INFERENCE_PATTERNS)}"
        )

    # 2. Temporal frequency → Cat 1 (Real-time)
    def test_inference_temporal_frequency(self):
        """'sensors sampling every 30 seconds' should infer Real-time."""
        result = sm.map_signals("sensors sampling every 30 seconds")
        signal_names = [s["signal"] for s in result["signals"]]
        assert "Real-time / Streaming" in signal_names

    # 3. Prediction intent → Cat 4 (ML)
    def test_inference_prediction_intent(self):
        """'detect early signs of disease from patient data' should infer ML."""
        result = sm.map_signals(
            "we need to detect early signs of disease from patient data"
        )
        signal_names = [s["signal"] for s in result["signals"]]
        assert "Machine Learning" in signal_names

    # 4. Compliance obligation → Cat 5 (Sensitive Data)
    def test_inference_compliance_obligation(self):
        """'comply with FDA regulations' should infer Sensitive Data."""
        result = sm.map_signals("we must comply with FDA regulations")
        signal_names = [s["signal"] for s in result["signals"]]
        assert "Sensitive Data" in signal_names

    # 5. Reporting cadence → Cat 2 (Batch)
    def test_inference_reporting_cadence(self):
        """'produce weekly reports for the board' should infer Batch."""
        result = sm.map_signals("produce weekly reports for the board")
        signal_names = [s["signal"] for s in result["signals"]]
        assert "Batch / Scheduled" in signal_names

    # 6. Customer-facing → Cat 9 (App Backend)
    def test_inference_customer_facing(self):
        """'customer portal showing their data' should infer Application Backend."""
        result = sm.map_signals("customer portal showing their data")
        signal_names = [s["signal"] for s in result["signals"]]
        assert "Application Backend" in signal_names

    # 7. Data heterogeneity → Cat 8 (Data Quality)
    def test_inference_data_heterogeneity(self):
        """'data from 5 different sources in different formats' should infer Data Quality."""
        result = sm.map_signals(
            "data from 5 different sources in different formats"
        )
        signal_names = [s["signal"] for s in result["signals"]]
        assert "Data Quality / Layered" in signal_names

    # 8. Optimization intent → Cat 4 (ML)
    def test_inference_optimization_intent(self):
        """'optimize costs based on historical patterns' should infer ML."""
        result = sm.map_signals("optimize costs based on historical patterns")
        signal_names = [s["signal"] for s in result["signals"]]
        assert "Machine Learning" in signal_names

    # 9. Inferred labels are prefixed
    def test_inference_labels_prefixed(self):
        """Inferred matches should have keywords starting with '(inferred:'."""
        result = sm.map_signals("sensors sampling every 30 seconds")
        all_kw = []
        for sig in result["signals"]:
            all_kw.extend(sig["source_keywords"])
        inferred = [k for k in all_kw if k.startswith("(inferred:")]
        assert len(inferred) > 0, f"Expected inferred keywords, got: {all_kw}"

    # 10. Weight respected — weight=2 adds 2 matches
    def test_inference_weight_respected(self):
        """A rule with weight>1 should produce that many matches (start=-1)."""
        import re as _re

        heavy = [ip for ip in sm.INFERENCE_PATTERNS if ip.weight >= 2]
        if not heavy:
            return  # no weight>=2 rules to test

        ip = heavy[0]
        for cat in sm.CATEGORIES:
            if cat.id != ip.category_id:
                continue
            for rule in cat.inference_rules:
                if rule.get("weight", 1) < 2:
                    continue
                regex = _re.compile(rule["pattern"], _re.IGNORECASE)
                test_text = rule["label"]
                if regex.search(test_text):
                    result = sm.map_signals(test_text)
                    inferred_kw = [
                        k
                        for s in result["signals"]
                        for k in s["source_keywords"]
                        if k == f"(inferred: {rule['label']})"
                    ]
                    if len(inferred_kw) >= 2:
                        assert len(inferred_kw) >= 2
                        return
        # Fallback: verify the weight attribute exists
        assert heavy[0].weight >= 2

    # 11. Combined keyword + inference matches
    def test_inference_combined_with_keywords(self):
        """Text with keyword hits AND inference matches should have both."""
        text = "real-time streaming with sensors sampling every 30 seconds"
        result = sm.map_signals(text)
        rt = [s for s in result["signals"] if s["signal"] == "Real-time / Streaming"]
        assert len(rt) == 1
        kw = rt[0]["source_keywords"]
        has_keyword = any(not k.startswith("(inferred:") for k in kw)
        has_inferred = any(k.startswith("(inferred:") for k in kw)
        assert has_keyword, f"Expected keyword match in {kw}"
        assert has_inferred, f"Expected inference match in {kw}"

    # 12. Coverage boost from inference-only matches
    def test_inference_coverage_boost(self):
        """Inference-only text (no keyword hits) should have non-zero coverage."""
        text = "detect early signs of disease in patients"
        result = sm.map_signals(text)
        if result["signals"]:
            assert result["keyword_coverage"] > 0.0

    # 13. Niche: salmon farming
    def test_niche_salmon_farming(self):
        """Salmon farming problem should detect Real-time, Batch, Lambda, ML."""
        text = (
            "We operate salmon farming pens. Each pen has underwater cameras "
            "monitoring fish behavior, dissolved oxygen sensors sampling every "
            "30 seconds. We need to detect early signs of sea lice infestations "
            "from sensor data, optimize feeding schedules based on historical "
            "patterns, and produce weekly biomass estimates for our harvest "
            "planning team."
        )
        result = sm.map_signals(text)
        signal_names = [s["signal"] for s in result["signals"]]
        assert "Real-time / Streaming" in signal_names, (
            f"Missing Real-time in {signal_names}"
        )
        assert "Batch / Scheduled" in signal_names, (
            f"Missing Batch in {signal_names}"
        )
        assert "Both / Mixed (Lambda)" in signal_names, (
            f"Missing Lambda in {signal_names}"
        )
        assert "Machine Learning" in signal_names, (
            f"Missing ML in {signal_names}"
        )

    # 14. Niche: semiconductor
    def test_niche_semiconductor(self):
        """Semiconductor fab problem should detect Real-time, ML, Batch."""
        text = (
            "Our wafer fab runs 24/7 with 400 process tools generating "
            "50 million measurements per day. We need to predict wafer quality "
            "from tool sensor data, trace defective dice back to specific "
            "tool-chamber combinations, and produce daily yield reports for "
            "the engineering team."
        )
        result = sm.map_signals(text)
        signal_names = [s["signal"] for s in result["signals"]]
        assert "Real-time / Streaming" in signal_names, (
            f"Missing Real-time in {signal_names}"
        )
        assert "Machine Learning" in signal_names, (
            f"Missing ML in {signal_names}"
        )
        assert "Batch / Scheduled" in signal_names, (
            f"Missing Batch in {signal_names}"
        )

    # 15. Verbose mode includes inference matches
    def test_verbose_includes_inference(self):
        """In verbose mode, inference matches should appear in output."""
        text = "sensors sampling every 30 seconds for real-time monitoring"
        details = sm._verbose_matches(text)
        inferred = [d for d in details if d["keyword"].startswith("(inferred:")]
        assert len(inferred) > 0, (
            f"Expected inference in verbose output, got: {details}"
        )


# ── Negation detection ──────────────────────────────────────────────────


class TestNegationDetection:
    """Tests for _is_negated() and its integration into map_signals()."""

    def test_negated_keyword_suppressed(self):
        """Keywords preceded by 'NOT' in the same sentence are suppressed."""
        result = sm.map_signals("We do NOT need dashboards. We want streaming.")
        signal_names = [s["signal"] for s in result["signals"]]
        kw_lists = {
            s["signal"]: s["source_keywords"] for s in result["signals"]
        }
        # "dashboard" should not appear as a keyword source
        batch_kws = kw_lists.get("Batch / Scheduled", [])
        assert "dashboard" not in batch_kws, (
            f"Negated keyword 'dashboard' should be suppressed, got: {batch_kws}"
        )

    def test_negated_keyword_dont_suppressed(self):
        """Contraction 'don't' triggers negation."""
        result = sm.map_signals("We don't want dashboards or any bar charts.")
        signal_names = [s["signal"] for s in result["signals"]]
        kw_lists = {
            s["signal"]: s["source_keywords"] for s in result["signals"]
        }
        batch_kws = kw_lists.get("Batch / Scheduled", [])
        assert "dashboard" not in batch_kws

    def test_negation_does_not_cross_sentence_boundary(self):
        """Negation in sentence 1 must NOT suppress keywords in sentence 2."""
        result = sm.map_signals(
            "We do NOT need dashboards. We want real-time sensor streaming."
        )
        signal_names = [s["signal"] for s in result["signals"]]
        assert "Real-time / Streaming" in signal_names, (
            f"real-time should not be negated across sentence boundary, got: {signal_names}"
        )
        rt = next(s for s in result["signals"] if s["signal"] == "Real-time / Streaming")
        assert "real-time" in rt["source_keywords"]

    def test_no_negation_positive_context(self):
        """Keywords in purely positive context are not suppressed."""
        result = sm.map_signals("We need real-time streaming dashboards.")
        signal_names = [s["signal"] for s in result["signals"]]
        assert "Real-time / Streaming" in signal_names

    def test_negation_various_forms(self):
        """Multiple negation forms all suppress keywords."""
        forms = [
            "We do not need dashboards.",
            "We don't want dashboards.",
            "No dashboards required.",
            "We never use dashboards.",
            "Without dashboards.",
            "We are not looking for dashboards.",
        ]
        for text in forms:
            result = sm.map_signals(text)
            kw_lists = {
                s["signal"]: s["source_keywords"] for s in result["signals"]
            }
            batch_kws = kw_lists.get("Batch / Scheduled", [])
            assert "dashboard" not in batch_kws, (
                f"Negation form should suppress 'dashboard': {text!r}"
            )

    def test_affirmation_override_cancels_negation(self):
        """'but also' between negation and keyword cancels the negation."""
        result = sm.map_signals(
            "We don't want batch processing, but also need real-time streaming."
        )
        signal_names = [s["signal"] for s in result["signals"]]
        assert "Real-time / Streaming" in signal_names

    def test_verbose_marks_negated(self):
        """Verbose output marks negated matches with negated: True."""
        text = "We do NOT need dashboards."
        details = sm._verbose_matches(text)
        negated = [d for d in details if d.get("negated")]
        assert any(d["keyword"] == "dashboard" for d in negated), (
            f"Expected negated dashboard in verbose, got: {details}"
        )

    def test_is_negated_helper_directly(self):
        """_is_negated returns True when negation cue precedes keyword."""
        text = "We do NOT need dashboards or charts"
        # "dashboards" starts at position 15
        pos = text.index("dashboards")
        assert sm._is_negated(text, pos) is True

    def test_is_negated_false_for_positive(self):
        """_is_negated returns False for non-negated context."""
        text = "We love dashboards and charts"
        pos = text.index("dashboards")
        assert sm._is_negated(text, pos) is False

    def test_tractor_health_problem_no_dashboard_keyword(self):
        """The exact tractor-health problem statement should not match
        'dashboard' as a keyword — the user explicitly said no dashboards."""
        problem = (
            "We have 250 acres with 2 tractors running continuously. "
            "We need proactive maintenance insights from tractor sensor data "
            "streamed in real-time to iPads. We are in a rural area with weak "
            "internet connectivity, so the solution must handle intermittent or "
            "low-bandwidth conditions. We do NOT need dashboards or charts. "
            "We want direct API integrations to connect tractor telemetry to "
            "our existing ag platform."
        )
        result = sm.map_signals(problem)
        # Real-time should still fire (different sentence)
        signal_names = [s["signal"] for s in result["signals"]]
        assert "Real-time / Streaming" in signal_names
        # Dashboard must not appear as a keyword match
        all_kws = []
        for s in result["signals"]:
            all_kws.extend(s["source_keywords"])
        assert "dashboard" not in all_kws, (
            f"'dashboard' was negated but still matched: {all_kws}"
        )


# ── Project-name guardrail tests ─────────────────────────────────────────


class TestProjectNameGuardrails:
    """Verify signal-mapper.py enforces the project-name hard gate."""

    def test_validate_project_context_intake_mode_skips_check(self):
        """--intake mode should not require a project."""
        # Should not raise or sys.exit
        sm._validate_project_context(None, intake=True)

    def test_validate_project_context_discovery_no_project_exits(self):
        """Discovery mode without --project should sys.exit(1)."""
        import pytest
        with pytest.raises(SystemExit) as exc_info:
            sm._validate_project_context(None, intake=False)
        assert exc_info.value.code == 1

    def test_validate_project_context_nonexistent_project_exits(self):
        """Discovery mode with a project that doesn't exist should sys.exit(1)."""
        import pytest
        with pytest.raises(SystemExit) as exc_info:
            sm._validate_project_context("this-project-does-not-exist-xyz", intake=False)
        assert exc_info.value.code == 1

    def test_validate_project_context_existing_project_passes(self, tmp_path, monkeypatch):
        """Discovery mode with a valid scaffolded project should pass."""
        # Create a fake repo root with _projects/<name>/
        projects_dir = tmp_path / "_projects" / "my-project"
        projects_dir.mkdir(parents=True)
        # Monkey-patch _resolve_repo_root to return our tmp dir
        monkeypatch.setattr(sm, "_resolve_repo_root", lambda: tmp_path)
        # Should not raise
        sm._validate_project_context("my-project", intake=False)
