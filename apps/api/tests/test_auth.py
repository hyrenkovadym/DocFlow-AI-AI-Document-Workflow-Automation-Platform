def test_register_login_and_me(client):
    register = client.post(
        "/api/auth/register",
        json={
            "email": "john@example.com",
            "full_name": "John Doe",
            "password": "StrongPass123!",
        },
    )
    assert register.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={"email": "john@example.com", "password": "StrongPass123!"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "john@example.com"
