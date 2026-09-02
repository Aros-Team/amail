"""Provider registry and factory helpers."""

from typing import TYPE_CHECKING

from amail.contracts.receiver import EmailReceiver
from amail.contracts.sender import EmailSender

if TYPE_CHECKING:
    from amail.providers.base import EmailProvider

_registry: dict[str, type["EmailProvider"]] = {}
_provider_instance: dict[str, "EmailProvider"] = {}


def register(name: str, cls: type["EmailProvider"]) -> None:
    """Register a provider class under the given name."""
    _registry[name] = cls


def get_provider(name: str | None = None) -> "EmailProvider":
    """Return a cached provider instance, optionally selecting by name."""
    from amail.config import get_settings

    provider_name = name or get_settings().email_provider
    if provider_name not in _registry:
        msg = f"Unknown provider: {provider_name}. Available: {list(_registry.keys())}"
        raise ValueError(msg)

    if provider_name not in _provider_instance:
        _provider_instance[provider_name] = _registry[provider_name]()
    return _provider_instance[provider_name]


def reset_provider(name: str | None = None) -> None:
    """Clear cached provider so next get_provider() creates a new one."""
    from amail.config import get_settings

    provider_name = name or get_settings().email_provider
    _provider_instance.pop(provider_name, None)


def get_sender() -> EmailSender:
    """Return the active provider's sender."""
    return get_provider().sender


def get_receiver() -> EmailReceiver | None:
    """Return the active provider's receiver, if any."""
    return get_provider().receiver


__all__ = ["register", "get_provider", "get_sender", "get_receiver", "reset_provider"]
