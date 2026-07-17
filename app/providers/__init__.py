from typing import TYPE_CHECKING

from app.contracts.sender import EmailSender
from app.contracts.receiver import EmailReceiver

if TYPE_CHECKING:
    from app.providers.base import EmailProvider

_registry: dict[str, type["EmailProvider"]] = {}


def register(name: str, cls: type["EmailProvider"]) -> None:
    _registry[name] = cls


def get_provider(name: str | None = None) -> "EmailProvider":
    from app.config import get_settings

    provider_name = name or get_settings().email_provider
    if provider_name not in _registry:
        msg = f"Unknown provider: {provider_name}. Available: {list(_registry.keys())}"
        raise ValueError(msg)
    return _registry[provider_name]()


def get_sender() -> EmailSender:
    return get_provider().sender


def get_receiver() -> EmailReceiver | None:
    return get_provider().receiver


__all__ = ["register", "get_provider", "get_sender", "get_receiver"]
