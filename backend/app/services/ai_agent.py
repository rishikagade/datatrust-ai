from __future__ import annotations

import os
from typing import Any

from .ai_summary import DEFAULT_MODEL, sanitize_audit_context


AGENT_SYSTEM_PROMPT = """
You are a data quality audit assistant embedded in DataTrust AI. You have reviewed
the complete audit report for this dataset and you answer questions about it.

YOUR KNOWLEDGE SOURCE:
You know only what is in the audit context below. Do not invent findings that are
not in the audit. If a user asks about something the audit did not check, say so.

HOW TO ANSWER:
1. Always reference actual values: column names, row counts, percentages, severity
   levels, score components. Never give generic advice that could apply to any dataset.
2. Lead with the most important point first.
3. When asked for priorities, use severity order: Critical then High then Medium then Low.
   Within the same severity, prioritise by affected row count (more rows = higher priority).
4. When explaining business impact, be concrete: say what breaks (joins fail, aggregations
   are wrong, filters split categories, models train on noise) -- not just that data
   quality is important.
5. Keep responses to 4-6 sentences by default. Expand only if the user asks for detail.
6. For fix questions, name the column, describe the operation, and explain why it works.
7. If a finding has a context_hint suggesting the issue may be intentional, mention it.

WHAT YOU CANNOT DO:
- You cannot see the actual data rows -- only aggregate statistics.
- You cannot run code or modify the dataset.
- You cannot answer questions outside this audit's scope. If asked, say:
  "That's outside what this audit measured. Here's what I can tell you from
  the findings: [relevant finding]."

TONE: Direct, specific, practical. You are a senior data analyst talking to a
colleague. Avoid filler phrases -- every sentence should carry specific information.

AUDIT CONTEXT:
{audit_context}
"""


INTENT_INSTRUCTIONS = {
    "prioritization": (
        "The user wants to know what to fix first. Give a numbered list ordered by "
        "severity (Critical first, then High, then Medium). For each item, one sentence "
        "explaining why it is urgent."
    ),
    "score_explanation": (
        "Walk through the score breakdown component by component, starting with the "
        "largest weighted deductions. End with the single change that would have the "
        "biggest positive impact on the score."
    ),
    "business_impact": (
        "Name specific operations that would break: JOIN fan-out on a non-unique key, "
        "GROUP BY splitting category variants, ORDER BY failing on mixed date formats. "
        "Connect each issue directly to a consequence."
    ),
    "remediation": (
        "Give a specific step-by-step answer naming the column and operation. "
        "If a context_hint suggests the issue may be intentional, mention it."
    ),
    "explanation": (
        "Define the concept clearly in one sentence, then apply it to this dataset's "
        "actual findings with specific numbers."
    ),
    "column_detail": (
        "Summarise all findings for the column: completeness, rule violations, "
        "severity levels, and suggested fixes. If no issues, say so."
    ),
    "general": (
        "Reference actual column names, row counts, and percentages from the audit."
    ),
}


SEVERITY_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
TOTAL_RULES_RUN = 11


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


def _primary_column(finding: dict[str, Any]) -> str:
    columns = finding.get("affected_columns") or []
    return str(columns[0]) if columns else "unknown"


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _scoring_components(scoring: dict[str, Any]) -> list[dict[str, Any]]:
    components = scoring.get("components")
    if isinstance(components, list):
        return components

    component_scores = scoring.get("component_scores") or {}
    normalized: list[dict[str, Any]] = []
    for key, value in component_scores.items():
        label = str(key).replace("_", " ").title()
        normalized.append(
            {
                "key": key,
                "name": label,
                "component_score": value.get("component_health", max(0.0, 100.0 - _as_float(value.get("p_i")))),
                "weighted_deduction": value.get("weighted_deduction", 0),
                "weight": value.get("weight"),
            }
        )
    return normalized


def _sorted_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        findings,
        key=lambda r: (
            SEVERITY_ORDER.get(str(r.get("severity", "Low")), 3),
            -_as_float(r.get("affected_count")),
        ),
    )


def _find_column_in_message(message: str, findings: list[dict[str, Any]], profiles: dict[str, Any] | None = None) -> str | None:
    msg = message.lower()
    all_cols = set(profiles or {})
    for finding in findings:
        all_cols.update(finding.get("affected_columns") or [])
    for col in sorted(all_cols, key=len, reverse=True):
        if str(col).lower() in msg:
            return str(col)
    return None


def _column_answer(column: str, findings: list[dict[str, Any]], profiles: dict[str, Any] | None = None) -> str:
    profile = (profiles or {}).get(column, {})
    col_findings = [f for f in findings if column in (f.get("affected_columns") or [])]
    completeness = 100.0 - _as_float(profile.get("null_pct"))
    lines = [f"Findings for column '{column}':"]
    if profile:
        lines.append(
            f"  Profile: inferred type={profile.get('inferred_type', 'unknown')}, "
            f"completeness={completeness:.1f}%, nulls={profile.get('null_count', 0)}, "
            f"unique values={profile.get('unique_count', 0)}."
        )
    if col_findings:
        for finding in _sorted_findings(col_findings):
            lines.append(f"  [{finding.get('severity', 'Low')}] {finding.get('rule_name', 'Rule finding')}: {finding.get('description', '')}")
            lines.append(f"  Fix: {finding.get('suggested_fix', 'Review and clean this column before using it downstream.')}")
            if finding.get("context_hint"):
                lines.append(f"  Note: {finding['context_hint']}")
    else:
        lines.append("  No rule violations were detected for this column.")
    return "\n".join(lines)


def rule_based_fallback(user_message: str, sanitized_audit: dict[str, Any]) -> str:
    """
    Produce a specific, data-grounded answer from the audit JSON without calling a model.
    Used when GROQ_API_KEY is not set or when Groq is unreachable.
    """
    msg = user_message.lower()
    findings = sanitized_audit.get("rule_results", []) or []
    scoring = sanitized_audit.get("scoring", {}) or {}
    meta = sanitized_audit.get("dataset", {}) or {}
    profiles = sanitized_audit.get("profile_stats", {}) or {}
    sorted_findings = _sorted_findings(findings)

    score = scoring.get("overall_score", 0)
    tier = scoring.get("tier") or _tier(score)
    filename = meta.get("filename", "your dataset")
    matching_col = _find_column_in_message(user_message, findings, profiles)

    if not findings:
        total_rules_run = (sanitized_audit.get("metadata") or {}).get("rules_applied_count", TOTAL_RULES_RUN)
        return (
            f"{filename} passed all {total_rules_run} validation checks "
            f"and scored {score}/100 ({tier}). No data quality issues were detected. "
            f"You can ask me about the column profiles, the scoring methodology, "
            f"or what the individual checks look for."
        )

    if matching_col:
        return _column_answer(matching_col, findings, profiles)

    if "duplicate key" in msg:
        duplicate_key = [f for f in sorted_findings if "duplicate" in str(f.get("rule_name", "")).lower() and "key" in str(f.get("rule_name", "")).lower()]
        if duplicate_key:
            finding = duplicate_key[0]
            col = _primary_column(finding)
            return (
                f"A duplicate key means an identifier that should uniquely identify one record appears more than once. "
                f"In {filename}, '{col}' has a {finding.get('severity')} duplicate-key finding affecting "
                f"{_as_float(finding.get('affected_count')):,.0f} rows ({_as_float(finding.get('affected_pct')):.1f}%). "
                f"This can create JOIN fan-out, duplicated customer or employee records, and inflated dashboard counts. "
                f"{finding.get('suggested_fix')}"
            )
        return f"No duplicate-key findings were detected in {filename}."

    if any(w in msg for w in ["fix first", "priorit", "start", "most important", "urgent", "worst"]):
        if not sorted_findings:
            return f"{filename} has no detected issues. The dataset scored {score}/100 ({tier})."
        lines = [f"Based on the audit of {filename} (score: {score}/100), fix these issues in order:"]
        for index, finding in enumerate(sorted_findings[:5], 1):
            col = _primary_column(finding)
            lines.append(
                f"{index}. [{finding.get('severity')}] {finding.get('rule_name')} on '{col}' -- "
                f"{_as_float(finding.get('affected_count')):,.0f} rows ({_as_float(finding.get('affected_pct')):.1f}%) affected. "
                f"{finding.get('suggested_fix')}"
            )
        return "\n".join(lines)

    if any(w in msg for w in ["score", "why low", "calculated", "points", "deduct"]):
        components = _scoring_components(scoring)
        worst = sorted(components, key=lambda c: _as_float(c.get("weighted_deduction")), reverse=True)[:3]
        lines = [f"The dataset scored {score}/100 ({tier}). The biggest score deductions are:"]
        for component in worst:
            if _as_float(component.get("weighted_deduction")) > 0:
                lines.append(
                    f"  * {component.get('name')}: -{_as_float(component.get('weighted_deduction')):.1f} points "
                    f"(component health: {_as_float(component.get('component_score')):.1f}/100)"
                )
        if sorted_findings:
            top = sorted_findings[0]
            col = _primary_column(top)
            lines.append(
                f"The highest priority issue is a {top.get('severity')}-severity finding "
                f"on '{col}' ({_as_float(top.get('affected_count')):,.0f} rows affected). "
                f"Fixing this would have the largest positive impact on the score."
            )
        return "\n".join(lines)

    if any(w in msg for w in ["dashboard", "report", "impact", "affect", "break", "wrong"]):
        critical_high = [f for f in sorted_findings if f.get("severity") in ("Critical", "High")]
        if not critical_high:
            return (
                f"{filename} has no Critical or High severity issues. "
                f"The Medium and Low findings are unlikely to cause major dashboard problems, "
                f"but reviewing them before production use is still recommended."
            )
        lines = [f"Using {filename} (score: {score}/100) without cleaning could cause:"]
        for finding in critical_high[:3]:
            col = _primary_column(finding)
            rule_name = str(finding.get("rule_name", "")).lower()
            if "duplicate" in rule_name and "key" in rule_name:
                lines.append(
                    f"  * JOIN fan-out on '{col}': any table joined on this column "
                    f"will produce inflated row counts and incorrect aggregations."
                )
            elif "missing" in rule_name:
                lines.append(
                    f"  * Silent nulls in '{col}': {_as_float(finding.get('affected_pct')):.1f}% of rows "
                    f"will be excluded from aggregations or produce null KPIs."
                )
            elif "duplicate row" in rule_name:
                lines.append(
                    f"  * Inflated counts: {_as_float(finding.get('affected_count')):,.0f} duplicate rows "
                    f"will double-count every metric."
                )
            elif "type" in rule_name:
                lines.append(
                    f"  * Type errors in '{col}': {_as_float(finding.get('affected_count')):,.0f} values "
                    f"cannot be used in numeric calculations."
                )
            else:
                lines.append(
                    f"  * [{finding.get('severity')}] {finding.get('rule_name')} on '{col}': {finding.get('description', '')}"
                )
        return "\n".join(lines)

    if any(w in msg for w in ["column", "field", "variable"]):
        affected = sorted({col for finding in findings for col in (finding.get("affected_columns") or [])})[:8]
        if affected:
            return (
                f"Columns with detected issues: {', '.join(affected)}. "
                f"Ask about a specific column for details."
            )
        return f"No columns in {filename} have detected rule violations."

    if any(w in msg for w in ["mean", "explain", "what is", "what does", "understand", "why"]):
        if sorted_findings:
            top = sorted_findings[0]
            col = _primary_column(top)
            return (
                f"The most important finding is [{top.get('severity')}] {top.get('rule_name')} on '{col}'. "
                f"It affects {_as_float(top.get('affected_count')):,.0f} rows ({_as_float(top.get('affected_pct')):.1f}%) in {filename}. "
                f"{top.get('description', '')} {top.get('suggested_fix', '')}"
            )

    if sorted_findings:
        top = sorted_findings[0]
        col = _primary_column(top)
        return (
            f"{filename} scored {score}/100 ({tier}). "
            f"The most urgent finding is a {top.get('severity')}-severity issue: "
            f"{top.get('rule_name')} on '{col}' affecting {_as_float(top.get('affected_count')):,.0f} rows "
            f"({_as_float(top.get('affected_pct')):.1f}%). {top.get('suggested_fix')} "
            f"Ask me about specific columns, what to fix first, or how this affects your dashboards."
        )

    return (
        f"{filename} scored {score}/100 ({tier}) with no rule violations detected. "
        f"The dataset appears clean across all checked categories."
    )


def format_audit_context_for_agent(sanitized_audit: dict[str, Any]) -> str:
    meta = sanitized_audit.get("dataset", {}) or {}
    scoring = sanitized_audit.get("scoring", {}) or {}
    findings = sanitized_audit.get("rule_results", []) or []
    profiles = sanitized_audit.get("profile_stats", {}) or {}
    sorted_findings = _sorted_findings(findings)

    lines: list[str] = []
    lines.append("=== DATASET OVERVIEW ===")
    lines.append(f"Filename: {meta.get('filename', 'unknown')}")
    lines.append(f"Rows: {int(meta.get('row_count') or 0):,}")
    lines.append(f"Columns: {meta.get('column_count', 0)}")
    lines.append(
        f"Quality Score: {scoring.get('overall_score', 0)}/100 "
        f"({scoring.get('tier') or _tier(scoring.get('overall_score'))})"
    )
    lines.append("")

    lines.append("=== SCORE BREAKDOWN ===")
    for component in _scoring_components(scoring):
        lines.append(
            f"{component.get('name')}: {_as_float(component.get('component_score')):.1f}/100 "
            f"(weighted deduction: -{_as_float(component.get('weighted_deduction')):.1f} pts)"
        )
    lines.append("")

    lines.append("=== AUDIT FINDINGS ===")
    for finding in sorted_findings:
        col = _primary_column(finding)
        lines.append(
            f"[{finding.get('severity', '?')}] {finding.get('rule_name', '?')} "
            f"| Column: {col} "
            f"| {_as_float(finding.get('affected_count')):,.0f} rows affected "
            f"({_as_float(finding.get('affected_pct')):.1f}%)"
        )
        lines.append(f"  Finding: {finding.get('description', '')}")
        lines.append(f"  Fix: {finding.get('suggested_fix', '')}")
        if finding.get("context_hint"):
            lines.append(f"  Note: {finding['context_hint']}")
    lines.append("")

    lines.append("=== COLUMN SUMMARY (most affected) ===")
    col_issue_counts: dict[str, int] = {}
    col_worst_severity: dict[str, str] = {}
    for finding in sorted_findings:
        for col in finding.get("affected_columns") or []:
            col_issue_counts[col] = col_issue_counts.get(col, 0) + 1
            current_worst = col_worst_severity.get(col, "Low")
            if SEVERITY_ORDER.get(str(finding.get("severity", "Low")), 3) < SEVERITY_ORDER.get(current_worst, 3):
                col_worst_severity[col] = str(finding.get("severity", "Low"))

    top_cols = sorted(col_issue_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    for col_name, issue_count in top_cols:
        profile = profiles.get(col_name, {})
        null_pct = _as_float(profile.get("null_pct"))
        inferred_type = profile.get("inferred_type", "unknown")
        worst_sev = col_worst_severity.get(col_name, "Low")
        lines.append(
            f"  {col_name} ({inferred_type}): {issue_count} issue(s), "
            f"worst severity={worst_sev}, completeness={(100 - null_pct):.0f}%"
        )

    return "\n".join(lines)


def detect_intent(user_message: str) -> str:
    msg = user_message.lower()
    if any(w in msg for w in ["fix first", "priorit", "start", "most important", "urgent", "worst"]):
        return "prioritization"
    if any(w in msg for w in ["score", "why low", "calculated", "points", "deduct"]):
        return "score_explanation"
    if any(w in msg for w in ["dashboard", "report", "impact", "affect", "break", "wrong"]):
        return "business_impact"
    if any(w in msg for w in ["fix", "clean", "resolve", "correct", "repair", "handle"]):
        return "remediation"
    if any(w in msg for w in ["mean", "explain", "what is", "what does", "understand", "why"]):
        return "explanation"
    if any(w in msg for w in ["column", "field", "variable"]):
        return "column_detail"
    return "general"


def build_user_message_with_intent(user_message: str) -> str:
    intent = detect_intent(user_message)
    instruction = INTENT_INSTRUCTIONS.get(intent, INTENT_INSTRUCTIONS["general"])
    return f"{user_message}\n\n[Answering guidance: {instruction}]"


def _normalize_history(conversation_history: list[dict[str, Any]], max_items: int) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for item in conversation_history[-max_items:]:
        role = item.get("role", "user")
        if role not in {"user", "assistant"}:
            continue
        content = item.get("content") or item.get("text") or ""
        if content:
            normalized.append({"role": role, "content": str(content)})
    return normalized


def generate_agent_reply(
    sanitized_audit: dict[str, Any],
    user_message: str,
    conversation_history: list[dict[str, Any]] | None = None,
    max_history_turns: int = 10,
) -> tuple[str, str]:
    """
    Returns (reply_text, provider_label).
    provider_label: "groq", "groq_rate_limited", or "local".
    """
    groq_key = os.environ.get("GROQ_API_KEY")

    if groq_key:
        audit_context_text = format_audit_context_for_agent(sanitized_audit)
        system_prompt = AGENT_SYSTEM_PROMPT.format(audit_context=audit_context_text)
        trimmed_history = _normalize_history(conversation_history or [], max_history_turns * 2)
        enhanced_message = build_user_message_with_intent(user_message)
        messages = [
            {"role": "system", "content": system_prompt},
            *trimmed_history,
            {"role": "user", "content": enhanced_message},
        ]

        try:
            from groq import APIConnectionError, Groq, RateLimitError

            client = Groq(api_key=groq_key)
            response = client.chat.completions.create(
                model=os.environ.get("GROQ_MODEL", DEFAULT_MODEL),
                messages=messages,
                max_tokens=600,
                temperature=0.2,
            )
            return response.choices[0].message.content.strip(), "groq"
        except RateLimitError:
            return (
                "The AI agent is temporarily rate-limited on the free tier. "
                "Wait 30 seconds and try again, or refer to the dashboard findings directly.",
                "groq_rate_limited",
            )
        except APIConnectionError:
            return rule_based_fallback(user_message, sanitized_audit), "local"
        except Exception:
            return rule_based_fallback(user_message, sanitized_audit), "local"

    return rule_based_fallback(user_message, sanitized_audit), "local"


def generate_agent_response(
    audit_context: dict[str, Any],
    message: str,
    conversation_history: list[dict[str, Any]] | None = None,
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    sanitized = sanitize_audit_context(audit_context)
    reply, provider = generate_agent_reply(
        sanitized,
        message,
        conversation_history=conversation_history or [],
    )
    return {
        "reply": reply,
        "answer": reply,
        "audit_id": sanitized.get("audit_id"),
        "model": os.environ.get("GROQ_MODEL", model),
        "provider": provider,
        "source": provider,
        "tier": sanitized.get("scoring", {}).get("tier") or _tier(sanitized.get("scoring", {}).get("overall_score")),
    }
