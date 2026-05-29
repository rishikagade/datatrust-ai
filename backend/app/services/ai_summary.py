from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

try:
    from groq import Groq
except ImportError:
    Groq = None


DEFAULT_MODEL = "llama-3.3-70b-versatile"
RAW_VALUE_KEYS = {"sample_values", "raw_values", "row_data", "value", "values", "top_values"}

if load_dotenv is not None:
    PROJECT_ROOT = Path(__file__).resolve().parents[3]
    BACKEND_ROOT = Path(__file__).resolve().parents[2]
    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv(BACKEND_ROOT / ".env", override=False)


def _tier(score: float | int | None) -> str:
    if score is None:
        return "Unknown"
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Needs Review"
    return "High Risk"


def _normalise_scoring(scoring: dict[str, Any]) -> dict[str, Any]:
    normalised = dict(scoring or {})
    score = normalised.get("overall_score")
    normalised["tier"] = normalised.get("tier") or _tier(score)

    if "components" not in normalised:
        components = []
        for key, component in (normalised.get("component_scores") or {}).items():
            penalty = component.get("p_i", 0) or 0
            components.append(
                {
                    "key": key,
                    "name": str(key).replace("_", " ").title(),
                    "component_score": component.get("component_health", max(0, 100 - float(penalty))),
                    "weighted_deduction": component.get("weighted_deduction", 0),
                    "weight": component.get("weight"),
                }
            )
        normalised["components"] = components
    return normalised


def _strip_raw_value_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_raw_value_fields(item)
            for key, item in value.items()
            if key not in RAW_VALUE_KEYS
        }
    if isinstance(value, list):
        return [_strip_raw_value_fields(item) for item in value]
    return value


def sanitize_audit_context(audit_json: dict[str, Any]) -> dict[str, Any]:
    profile_stats = {}
    for column, stats in (audit_json.get("profile_stats") or {}).items():
        numeric_summary = stats.get("numeric_summary") or None
        profile_stats[column] = {
            "name": stats.get("name", column),
            "inferred_type": stats.get("inferred_type"),
            "null_count": stats.get("null_count"),
            "null_pct": stats.get("null_pct"),
            "unique_count": stats.get("unique_count"),
            "numeric_summary": numeric_summary,
            "top_value_count": len(stats.get("top_values") or []),
        }

    sanitized_rules = []
    for rule in audit_json.get("rule_results", []) or []:
        sanitized_rules.append(
            {
                "rule_id": rule.get("rule_id"),
                "rule_name": rule.get("rule_name"),
                "category": rule.get("category"),
                "affected_columns": rule.get("affected_columns", []),
                "affected_count": rule.get("affected_count"),
                "affected_pct": rule.get("affected_pct"),
                "severity": rule.get("severity"),
                "description": rule.get("description"),
                "suggested_fix": rule.get("suggested_fix"),
                "context_hint": rule.get("context_hint") or (rule.get("metadata") or {}).get("context_hint"),
            }
        )

    sanitized = {
        "audit_id": audit_json.get("audit_id"),
        "dataset": audit_json.get("dataset", {}),
        "profile_stats": profile_stats,
        "scoring": _normalise_scoring(audit_json.get("scoring", {})),
        "rule_results": sanitized_rules,
        "metadata": {
            "rules_applied_count": (audit_json.get("metadata") or {}).get("rules_applied_count", 11),
        },
    }
    return _strip_raw_value_fields(sanitized)


def _build_prompt(audit_json: dict[str, Any]) -> str:
    dataset = audit_json.get("dataset", {})
    scoring = audit_json.get("scoring", {})
    rules = audit_json.get("rule_results", [])
    lines = [
        "You are an AI assistant that writes business-readable audit summaries for dataset quality reports.",
        "Use only the provided structured aggregate audit data. Never invent sample rows or cell values.",
        "Return valid JSON with exactly these keys: executive_summary, risk_interpretation, cleaning_recommendations, dashboard_impact.",
        f"Dataset filename: {dataset.get('filename', 'unknown')}",
        f"Rows: {dataset.get('row_count', 'unknown')}",
        f"Columns: {dataset.get('column_count', 'unknown')}",
        f"Quality score: {scoring.get('overall_score', 'unknown')}/100",
        "Issues detected:",
    ]
    for rule in rules:
        columns = ", ".join(rule.get("affected_columns") or [])
        lines.append(
            f"- {rule.get('rule_name')} | severity={rule.get('severity')} | columns={columns} | "
            f"rows={rule.get('affected_count')} | pct={rule.get('affected_pct')} | fix={rule.get('suggested_fix')}"
        )
    return "\n".join(lines)


def _build_local_summary(audit_json: dict[str, Any], model: str) -> dict[str, Any]:
    score = audit_json.get("scoring", {}).get("overall_score", "unknown")
    rules = audit_json.get("rule_results", [])
    critical = [r for r in rules if r.get("severity") == "Critical"]
    high = [r for r in rules if r.get("severity") == "High"]
    top_columns = sorted({col for rule in rules[:5] for col in rule.get("affected_columns", [])})

    executive_summary = (
        f"This dataset scored {score}/100 with {len(rules)} detected issue(s), "
        f"including {len(critical)} critical and {len(high)} high-severity finding(s)."
    )
    if top_columns:
        executive_summary += f" The most visible affected columns include {', '.join(top_columns[:5])}."

    recommendations = []
    for rule in rules[:6]:
        fix = rule.get("suggested_fix")
        if fix and fix not in recommendations:
            recommendations.append(fix)
    if not recommendations:
        recommendations.append("Continue monitoring this dataset with the same deterministic rules.")

    return {
        "executive_summary": executive_summary,
        "risk_interpretation": "Prioritize critical and high-severity findings because they can distort KPIs, joins, filters, and downstream models.",
        "cleaning_recommendations": " ".join(recommendations),
        "dashboard_impact": "Resolving these findings improves dashboard trust, metric consistency, and model feature reliability.",
        "generated_at": audit_json.get("dataset", {}).get("uploaded_at"),
        "model": model,
        "source": "local",
        "warning": "GROQ_API_KEY is not configured; using local summary fallback.",
    }


def generate_ai_report(audit_json: dict[str, Any], model: str = DEFAULT_MODEL) -> dict[str, Any]:
    sanitized = sanitize_audit_context(audit_json)
    prompt = _build_prompt(sanitized)
    api_key = os.getenv("GROQ_API_KEY")
    if Groq is None or not api_key:
        return _build_local_summary(sanitized, model)

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=os.environ.get("GROQ_MODEL", model),
            messages=[
                {"role": "system", "content": "You write concise business-facing data quality reports from aggregate audit statistics only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=700,
        )
        raw = response.choices[0].message.content.strip()
        parsed = json.loads(raw[raw.find("{") : raw.rfind("}") + 1] if "{" in raw and "}" in raw else raw)
        return {
            "executive_summary": parsed.get("executive_summary", ""),
            "risk_interpretation": parsed.get("risk_interpretation", ""),
            "cleaning_recommendations": parsed.get("cleaning_recommendations", ""),
            "dashboard_impact": parsed.get("dashboard_impact", ""),
            "generated_at": audit_json.get("dataset", {}).get("uploaded_at"),
            "model": os.environ.get("GROQ_MODEL", model),
            "source": "groq",
        }
    except Exception:
        return _build_local_summary(sanitized, model)
