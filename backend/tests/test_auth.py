from app.auth import create_access_token, decode_token


def test_create_and_decode_token():
    data = {"sub": "test@test.org", "role": "ops_director", "org_id": 1}
    token = create_access_token(data)
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "test@test.org"
    assert payload["role"] == "ops_director"
    assert payload["type"] == "access"


def test_decode_invalid_token():
    result = decode_token("invalid.token.here")
    assert result is None


def test_login_valid_user(client):
    resp = client.post("/api/v1/auth/login", json={"email": "test@test.org"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "test@test.org"


def test_login_invalid_user(client):
    resp = client.post("/api/v1/auth/login", json={"email": "nobody@example.org"})
    assert resp.status_code == 401


def test_users_list(client, auth_headers):
    resp = client.get("/api/v1/auth/users", headers=auth_headers)
    assert resp.status_code == 200
    users = resp.json()
    assert isinstance(users, list)
    assert len(users) >= 1


def test_protected_endpoint_no_token(client):
    resp = client.get("/api/v1/dashboard/stats")
    assert resp.status_code == 401
