from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_list_templates_returns_exact_set() -> None:
    """Verify the templates endpoint lists the expected template names."""
    resp = client.get("/api/v1/templates")
    assert resp.status_code == 200
    names = {t["name"] for t in resp.json()["templates"]}
    assert names == {"action", "notification", "verification", "custom"}


def test_render_template_ok() -> None:
    """Verify rendering a valid template returns the expected HTML."""
    resp = client.post(
        "/api/v1/templates/render",
        json={"template": "verification", "data": {"code": "123456", "lang": "en"}},
    )
    assert resp.status_code == 200
    html = resp.json()["html"]
    assert html.count("123456") == 1
    assert ">123456</span>" in html


def test_render_template_not_found() -> None:
    """Verify rendering an unknown template returns 404."""
    resp = client.post(
        "/api/v1/templates/render",
        json={"template": "does_not_exist", "data": {}},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Template 'does_not_exist' not found"


def test_render_invalid_payload_missing_template() -> None:
    """Verify a render payload without a template returns 422."""
    resp = client.post("/api/v1/templates/render", json={"data": {}})
    assert resp.status_code == 422
