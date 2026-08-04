import re

import pytest
from jinja2 import TemplateNotFound

from app.services.templates import get_templates, render_template


def test_get_templates_returns_exact_set():
    templates = get_templates()
    assert set(templates) == {"action", "notification", "verification", "custom"}


def test_template_metadata_has_description_and_variables():
    templates = get_templates()
    for name, info in templates.items():
        assert "description" in info
        assert "variables" in info
        assert isinstance(info["variables"], list)


def test_render_action_english_message():
    html = render_template("action", {"message": "Hello", "lang": "en"})
    assert ">Hello</p>" in html
    assert "Need help?" in html


def test_render_action_spanish_message():
    html = render_template("action", {"message": "Hola", "lang": "es"})
    assert ">Hola</p>" in html
    assert "¿Necesitas ayuda?" in html


def test_render_defaults_lang_to_spanish():
    html = render_template("action", {"message": "Hi"})
    assert "¿Necesitas ayuda?" in html


def test_render_action_without_message_renders_empty_paragraph():
    html = render_template("action", {})
    assert '<p style="color:#333;font-size:16px;line-height:1.5"></p>' in html


def test_render_action_escapes_message_to_prevent_xss():
    html = render_template(
        "action", {"message": "<script>alert(1)</script>", "lang": "en"}
    )
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_render_action_with_cta_renders_button_link():
    html = render_template(
        "action",
        {
            "message": "Click below",
            "cta_text": "Go",
            "cta_url": "https://example.com",
            "lang": "en",
        },
    )
    assert 'href="https://example.com"' in html
    assert ">Go</a>" in html


def test_render_action_without_cta_renders_no_button():
    html = render_template(
        "action", {"message": "No CTA", "cta_text": "Go", "lang": "en"}
    )
    assert ">Go</a>" not in html
    assert "https://" not in html


def test_render_action_with_notification_box():
    html = render_template(
        "action",
        {"message": "Test", "notification": {"message": "Extra info"}, "lang": "en"},
    )
    assert "background-color:#fff3cd" in html
    assert ">Extra info</p>" in html


def test_render_action_with_brand_context():
    html = render_template(
        "action",
        {
            "message": "Welcome",
            "brand_name": "MyApp",
            "brand_color": "#ff0000",
            "lang": "en",
        },
    )
    assert "color:#ff0000" in html
    assert re.search(r"<h1[^>]*>.*?MyApp.*?</h1>", html, re.S)


def test_render_verification_english_code_placed_once_in_code_span():
    html = render_template("verification", {"code": "123456", "lang": "en"})
    assert html.count("123456") == 1
    assert ">123456</span>" in html
    assert "Use this code to verify your identity:" in html


def test_render_verification_spanish_text():
    html = render_template("verification", {"code": "654321", "lang": "es"})
    assert html.count("654321") == 1
    assert "Usa este codigo para verificar tu identidad:" in html


def test_render_verification_escapes_code_to_prevent_html_injection():
    html = render_template("verification", {"code": "<b>hi</b>", "lang": "en"})
    assert "<b>hi</b>" not in html
    assert "&lt;b&gt;hi&lt;/b&gt;" in html


def test_render_verification_with_expiry():
    html = render_template(
        "verification", {"code": "999999", "expiry": "5 minutes", "lang": "en"}
    )
    assert "Expires in" in html
    assert ">5 minutes</strong>" in html


def test_render_verification_without_expiry_shows_no_expiry_text():
    html = render_template("verification", {"code": "123456", "lang": "en"})
    assert "Expires in" not in html
    assert "Expira en" not in html


def test_render_notification_with_heading_and_details():
    html = render_template(
        "notification",
        {
            "heading": "Notice",
            "message": "Alert!",
            "details": {"server": "web-01"},
            "lang": "en",
        },
    )
    assert re.search(r"<h2[^>]*>\s*Notice\s*</h2>", html)
    assert re.search(r"<p[^>]*>\s*Alert!\s*</p>", html)
    assert "<li><strong>server:</strong> web-01</li>" in html


def test_render_notification_without_heading_omits_heading():
    html = render_template("notification", {"message": "Alert!", "lang": "en"})
    assert "</h2>" not in html
    assert re.search(r"<p[^>]*>\s*Alert!\s*</p>", html)


def test_render_custom_passes_raw_html_through():
    html = render_template("custom", {"content": "<p>Raw HTML</p>"})
    assert "<p>Raw HTML</p>" in html


def test_render_unknown_template_raises_template_not_found():
    with pytest.raises(TemplateNotFound):
        render_template("does_not_exist", {})
