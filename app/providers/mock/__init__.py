"""Mock provider package that self-registers the provider."""

from app.providers import register
from app.providers.mock.provider import MockProvider

register("mock", MockProvider)

__all__ = ["MockProvider"]
