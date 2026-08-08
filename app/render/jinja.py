"""Jinja2-backed implementation of the Renderer seam."""

from typing import Any

from jinja2 import TemplateNotFound

from app.render.base import Renderer
from app.render.errors import TemplateNotFoundError
from app.services.templates import get_templates, render_template


class JinjaRenderer(Renderer):
    """Renderer that produces HTML via the Jinja2 template engine."""

    def render(self, name: str, data: dict[str, Any]) -> str:
        """Render a named template to HTML, mapping engine errors to project errors."""
        try:
            return render_template(name, data)
        except TemplateNotFound as e:
            raise TemplateNotFoundError(f"Template '{name}' not found") from e

    def get_templates(self) -> dict[str, dict[str, Any]]:
        """Return template metadata keyed by name (description + variables)."""
        return get_templates()
