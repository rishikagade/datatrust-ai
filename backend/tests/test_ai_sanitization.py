from app.services.ai_summary import sanitize_audit_context


def test_sanitize_audit_context_strips_raw_value_fields():
    audit = {
        "audit_id": "audit-1",
        "dataset": {"filename": "example.csv", "row_count": 2, "column_count": 1},
        "profile_stats": {
            "email": {
                "name": "email",
                "inferred_type": "string",
                "null_count": 0,
                "null_pct": 0,
                "unique_count": 2,
                "top_values": [{"value": "person@example.com", "count": 1}],
                "sample_values": ["person@example.com"],
                "raw_values": ["person@example.com", "other@example.com"],
                "row_data": [{"email": "person@example.com"}],
            }
        },
        "rule_results": [
            {
                "rule_id": "missing_values",
                "rule_name": "Missing Value Check",
                "category": "completeness",
                "affected_columns": ["email"],
                "affected_count": 1,
                "affected_pct": 50,
                "severity": "Critical",
                "description": "Aggregated finding only.",
                "suggested_fix": "Inspect upstream source.",
                "metadata": {
                    "sample_values": ["person@example.com"],
                    "row_data": [{"email": "person@example.com"}],
                },
            }
        ],
        "scoring": {"overall_score": 75},
    }

    sanitized = sanitize_audit_context(audit)
    rendered = str(sanitized)
    for raw_key in ["sample_values", "top_values", "raw_values", "row_data"]:
        assert raw_key not in rendered
    assert "person@example.com" not in rendered
