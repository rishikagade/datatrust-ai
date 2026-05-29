from app.services.scoring import compute_overall_score


def test_weighted_formula_consistent():
    rules = [
        {"rule_id": "missing_values", "affected_pct": 20, "severity": "High"},
        {"rule_id": "duplicate_rows", "affected_pct": 10, "severity": "High"},
        {"rule_id": "invalid_type", "affected_pct": 5, "severity": "Medium"},
        {"rule_id": "numeric_range", "affected_pct": 20, "severity": "High"},
    ]
    profile = {"a": {"null_pct": 20}, "b": {"null_pct": 0}}
    score = compute_overall_score(rules, profile)
    expected_deduction = 20 * 0.25 + 20 * 0.20 + 5 * 0.20 + 40 * 0.10
    assert score["calculation_detail"]["weighted_penalty_sum"] == expected_deduction
    assert score["overall_score"] == 100 - expected_deduction


def test_no_issues_scores_100():
    assert compute_overall_score([], {"a": {"null_pct": 0}})["overall_score"] == 100


def test_no_rule_findings_ignore_profile_nulls():
    result = compute_overall_score([], {"crm_queue": {"null_pct": 100}})
    assert result["overall_score"] == 100
    assert result["component_scores"]["missing_value"]["weighted_deduction"] == 0


def test_critical_finding_scores_below_85():
    result = compute_overall_score(
        [{"rule_id": "duplicate_rows", "affected_pct": 30, "severity": "Critical"}],
        {"id": {"null_pct": 0}},
    )
    assert result["overall_score"] < 85


def test_no_business_rules_keeps_weights_normalized():
    result = compute_overall_score([], {"a": {"null_pct": 0}})
    weights = [item["renormalized_weight"] for item in result["component_scores"].values()]
    assert round(sum(weights), 4) == 100


def test_empty_dataset_scores_zero():
    assert compute_overall_score([], {})["overall_score"] == 0


def test_all_null_dataset_with_missing_rule_scores_below_80():
    result = compute_overall_score(
        [{"rule_id": "missing_values", "affected_pct": 100, "severity": "Critical"}],
        {"a": {"null_pct": 100}},
    )
    assert result["overall_score"] < 80


def test_single_row_clean_dataset_scores_100():
    assert compute_overall_score([], {"id": {"null_pct": 0}})["overall_score"] == 100
