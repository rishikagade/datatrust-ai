from typing import Dict, Any, List
from datetime import datetime, timezone


def _severity_for_missing(pct: float) -> str:
    if pct > 35:
        return 'Critical'
    if pct > 15:
        return 'High'
    if pct > 5:
        return 'Medium'
    return 'Low'


def missing_value_rule(column_name: str, null_count: int, null_pct: float, row_count: int) -> Dict[str, Any]:
    affected_count = int(null_count)
    affected_pct = round(null_pct, 4)
    severity = _severity_for_missing(affected_pct)
    rule = {
        'rule_id': 'missing_values',
        'rule_name': 'Missing Value Check',
        'category': 'completeness',
        'affected_columns': [column_name],
        'affected_count': affected_count,
        'affected_pct': affected_pct,
        'severity': severity,
        'description': f"Column '{column_name}' has {affected_pct}% missing values ({affected_count} rows).",
        'suggested_fix': 'Impute or inspect upstream source for missing values.',
        'metadata': {},
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    return rule


def duplicate_rows_rule(duplicate_count: int, row_count: int) -> Dict[str, Any]:
    affected_pct = round((duplicate_count / row_count) * 100, 4) if row_count > 0 else 0.0
    if affected_pct > 5:
        severity = 'Critical'
    elif affected_pct > 2:
        severity = 'High'
    elif affected_pct > 0.5:
        severity = 'Medium'
    else:
        severity = 'Low'

    rule = {
        'rule_id': 'duplicate_rows',
        'rule_name': 'Duplicate Row Check',
        'category': 'uniqueness',
        'affected_columns': [],
        'affected_count': int(duplicate_count),
        'affected_pct': affected_pct,
        'severity': severity,
        'description': f"Found {duplicate_count} exact duplicate rows ({affected_pct}% of dataset).",
        'suggested_fix': 'Deduplicate rows keeping the appropriate occurrence and investigate source pipeline.',
        'metadata': {},
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    return rule


def duplicate_key_rule(column_name: str, non_unique_count: int, row_count: int) -> Dict[str, Any]:
    affected_pct = round((non_unique_count / row_count) * 100, 4) if row_count > 0 else 0.0
    severity = 'Critical' if non_unique_count > 0 else 'Low'
    rule = {
        'rule_id': 'duplicate_key',
        'rule_name': 'Duplicate Key Check',
        'category': 'uniqueness',
        'affected_columns': [column_name],
        'affected_count': int(non_unique_count),
        'affected_pct': affected_pct,
        'severity': severity,
        'description': f"Column '{column_name}' has {non_unique_count} non-unique key values.",
        'suggested_fix': 'Investigate key generation and deduplicate or repair keys at source.',
        'metadata': {},
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    return rule


def _severity_for_invalid_type(pct: float) -> str:
    if pct > 20:
        return 'Critical'
    if pct > 10:
        return 'High'
    if pct > 2:
        return 'Medium'
    return 'Low'


def invalid_type_rule(column_name: str, invalid_count: int, invalid_pct: float, row_count: int, expected_type: str) -> Dict[str, Any]:
    severity = _severity_for_invalid_type(invalid_pct)
    return {
        'rule_id': 'invalid_type',
        'rule_name': 'Invalid Data Type Check',
        'category': 'invalid_type',
        'affected_columns': [column_name],
        'affected_count': int(invalid_count),
        'affected_pct': round(invalid_pct, 4),
        'severity': severity,
        'description': f"Column '{column_name}' has {invalid_pct:.2f}% values that do not match the inferred type '{expected_type}'.",
        'suggested_fix': 'Correct or cleanse invalid values so they conform to the expected column type.',
        'metadata': {'expected_type': expected_type},
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


def _severity_for_outliers(pct: float) -> str:
    if pct > 15:
        return 'High'
    if pct > 5:
        return 'Medium'
    return 'Low'


def outlier_rule(column_name: str, outlier_count: int, outlier_pct: float, row_count: int) -> Dict[str, Any]:
    severity = _severity_for_outliers(outlier_pct)
    return {
        'rule_id': 'outliers',
        'rule_name': 'Outlier Detection Check',
        'category': 'outliers',
        'affected_columns': [column_name],
        'affected_count': int(outlier_count),
        'affected_pct': round(outlier_pct, 4),
        'severity': severity,
        'description': f"Column '{column_name}' has {outlier_pct:.2f}% outlier values ({outlier_count} rows).",
        'suggested_fix': 'Inspect outliers and decide whether to correct, remove, or preserve them based on business context.',
        'metadata': {},
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


def inconsistent_category_rule(column_name: str, variant_clusters: int, variant_values: int, row_count: int, example_cluster: str = None) -> Dict[str, Any]:
    affected_count = int(variant_values)
    affected_pct = round((variant_values / row_count) * 100, 4) if row_count > 0 else 0.0
    # Severity rules
    if variant_clusters > 5 or any(int(x) > 5 for x in [variant_values]):
        severity = 'High'
    elif 3 <= variant_clusters <= 5 or (variant_clusters > 0 and variant_values >= 2):
        severity = 'Medium'
    elif 1 <= variant_clusters <= 2:
        severity = 'Low'
    else:
        severity = 'Low'

    desc = f"Column '{column_name}' has {variant_clusters} variant cluster(s) with {variant_values} non-canonical value(s)."

    return {
        'rule_id': 'inconsistent_category',
        'rule_name': 'Inconsistent Category Check',
        'category': 'consistency',
        'affected_columns': [column_name],
        'affected_count': affected_count,
        'affected_pct': affected_pct,
        'severity': severity,
        'description': desc,
        'suggested_fix': f"Standardise '{column_name}' to one canonical label set before joins, grouping, and dashboard filters.",
        'metadata': {},
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


def date_format_validation_rule(column_name: str, distinct_patterns: int, unparseable_count: int, row_count: int, sample_patterns: list) -> Dict[str, Any]:
    affected_count = int(unparseable_count if unparseable_count > 0 else row_count)
    affected_pct = round((unparseable_count / row_count) * 100, 4) if row_count > 0 else 0.0
    if unparseable_count == 0 and distinct_patterns > 1:
        affected_pct = 100.0

    # Severity
    if distinct_patterns >= 4 or affected_pct > 5:
        severity = 'High'
    elif distinct_patterns == 3 or (0 < affected_pct <= 5):
        severity = 'Medium'
    elif distinct_patterns == 2:
        severity = 'Low'
    else:
        severity = 'Low'

    patterns_str = ', '.join(sample_patterns[:5]) if sample_patterns else ''
    desc = f"Column '{column_name}' contains {distinct_patterns} distinct date format pattern(s). Unparseable values: {unparseable_count}."
    if patterns_str:
        desc += f" Example patterns: {patterns_str}"

    return {
        'rule_id': 'date_format_validation',
        'rule_name': 'Date Format Validation',
        'category': 'conformity',
        'affected_columns': [column_name],
        'affected_count': affected_count,
        'affected_pct': affected_pct,
        'severity': severity,
        'description': desc,
        'suggested_fix': f"Standardise '{column_name}' to ISO 8601 format (YYYY-MM-DD). Found {distinct_patterns} distinct date format patterns.",
        'metadata': {'patterns': sample_patterns},
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


def numeric_range_rule(column_name: str, violation_count: int, row_count: int, range_description: str) -> Dict[str, Any]:
    affected_count = int(violation_count)
    affected_pct = round((violation_count / row_count) * 100, 4) if row_count > 0 else 0.0
    # Severity thresholds
    if violation_count > 10 or affected_pct > 1.0:
        severity = 'High'
    elif 3 <= violation_count <= 10 or (affected_pct > 0 and affected_pct <= 1.0):
        severity = 'Medium'
    elif 1 <= violation_count <= 2:
        severity = 'Low'
    else:
        severity = 'Low'

    desc = f"Column '{column_name}' has {violation_count} value(s) outside expected range ({range_description})."
    return {
        'rule_id': 'numeric_range',
        'rule_name': 'Numeric Range Check',
        'category': 'accuracy',
        'affected_columns': [column_name],
        'affected_count': affected_count,
        'affected_pct': affected_pct,
        'severity': severity,
        'description': desc,
        'suggested_fix': f"Column '{column_name}' has {violation_count} values outside the expected range ({range_description}). Review for data entry errors or unit mismatches.",
        'metadata': {'range_description': range_description},
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


def text_formatting_rule(column_name: str, issue_count: int, row_count: int) -> Dict[str, Any]:
    affected_count = int(issue_count)
    affected_pct = round((issue_count / row_count) * 100, 4) if row_count > 0 else 0.0

    return {
        'rule_id': 'text_formatting',
        'rule_name': 'Text Formatting Check',
        'category': 'conformity',
        'affected_columns': [column_name],
        'affected_count': affected_count,
        'affected_pct': affected_pct,
        'severity': 'Medium' if affected_pct >= 10 else 'Low',
        'description': f"Column '{column_name}' has {issue_count} value(s) with leading/trailing whitespace or ALL CAPS.",
        'suggested_fix': f"Column '{column_name}' has {issue_count} values with formatting issues (leading/trailing whitespace or ALL CAPS). Strip whitespace before joins and standardise case.",
        'metadata': {},
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


def freshness_rule(column_name: str, days_since_most_recent: int, most_recent_date: str, row_count: int) -> Dict[str, Any]:
    # Only report if >=30 days
    affected_count = 1 if days_since_most_recent >= 30 else 0
    affected_pct = round((affected_count / row_count) * 100, 4) if row_count > 0 else 0.0
    if days_since_most_recent > 180:
        severity = 'High'
    elif days_since_most_recent > 60:
        severity = 'Medium'
    elif days_since_most_recent >= 30:
        severity = 'Low'
    else:
        severity = 'Low'

    desc = f"The most recent value in '{column_name}' is {days_since_most_recent} days old ({most_recent_date})."
    return {
        'rule_id': 'freshness',
        'rule_name': 'Freshness Check',
        'category': 'timeliness',
        'affected_columns': [column_name],
        'affected_count': affected_count,
        'affected_pct': affected_pct,
        'severity': severity,
        'description': desc,
        'suggested_fix': f"The most recent value in '{column_name}' is {days_since_most_recent} days old ({most_recent_date}). Confirm this dataset is current before using it for reporting or analysis.",
        'metadata': {'most_recent_date': most_recent_date, 'days_since_most_recent': days_since_most_recent},
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


def referential_integrity_rule(col_a: str, col_b: str, violations: int, row_count: int) -> Dict[str, Any]:
    affected_count = int(violations)
    affected_pct = round((violations / row_count) * 100, 4) if row_count > 0 else 0.0
    if violations > 10 or affected_pct > 0.5:
        severity = 'High'
    elif 3 <= violations <= 10 or affected_pct > 0:
        severity = 'Medium'
    elif 1 <= violations <= 2:
        severity = 'Low'
    else:
        severity = 'Low'

    desc = f"Found {violations} rows where '{col_a}' is after '{col_b}', violating expected chronological relationship."
    return {
        'rule_id': 'referential_integrity',
        'rule_name': 'Referential Integrity Check',
        'category': 'integrity',
        'affected_columns': [col_a, col_b],
        'affected_count': affected_count,
        'affected_pct': affected_pct,
        'severity': severity,
        'description': desc,
        'suggested_fix': f"Found {violations} rows where '{col_a}' is after '{col_b}'. Review for data entry errors or migration artifacts.",
        'metadata': {},
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


def missing_value_rule_with_domain_note(column_name: str, null_count: int, null_pct: float, row_count: int, note: str) -> Dict[str, Any]:
    rule = missing_value_rule(column_name, null_count, null_pct, row_count)
    rule['suggested_fix'] = f"{rule['suggested_fix']} {note}"
    rule['metadata']['domain_note'] = note
    return rule
