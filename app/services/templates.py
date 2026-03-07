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


class TemplateVariable:
    def __init__(self, name: str, type: str, description: str, required: bool = True):
        self.name = name
        self.type = type
        self.description = description
        self.required = required


AVAILABLE_TEMPLATES = {
    "welcome": {
        "description": "Correo de bienvenida",
        "variables": [
            TemplateVariable("name", "string", "Nombre del usuario (opcional)", False),
            TemplateVariable("message", "string", "Mensaje de bienvenida", True),
        ],
    },
    "notification": {
        "description": "Notificación general",
        "variables": [
            TemplateVariable("message", "string", "Contenido de la notificación", True),
        ],
    },
    "two_factor": {
        "description": "Código de verificación de dos factores",
        "variables": [
            TemplateVariable("code", "string", "Código de 6 dígitos", True),
            TemplateVariable("expiry", "string", "Minutos hasta expiración (opcional)", False),
        ],
    },
}


def get_templates() -> dict[str, dict]:
    return {
        name: {"description": info["description"], "variables": [
            {"name": v.name, "type": v.type, "description": v.description, "required": v.required}
            for v in info["variables"]
        ]}
        for name, info in AVAILABLE_TEMPLATES.items()
    }
