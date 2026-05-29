from __future__ import annotations

from collections import defaultdict
from typing import Any
import re
import warnings

import pandas as pd

from ..rules import implementations


DATE_FORMATS = [
    ("%Y-%m-%d", "YYYY-MM-DD"),
    ("%m/%d/%Y", "MM/DD/YYYY"),
    ("%d/%m/%Y", "DD/MM/YYYY"),
    ("%Y/%m/%d", "YYYY/MM/DD"),
]


def _read_frame(text: str, delimiter: str) -> pd.DataFrame:
    return pd.read_csv(
        pd.io.common.StringIO(text),
        sep=delimiter,
        dtype=object,
        keep_default_na=True,
        na_values=["", "NA", "N/A", "null", "NULL"],
    )


def _non_null_strings(series: pd.Series) -> pd.Series:
    return series.dropna().astype(str).map(str.strip).replace("", pd.NA).dropna()


def _infer_expected_type(series: pd.Series) -> str:
    values = _non_null_strings(series)
    if values.empty:
        return "string"

    lower_values = values.str.lower()
    if lower_values.isin(["true", "false", "0", "1"]).mean() >= 0.90:
        return "boolean"

    numeric = pd.to_numeric(values, errors="coerce")
    numeric_pct = numeric.notna().mean()
    if numeric_pct >= 0.80:
        if (numeric.dropna() % 1 == 0).all():
            return "integer"
        return "float"

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        dates = pd.to_datetime(values, errors="coerce", format="mixed")
    if dates.notna().mean() >= 0.70 and values.str.contains(r"[-/]").mean() >= 0.50:
        return "datetime"

    return "string"


def _count_invalid_type(series: pd.Series, expected_type: str) -> int:
    values = _non_null_strings(series)
    if values.empty:
        return 0

    if expected_type in {"integer", "float"}:
        parsed = pd.to_numeric(values, errors="coerce")
        invalid = parsed.isna()
        if expected_type == "integer":
            invalid = invalid | ((parsed % 1 != 0) & parsed.notna())
        return int(invalid.sum())

    if expected_type == "boolean":
        return int((~values.str.lower().isin(["true", "false", "0", "1"])).sum())

    if expected_type == "datetime":
        parsed = pd.to_datetime(values, errors="coerce", format="mixed")
        return int(parsed.isna().sum())

    return 0


def _numeric_values(series: pd.Series) -> pd.Series:
    values = _non_null_strings(series)
    return pd.to_numeric(values.str.replace(r"[$,]", "", regex=True), errors="coerce").dropna()


def _detect_outliers(series: pd.Series) -> int:
    numeric = _numeric_values(series)
    if len(numeric) < 4:
        return 0
    q1 = numeric.quantile(0.25)
    q3 = numeric.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0:
        return 0
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return int(((numeric < lower) | (numeric > upper)).sum())


def _canonical_category(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", value.strip().lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    synonyms = {
        "us": "united states",
        "u s": "united states",
        "u s a": "united states",
        "usa": "united states",
        "usa.": "united states",
        "america": "united states",
        "united states of america": "united states",
        "fin": "finance",
        "hr": "human resources",
        "eng": "engineering",
        "mkt": "marketing",
        "term": "terminated",
    }
    return synonyms.get(normalized, normalized)


def _detect_inconsistent_categories(df: pd.DataFrame, col: str, row_count: int) -> dict[str, Any] | None:
    values = _non_null_strings(df[col])
    if values.empty:
        return None
    unique_ratio = values.nunique() / max(1, len(values))
    likely_categorical = any(token in col.lower() for token in ["country", "status", "department", "category", "region"])
    if unique_ratio > 0.8 and not likely_categorical:
        return None

    clusters: dict[str, set[str]] = defaultdict(set)
    for value in values.unique():
        clusters[_canonical_category(str(value))].add(str(value))

    variant_clusters = sum(1 for variants in clusters.values() if len(variants) > 1)
    variant_values = sum(len(variants) - 1 for variants in clusters.values() if len(variants) > 1)
    if variant_clusters == 0:
        return None
    return implementations.inconsistent_category_rule(col, variant_clusters, variant_values, row_count)


def _date_patterns(series: pd.Series) -> tuple[set[str], int, list[pd.Timestamp]]:
    values = _non_null_strings(series)
    patterns: set[str] = set()
    unparseable = 0
    parsed_dates: list[pd.Timestamp] = []

    for raw in values:
        value = str(raw).strip()
        matched = False
        parsed = None
        for fmt, label in DATE_FORMATS:
            try:
                parsed = pd.to_datetime(value, format=fmt, errors="raise")
                patterns.add(label)
                matched = True
                break
            except Exception:
                continue
        if not matched:
            parsed = pd.to_datetime(value, errors="coerce", format="mixed")
            if pd.isna(parsed):
                unparseable += 1
                continue
            patterns.add("Other parseable date")
        parsed_dates.append(parsed)

    return patterns, unparseable, parsed_dates


def _is_date_column(col: str, expected_type: str) -> bool:
    name = col.lower()
    return expected_type == "datetime" or any(token in name for token in ["date", "timestamp", "created", "updated"])


def _numeric_range_violations(col: str, series: pd.Series) -> tuple[int, str]:
    numeric = _numeric_values(series)
    if numeric.empty:
        return 0, ""
    name = col.lower()
    checks: list[tuple[pd.Series, str]] = []
    if "age" in name:
        checks.append(((numeric < 0) | (numeric > 120), "age outside 0-120"))
    if any(k in name for k in ["pct", "percent", "rate", "discount"]):
        checks.append(((numeric < 0) | (numeric > 100), "percentage outside 0-100"))
    if any(k in name for k in ["price", "cost", "revenue", "salary", "total", "amount"]):
        checks.append((numeric < 0, "negative values in monetary field"))
    checks.append((numeric.abs() > 1e12, "values above 1e12"))

    violation_mask = pd.Series(False, index=numeric.index)
    descriptions = []
    for mask, description in checks:
        if int(mask.sum()) > 0:
            violation_mask = violation_mask | mask
            descriptions.append(description)
    return int(violation_mask.sum()), "; ".join(descriptions)


def _text_formatting_issues(series: pd.Series) -> int:
    values = series.dropna().astype(str)
    issues = 0
    for value in values:
        if value != value.lstrip() or value != value.rstrip():
            issues += 1
            continue
        stripped = value.strip()
        if len(stripped) > 3 and stripped.isupper() and any(ch.isalpha() for ch in stripped):
            issues += 1
    return issues


def _referential_pairs(columns: list[str]) -> list[tuple[str, str]]:
    lower = {c.lower(): c for c in columns}
    candidates = [
        ("start_date", "end_date"),
        ("order_date", "ship_date"),
        ("hire_date", "termination_date"),
        ("created_date", "updated_date"),
        ("begin_date", "end_date"),
    ]
    pairs: list[tuple[str, str]] = []
    for first, second in candidates:
        if first in lower and second in lower:
            pairs.append((lower[first], lower[second]))
    return pairs


def _count_date_inversions(df: pd.DataFrame, first: str, second: str) -> int:
    left = pd.to_datetime(df[first], errors="coerce", format="mixed")
    right = pd.to_datetime(df[second], errors="coerce", format="mixed")
    valid = left.notna() & right.notna()
    return int((left[valid] > right[valid]).sum())


def run_rules_from_text(text: str, delimiter: str = ",") -> list[dict[str, Any]]:
    df = _read_frame(text, delimiter)
    row_count = int(df.shape[0])
    results: list[dict[str, Any]] = []
    if row_count == 0:
        return results

    duplicate_count = int(df.duplicated(keep=False).sum())
    if duplicate_count > 0:
        results.append(implementations.duplicate_rows_rule(duplicate_count, row_count))

    id_columns = [c for c in df.columns if c.lower() == "id" or c.lower().endswith("_id")]
    for col in id_columns:
        duplicate_key_rows = int(df[col].notna().sum() - df[col].nunique(dropna=True))
        if duplicate_key_rows > 0:
            results.append(implementations.duplicate_key_rule(col, duplicate_key_rows, row_count))

    inferred_types: dict[str, str] = {}
    parsed_date_cache: dict[str, list[pd.Timestamp]] = {}

    for col in df.columns:
        series = df[col]
        null_count = int(series.isna().sum() + (series.astype(str).str.strip() == "").sum())
        if null_count > 0:
            null_pct = (null_count / row_count) * 100
            if col.lower() == "termination_date":
                results.append(
                    implementations.missing_value_rule_with_domain_note(
                        col,
                        null_count,
                        null_pct,
                        row_count,
                        "This column may be intentionally sparse for active employees; validate against status before treating it as a defect.",
                    )
                )
            else:
                results.append(implementations.missing_value_rule(col, null_count, null_pct, row_count))

        expected_type = _infer_expected_type(series)
        inferred_types[col] = expected_type
        invalid_count = _count_invalid_type(series, expected_type)
        if invalid_count > 0:
            invalid_pct = (invalid_count / row_count) * 100
            results.append(implementations.invalid_type_rule(col, invalid_count, invalid_pct, row_count, expected_type))

        if expected_type in {"integer", "float"}:
            outlier_count = _detect_outliers(series)
            if outlier_count > 0:
                results.append(implementations.outlier_rule(col, outlier_count, (outlier_count / row_count) * 100, row_count))

            violations, range_description = _numeric_range_violations(col, series)
            if violations > 0:
                results.append(implementations.numeric_range_rule(col, violations, row_count, range_description))

        category_result = _detect_inconsistent_categories(df, col, row_count)
        if category_result:
            results.append(category_result)

        if _is_date_column(col, expected_type):
            patterns, unparseable, parsed_dates = _date_patterns(series)
            parsed_date_cache[col] = parsed_dates
            if len(patterns) > 1 or unparseable > 0:
                results.append(implementations.date_format_validation_rule(col, len(patterns), unparseable, row_count, sorted(patterns)))

            if parsed_dates:
                max_date = max(parsed_dates)
                days_since = (pd.Timestamp.now(tz=None) - max_date).days
                if days_since >= 30:
                    results.append(implementations.freshness_rule(col, int(days_since), str(max_date.date()), row_count))

        if expected_type == "string" and col not in id_columns:
            values = _non_null_strings(series)
            if not values.empty and values.nunique() / max(1, len(values)) <= 0.8:
                issues = _text_formatting_issues(series)
                if issues > 0:
                    results.append(implementations.text_formatting_rule(col, issues, row_count))

    for first, second in _referential_pairs(list(df.columns)):
        inversions = _count_date_inversions(df, first, second)
        if inversions > 0:
            results.append(implementations.referential_integrity_rule(first, second, inversions, row_count))

    severity_rank = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    return sorted(results, key=lambda rule: (severity_rank.get(rule.get("severity", "Low"), 3), rule.get("rule_name", "")))
