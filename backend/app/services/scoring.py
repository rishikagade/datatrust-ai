from typing import List, Dict, Any

# Component weights (percent)
COMPONENT_WEIGHTS = {
    'missing_value': 25.0,
    'duplicate_rows': 20.0,
    'invalid_type': 20.0,
    'outliers': 10.0,
    'critical_failures': 15.0,
    'business_rule_violations': 10.0,
}

SEVERITY_MULTIPLIER = {
    'Critical': 3.0,
    'High': 2.0,
    'Medium': 1.0,
    'Low': 0.5,
}


def compute_component_penalties(rule_results: List[Dict[str, Any]], profile_stats: Dict[str, Any]) -> Dict[str, float]:
    """Compute p_i penalties (0-100) per component from rule_results and profile_stats."""
    penalties = {k: 0.0 for k in COMPONENT_WEIGHTS.keys()}

    # Missing value: use the worst Missing Value rule so score deductions match visible findings.
    missing_rules = [r for r in rule_results if r.get('rule_id') == 'missing_values']
    if missing_rules:
        penalties['missing_value'] = round(max(float(r.get('affected_pct', 0.0)) for r in missing_rules), 4)

    # Duplicate rows: use duplicate row share and severity multiplier
    dup_rules = [r for r in rule_results if r.get('rule_id') == 'duplicate_rows']
    if dup_rules:
        r = dup_rules[0]
        affected_pct = float(r.get('affected_pct', 0.0))
        severity = r.get('severity', 'Medium')
        penalties['duplicate_rows'] = min(100.0, affected_pct * SEVERITY_MULTIPLIER.get(severity, 1.0))

    # Invalid type penalties: penalize the highest affected_pct among invalid type rules
    invalid_rules = [r for r in rule_results if r.get('rule_id') in {'invalid_type', 'date_format_validation'}]
    if invalid_rules:
        invalid_penalty = 0.0
        for r in invalid_rules:
            affected_pct = float(r.get('affected_pct', 0.0))
            severity = r.get('severity', 'Medium')
            invalid_penalty = max(invalid_penalty, affected_pct * SEVERITY_MULTIPLIER.get(severity, 1.0))
        penalties['invalid_type'] = min(100.0, round(invalid_penalty, 4))

    # Outlier penalties: penalize outlier rate across numeric columns
    outlier_rules = [r for r in rule_results if r.get('rule_id') == 'outliers']
    if outlier_rules:
        outlier_penalty = 0.0
        for r in outlier_rules:
            affected_pct = float(r.get('affected_pct', 0.0))
            severity = r.get('severity', 'Low')
            outlier_penalty = max(outlier_penalty, affected_pct * SEVERITY_MULTIPLIER.get(severity, 1.0))
        penalties['outliers'] = min(100.0, round(outlier_penalty, 4))

    # Business rule violations: aggregate severity-weighted affected_pct for business rule checks
    business_rule_ids = {
        'numeric_range',
        'referential_integrity',
        'inconsistent_category',
        'text_formatting',
        'freshness',
    }
    business_rules = [r for r in rule_results if r.get('category') == 'business_rule' or r.get('rule_id') in business_rule_ids]
    if business_rules:
        business_penalty = 0.0
        for r in business_rules:
            affected_pct = float(r.get('affected_pct', 0.0))
            severity = r.get('severity', 'Medium')
            business_penalty += affected_pct * SEVERITY_MULTIPLIER.get(severity, 1.0)
        penalties['business_rule_violations'] = min(100.0, round(business_penalty, 4))

    # Critical failures: aggregate severity-weighted affected_pct of all Critical rules
    critical_sum = 0.0
    for r in rule_results:
        if r.get('severity') == 'Critical':
            critical_sum += float(r.get('affected_pct', 0.0)) * SEVERITY_MULTIPLIER.get('Critical', 3.0)
    penalties['critical_failures'] = min(70.0, round(critical_sum, 4))

    return penalties


def compute_overall_score(rule_results: List[Dict[str, Any]], profile_stats: Dict[str, Any]) -> Dict[str, Any]:
    if not profile_stats and not rule_results:
        return {
            "overall_score": 0,
            "component_scores": {},
            "component_weights": COMPONENT_WEIGHTS,
            "calculation_detail": {
                "weighted_penalty_sum": 100.0,
                "penalties": {},
                "severity_multiplier": SEVERITY_MULTIPLIER,
            },
        }

    penalties = compute_component_penalties(rule_results, profile_stats)

    # Determine applicable components (non-zero or available)
    applicable = {k: v for k, v in COMPONENT_WEIGHTS.items() if True}

    # Renormalize weights if some components are effectively missing (optional rule)
    total_weight = sum(applicable.values())
    if total_weight <= 0:
        total_weight = 100.0

    # Compute weighted penalty sum (weights in percent, penalties 0-100)
    weighted_penalty_sum = 0.0
    component_scores: Dict[str, Dict[str, float]] = {}
    for comp, orig_w in COMPONENT_WEIGHTS.items():
        # renormalized weight
        w = orig_w / total_weight * 100.0
        p = float(penalties.get(comp, 0.0))
        weighted_penalty_sum += (w * p) / 100.0
        component_scores[comp] = {
            "p_i": p,
            "weight": orig_w,
            "renormalized_weight": round(w, 4),
            "weighted_deduction": round((w * p) / 100.0, 4),
            "component_health": round(max(0.0, 100.0 - p), 4),
        }

    overall = max(0.0, round(100.0 - weighted_penalty_sum, 2))

    return {
        "overall_score": overall,
        "component_scores": component_scores,
        "component_weights": COMPONENT_WEIGHTS,
        "calculation_detail": {
            "weighted_penalty_sum": round(weighted_penalty_sum, 4),
            "penalties": penalties,
            "severity_multiplier": SEVERITY_MULTIPLIER,
        }
    }
