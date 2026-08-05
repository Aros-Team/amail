"""Jinja2 template rendering and metadata for Amail emails."""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.models.schemas import TemplateVariable

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)

TEMPLATE_METADATA: dict[str, dict[str, Any]] = {
    "action": {
        "description": "Call-to-action email (welcome, password reset, invitation)",
        "variables": [
            TemplateVariable(
                name="message",
                type="string",
                description="Main message body",
                required=True,
            ),
            TemplateVariable(
                name="cta_text",
                type="string",
                description="Button label",
                required=False,
            ),
            TemplateVariable(
                name="cta_url", type="string", description="Button URL", required=False
            ),
            TemplateVariable(
                name="expiry",
                type="string",
                description="Expiration time",
                required=False,
            ),
            TemplateVariable(
                name="notification",
                type="object",
                description="Additional notice",
                required=False,
            ),
        ],
    },
    "notification": {
        "description": "General notification or alert",
        "variables": [
            TemplateVariable(
                name="heading",
                type="string",
                description="Notification heading",
                required=False,
            ),
            TemplateVariable(
                name="message", type="string", description="Content body", required=True
            ),
            TemplateVariable(
                name="details",
                type="object",
                description="Key-value detail list",
                required=False,
            ),
        ],
    },
    "verification": {
        "description": "Verification or one-time code",
        "variables": [
            TemplateVariable(
                name="code",
                type="string",
                description="Verification code",
                required=True,
            ),
            TemplateVariable(
                name="expiry",
                type="string",
                description="Expiration time",
                required=False,
            ),
        ],
    },
    "custom": {
        "description": "Custom raw HTML content wrapped in base layout",
        "variables": [
            TemplateVariable(
                name="content",
                type="string",
                description="Raw HTML body content",
                required=True,
            ),
        ],
    },
}


def build_base_context(data: dict[str, Any]) -> dict[str, Any]:
    """Extract base layout variables from data and merge the remainder."""
    return {
        "brand_name": data.pop("brand_name", ""),
        "brand_color": data.pop("brand_color", "#1a73e8"),
        "logo_url": data.pop("logo_url", None),
        "support_email": data.pop("support_email", "support@example.com"),
        "lang": data.pop("lang", "es"),
        **data,
    }


def render_template(template_name: str, data: dict[str, Any]) -> str:
    """Render a named template with the given data and return the HTML."""
    template = env.get_template(f"{template_name}.html")
    context = build_base_context(data.copy())
    return template.render(**context)


def get_templates() -> dict[str, dict[str, Any]]:
    """Return template metadata keyed by template name."""
    return {
        name: {"description": info["description"], "variables": info["variables"]}
        for name, info in TEMPLATE_METADATA.items()
    }
