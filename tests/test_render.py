"""Tests for the template rendering seam (app/render)."""

import pytest
from jinja2 import TemplateNotFound as JinjaTemplateNotFound

from app.render import TemplateNotFoundError, get_renderer
from app.render.base import Renderer


def test_get_renderer_renders_action_template() -> None:
    """Verify the active renderer renders the action template to HTML."""
    renderer = get_renderer()
    html = renderer.render("action", {"message": "Hi", "lang": "en"})
    assert ">Hi</p>" in html
    assert "Need help?" in html


def test_render_escapes_user_message_to_prevent_xss() -> None:
    """Verify renderer escapes user input to prevent XSS."""
    renderer = get_renderer()
    html = renderer.render(
        "action", {"message": "<script>alert(1)</script>", "lang": "en"}
    )
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_render_unknown_template_raises_project_error() -> None:
    """Verify rendering an unknown template raises the project error class."""
    renderer = get_renderer()
    with pytest.raises(TemplateNotFoundError) as exc_info:
        renderer.render("does_not_exist", {})
    assert not isinstance(exc_info.value, JinjaTemplateNotFound)


def test_get_templates_returns_exact_set_with_metadata() -> None:
    """Verify get_templates returns the expected set with metadata."""
    renderer = get_renderer()
    templates = renderer.get_templates()
    assert set(templates) == {"action", "notification", "verification", "custom"}
    for info in templates.values():
        assert "description" in info
        assert "variables" in info
        assert isinstance(info["variables"], list)


def test_jinja_renderer_implements_renderer_interface() -> None:
    """Verify JinjaRenderer satisfies the Renderer contract."""
    renderer = get_renderer()
    assert isinstance(renderer, Renderer)
