from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
    "customer_master": ("customer_master.csv", 55, 65, "duplicate_key"),
    "sales_transactions": ("sales_transactions.csv", 68, 78, "referential_integrity"),
    "hr_employees": ("hr_employees.csv", 62, 72, "duplicate_key"),
}


def test_upload_sample_datasets(client):
    for _, (filename, low, high, expected_rule) in EXPECTED.items():
        payload = (ROOT / "sample_datasets" / filename).read_bytes()
        response = client.post("/audit", files={"file": (filename, payload, "text/csv")})
        assert response.status_code == 200
        audit = response.json()
        assert low <= audit["scoring"]["overall_score"] <= high
        assert expected_rule in {rule["rule_id"] for rule in audit["rule_results"]}


def test_malformed_file_returns_400(client):
    response = client.post("/audit", files={"file": ("bad.csv", b"\x80\x81", "text/csv")})
    assert response.status_code in {400, 500}


def test_empty_file_returns_400(client):
    response = client.post("/audit", files={"file": ("empty.csv", b"", "text/csv")})
    assert response.status_code == 400
    assert "Empty" in response.json()["detail"] or "Failed" in response.json()["detail"]


def test_demo_endpoints_run_live_pipeline(client):
    for name, (_, low, high, _) in EXPECTED.items():
        response = client.get(f"/demo/{name}")
        assert response.status_code == 200
        audit = response.json()
        assert low <= audit["scoring"]["overall_score"] <= high
        assert audit["rule_results"]


def test_demo_nonexistent_returns_404(client):
    assert client.get("/demo/nonexistent").status_code == 404


def test_agent_message_returns_reply(client):
    audit = client.get("/demo/customer_master").json()
    response = client.post(
        "/agent/message",
        json={"message": "Which column should I fix first?", "conversation_history": [], "audit_context": audit},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["reply"]
    assert "customer_id" in body["reply"] or "email" in body["reply"]


def test_report_pdf_endpoint(client):
    audit = client.get("/demo/hr_employees").json()
    response = client.post("/report/pdf", json=audit)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content[:4] == b"%PDF"
