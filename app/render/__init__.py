"""Template rendering seam: the single point where renderers are swapped."""

from app.render.base import Renderer
from app.render.errors import TemplateNotFoundError
from app.render.jinja import JinjaRenderer

__all__ = ["Renderer", "TemplateNotFoundError", "get_renderer"]


def get_renderer() -> Renderer:
    """Return the active template renderer (currently the Jinja2 renderer)."""
    return JinjaRenderer()
