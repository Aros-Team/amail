from app.services.templates import get_templates, render_template


def test_get_templates_returns_all():
    templates = get_templates()
    assert "action" in templates
    assert "notification" in templates
    assert "verification" in templates
    assert "custom" in templates


def test_template_metadata_has_variables():
    templates = get_templates()
    for name, info in templates.items():
        assert "description" in info
        assert "variables" in info
        assert isinstance(info["variables"], list)


def test_render_action_template():
    html = render_template("action", {"message": "Hello", "lang": "en"})
    assert "Hello" in html
    assert "Need help?" in html


def test_render_action_template_spanish():
    html = render_template("action", {"message": "Hola", "lang": "es"})
    assert "Hola" in html
    assert "Necesitas ayuda" in html


def test_render_notification():
    html = render_template("notification", {"message": "Alert!", "heading": "Notice"})
    assert "Alert!" in html
    assert "Notice" in html


def test_render_verification():
    html = render_template("verification", {"code": "123456", "lang": "en"})
    assert "123456" in html


def test_render_custom():
    html = render_template("custom", {"content": "<p>Raw HTML</p>"})
    assert "Raw HTML" in html


def test_render_with_brand_context():
    html = render_template("action", {
        "message": "Welcome",
        "brand_name": "MyApp",
        "brand_color": "#ff0000",
        "lang": "en",
    })
    assert "MyApp" in html
    assert "#ff0000" in html or "ff0000" in html


def test_render_action_with_cta():
    html = render_template("action", {
        "message": "Click below",
        "cta_text": "Go",
        "cta_url": "https://example.com",
        "lang": "en",
    })
    assert "Go" in html
    assert "https://example.com" in html


def test_render_action_with_notification():
    html = render_template("action", {
        "message": "Test",
        "notification": {"message": "Extra info"},
        "lang": "en",
    })
    assert "Extra info" in html


def test_render_verification_with_expiry():
    html = render_template("verification", {
        "code": "999999",
        "expiry": "5 minutes",
        "lang": "en",
    })
    assert "999999" in html
    assert "Expires in" in html
    assert "5 minutes" in html
