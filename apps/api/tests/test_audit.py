from app.models.enums import UserRole


def test_admin_can_view_audit_logs(client, create_user):
    create_user(email="admin@example.com", password="AdminPass123!", role=UserRole.ADMIN, full_name="Admin")

    login = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "AdminPass123!"},
    )
    token = login.json()["access_token"]

    logs = client.get("/api/audit-logs", headers={"Authorization": f"Bearer {token}"})
    assert logs.status_code == 200
    assert isinstance(logs.json(), list)


def test_user_cannot_view_audit_logs(client):
    client.post(
        "/api/auth/register",
        json={
            "email": "simple@example.com",
            "full_name": "Simple User",
            "password": "SimplePass123!",
        },
    )
    login = client.post(
        "/api/auth/login",
        json={"email": "simple@example.com", "password": "SimplePass123!"},
    )
    token = login.json()["access_token"]

    logs = client.get("/api/audit-logs", headers={"Authorization": f"Bearer {token}"})
    assert logs.status_code == 403
    assert logs.json()["detail"] == "Insufficient permissions"
