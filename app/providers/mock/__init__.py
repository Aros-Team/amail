from app.providers.mock.provider import MockProvider
from app.providers import register

register("mock", MockProvider)

__all__ = ["MockProvider"]
