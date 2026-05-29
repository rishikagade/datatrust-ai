import json


def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_demo_list_endpoint(client):
    response = client.get('/demo')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(item['name'] == 'customer_master' for item in data)


def test_demo_customer_master_endpoint(client):
    response = client.get('/demo/customer_master')
    assert response.status_code == 200
    data = response.json()
    assert data['metadata']['demo_dataset'] == 'customer_master'
    assert data['ai_report']['executive_summary']
    assert data['dataset']['filename'] == 'customer_master.csv'


def test_demo_invalid_dataset_returns_404(client):
    response = client.get('/demo/does_not_exist')
    assert response.status_code == 404


def test_audit_upload_and_assistant_fallback(client):
    csv_payload = 'id,name\n1,Alice\n2,Bob\n'

    response = client.post(
        '/audit',
        files={'file': ('test.csv', csv_payload, 'text/csv')},
        data={'ai': 'false'},
    )
    assert response.status_code == 200
    audit = response.json()
    assert audit['dataset']['row_count'] == 2
    assert audit['dataset']['column_count'] == 2
    assert audit['ai_report']['executive_summary']

    audit_id = audit['audit_id']
    question_payload = {'question': 'What is the biggest issue?'}
    assistant_response = client.post(f'/audit/{audit_id}/assistant', json=question_payload)

    assert assistant_response.status_code == 200
    assistant = assistant_response.json()
    assert assistant['answer']
    assert assistant['audit_id'] == audit_id


def test_get_audit_by_id_endpoint(client):
    csv_payload = 'id,name\n1,Alice\n2,Bob\n'

    response = client.post(
        '/audit',
        files={'file': ('test.csv', csv_payload, 'text/csv')},
        data={'ai': 'false'},
    )
    assert response.status_code == 200
    audit = response.json()
    audit_id = audit['audit_id']

    audit_response = client.get(f'/audit/{audit_id}')
    assert audit_response.status_code == 200
    audit_data = audit_response.json()
    assert audit_data['audit_id'] == audit_id
    assert audit_data['dataset']['filename'] == 'test.csv'
