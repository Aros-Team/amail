from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_list_templates():
    resp = client.get("/api/v1/templates")
    assert resp.status_code == 200
    names = {t["name"] for t in resp.json()["templates"]}
    assert {"action", "notification", "verification", "custom"} <= names


def test_render_template_ok():
    resp = client.post(
        "/api/v1/templates/render",
        json={"template": "verification", "data": {"code": "123456", "lang": "en"}},
    )
    assert resp.status_code == 200
    assert "123456" in resp.json()["html"]


def test_render_template_not_found():
    resp = client.post(
        "/api/v1/templates/render",
        json={"template": "does_not_exist", "data": {}},
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"]


def test_render_invalid_payload():
    resp = client.post("/api/v1/templates/render", json={"data": {}})
    assert resp.status_code == 422
