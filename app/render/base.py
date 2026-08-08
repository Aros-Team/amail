"""Renderer abstraction for the email template system."""

from abc import ABC, abstractmethod
from typing import Any


class Renderer(ABC):
    """Contract every template renderer must satisfy."""

    @abstractmethod
    def render(self, name: str, data: dict[str, Any]) -> str:
        """Render the named template to HTML for the given data."""

    @abstractmethod
    def get_templates(self) -> dict[str, dict[str, Any]]:
        """Return template metadata keyed by name (description + variables)."""
