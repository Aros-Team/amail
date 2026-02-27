import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


@pytest.fixture
def auth_headers():
    from app.security import create_access_token

    token = create_access_token({"sub": "test-user"})
    return {"Authorization": f"Bearer {token}"}


class TestMessages:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_list_templates(self, client, auth_headers):
        response = client.get("/api/templates")
        assert response.status_code == 200
        assert "templates" in response.json()

    def test_send_requires_auth(self, client):
        response = client.post(
            "/api/send",
            json={
                "to": "test@example.com",
                "template": "welcome",
                "subject": "Test",
            },
        )
        assert response.status_code == 403

    def test_send_with_auth(self, client, auth_headers, mock_resend):
        response = client.post(
            "/api/send",
            json={
                "to": "test@example.com",
                "template": "welcome",
                "subject": "Test",
                "data": {"name": "Test"},
            },
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_receive_requires_auth(self, client):
        response = client.post(
            "/api/receive",
            json={"type": "email.received", "data": {}},
        )
        assert response.status_code == 403

    def test_receive_with_auth(self, client, auth_headers, mock_resend):
        response = client.post(
            "/api/receive",
            json={
                "type": "email.received",
                "data": {
                    "from": "support@aros.services",
                    "subject": "Test",
                    "html": "<html>Test</html>",
                },
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_get_token(self, client):
        response = client.get("/api/token")
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
