from app.services import rules_runner


def rule_ids(csv_text: str) -> set[str]:
    return {rule["rule_id"] for rule in rules_runner.run_rules_from_text(csv_text)}


def find_rule(csv_text: str, rule_id: str):
    for rule in rules_runner.run_rules_from_text(csv_text):
        if rule["rule_id"] == rule_id:
            return rule
    return None


def test_missing_values_trigger_and_clean_and_edge():
    rule = find_rule("id,email\n1,\n2,a@example.com\n", "missing_values")
    assert rule and rule["severity"] == "Critical"
    assert "missing_values" not in rule_ids("id,email\n1,a@example.com\n2,b@example.com\n")
    assert rules_runner.run_rules_from_text("id,email\n") == []


def test_duplicate_rows_trigger_and_clean():
    rule = find_rule("id,name\n1,A\n1,A\n2,B\n", "duplicate_rows")
    assert rule and rule["severity"] == "Critical"
    assert "duplicate_rows" not in rule_ids("id,name\n1,A\n2,B\n")


def test_duplicate_key_trigger_and_clean():
    rule = find_rule("customer_id,name\nC1,A\nC1,B\nC2,C\n", "duplicate_key")
    assert rule and rule["severity"] == "Critical"
    assert "duplicate_key" not in rule_ids("customer_id,name\nC1,A\nC2,B\n")


def test_invalid_type_trigger_and_clean():
    rule = find_rule("amount\n10\n20\n30\n40\n50\n60\n70\n80\nbad\n", "invalid_type")
    assert rule and rule["severity"] in {"Medium", "High", "Critical"}
    assert "invalid_type" not in rule_ids("amount\n10\n20\n30\n")


def test_outlier_trigger_and_clean():
    csv_text = "salary\n" + "\n".join([str(100 + i) for i in range(20)] + ["10000"]) + "\n"
    rule = find_rule(csv_text, "outliers")
    assert rule and rule["affected_count"] == 1
    assert "outliers" not in rule_ids("salary\n100\n105\n110\n115\n")


def test_inconsistent_category_trigger_and_clean():
    rule = find_rule("country\nUnited States\nUnited States\nUS\nUSA\nCanada\nCanada\n", "inconsistent_category")
    assert rule and rule["severity"] in {"Medium", "High"}
    assert "inconsistent_category" not in rule_ids("country\nCanada\nCanada\nMexico\nMexico\n")


def test_date_format_validation_trigger_and_clean():
    rule = find_rule("order_date\n2026-01-01\n01/02/2026\n03/01/2026\n", "date_format_validation")
    assert rule and rule["affected_pct"] == 100.0
    assert "date_format_validation" not in rule_ids("order_date\n2026-01-01\n2026-01-02\n")


def test_numeric_range_trigger_and_clean():
    rule = find_rule("age\n25\n130\n40\n", "numeric_range")
    assert rule and rule["severity"] in {"Low", "Medium", "High"}
    assert "numeric_range" not in rule_ids("age\n25\n30\n40\n")


def test_text_formatting_trigger_and_clean():
    rule = find_rule("status\nActive\nActive\nACTIVE\nactive \n", "text_formatting")
    assert rule and rule["severity"] in {"Low", "Medium"}
    assert "text_formatting" not in rule_ids("status\nActive\nInactive\nActive\n")


def test_freshness_trigger_and_clean_edge():
    rule = find_rule("order_date\n2020-01-01\n2020-01-02\n", "freshness")
    assert rule and rule["severity"] == "High"
    assert rules_runner.run_rules_from_text("order_date\n") == []


def test_referential_integrity_trigger_and_clean():
    rule = find_rule("order_date,ship_date\n2026-01-05,2026-01-01\n2026-01-01,2026-01-03\n", "referential_integrity")
    assert rule and rule["severity"] in {"Medium", "High"}
    assert "referential_integrity" not in rule_ids("order_date,ship_date\n2026-01-01,2026-01-03\n")
