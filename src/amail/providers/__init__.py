"""Provider registry and factory helpers."""

from typing import TYPE_CHECKING

from amail.contracts.receiver import EmailReceiver
from amail.contracts.sender import EmailSender

if TYPE_CHECKING:
    from amail.providers.base import EmailProvider

_registry: dict[str, type["EmailProvider"]] = {}


def register(name: str, cls: type["EmailProvider"]) -> None:
    """Register a provider class under the given name."""
    _registry[name] = cls


def get_provider(name: str | None = None) -> "EmailProvider":
    """Return an instantiated provider, optionally selecting by name."""
    from amail.config import get_settings

    provider_name = name or get_settings().email_provider
    if provider_name not in _registry:
        msg = f"Unknown provider: {provider_name}. Available: {list(_registry.keys())}"
        raise ValueError(msg)
    return _registry[provider_name]()


def get_sender() -> EmailSender:
    """Return the active provider's sender."""
    return get_provider().sender


def get_receiver() -> EmailReceiver | None:
    """Return the active provider's receiver, if any."""
    return get_provider().receiver


__all__ = ["register", "get_provider", "get_sender", "get_receiver"]
