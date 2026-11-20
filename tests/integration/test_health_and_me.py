"""Integration tests for Health check probes and GET /v1/me endpoint."""

from fastapi.testclient import TestClient


def test_health_liveness(client: TestClient):
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert data["service"] == "learningbridge-backend"


def test_health_readiness(client: TestClient):
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"


def test_get_me_without_token_fails(client: TestClient):
    response = client.get("/v1/me")
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "AUTHENTICATION_FAILED"
    assert "request_id" in data


def test_get_me_with_priya_token(client: TestClient, priya_token: str):
    headers = {"Authorization": f"Bearer {priya_token}"}
    response = client.get("/v1/me", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["email"] == "priya.sharma@demo.learningbridge.internal"
    assert data["full_name"] == "Priya Sharma"
    assert data["role"] == "teacher"
    assert data["active_school_name"] == "Oakridge International Academy"
    assert "cls-oak-6a-001" in data["authorized_class_ids"]


def test_login_endpoint_success(client: TestClient):
    login_payload = {
        "email": "priya.sharma@demo.learningbridge.internal",
        "password": "TeacherPass123!",
    }
    response = client.post("/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["user"]["full_name"] == "Priya Sharma"
    assert data["active_school"]["school_name"] == "Oakridge International Academy"


def test_login_invalid_password(client: TestClient):
    login_payload = {
        "email": "priya.sharma@demo.learningbridge.internal",
        "password": "WrongPassword123!",
    }
    response = client.post("/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "AUTHENTICATION_FAILED"
