def test_register_success(client):
    resp = client.post("/auth/register", json={"email": "new@example.com", "password": "secret"})
    assert resp.status_code == 201
    assert resp.json()["email"] == "new@example.com"


def test_register_duplicate_email(client, registered_user):
    resp = client.post("/auth/register", json={"email": "test@example.com", "password": "other"})
    assert resp.status_code == 400


def test_login_success(client, registered_user):
    resp = client.post("/auth/login", data={"username": "test@example.com", "password": "password123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client, registered_user):
    resp = client.post("/auth/login", data={"username": "test@example.com", "password": "wrong"})
    assert resp.status_code == 401
