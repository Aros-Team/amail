from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from typing import Any

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"])
)


def render_template(template_name: str, data: dict[str, Any]) -> str:
    template = env.get_template(f"{template_name}.html")
    return template.render(**data)


AVAILABLE_TEMPLATES = {
    "welcome": "Correo de bienvenida",
    "notification": "Notificación general",
}


def get_templates() -> dict[str, str]:
    return AVAILABLE_TEMPLATES.copy()
