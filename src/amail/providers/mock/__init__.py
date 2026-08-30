"""Mock provider package that self-registers the provider."""

from amail.providers import register
from amail.providers.mock.provider import MockProvider

register("mock", MockProvider)

__all__ = ["MockProvider"]
