def test_dashboard_stats(client, auth_headers):
    resp = client.get("/api/v1/dashboard/stats", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "active_disasters" in data
    assert "total_warehouses" in data
    assert "pending_requests" in data
    assert "in_transit_shipments" in data
    assert "active_alerts" in data


def test_inventory_warehouses(client, auth_headers):
    resp = client.get("/api/v1/inventory/warehouses", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_inventory_items(client, auth_headers):
    resp = client.get("/api/v1/inventory/items", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_supply_requests_list(client, auth_headers):
    resp = client.get("/api/v1/requests", headers=auth_headers)
    assert resp.status_code == 200


def test_disasters_list(client, auth_headers):
    resp = client.get("/api/v1/disasters", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_alerts_list(client, auth_headers):
    resp = client.get("/api/v1/alerts", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "alerts" in data
    assert isinstance(data["alerts"], list)


def test_shipments_list(client, auth_headers):
    resp = client.get("/api/v1/shipments", headers=auth_headers)
    assert resp.status_code == 200


def test_suppliers_list(client, auth_headers):
    resp = client.get("/api/v1/suppliers", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_coordination_list(client, auth_headers):
    resp = client.get("/api/v1/coordination", headers=auth_headers)
    assert resp.status_code == 200


def test_compliance_check(client, auth_headers):
    resp = client.get("/api/v1/compliance", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "sphere_standards" in data
    assert "overall_score" in data


def test_risk_map(client, auth_headers):
    resp = client.get("/api/v1/risk/map", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "regions" in data


def test_marketplace_list(client, auth_headers):
    resp = client.get("/api/v1/marketplace", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_audit_list(client, auth_headers):
    resp = client.get("/api/v1/audit", headers=auth_headers)
    assert resp.status_code == 200


def test_anomalies_summary(client, auth_headers):
    resp = client.get("/api/v1/anomalies/summary", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "inventory" in data
    assert "shipments" in data


def test_root_returns_ok(client):
    resp = client.get("/")
    assert resp.status_code in (200, 404)


def test_docs_available(client):
    resp = client.get("/docs")
    assert resp.status_code == 200
