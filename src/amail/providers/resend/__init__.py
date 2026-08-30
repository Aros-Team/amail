"""Resend provider package that self-registers the provider."""

from amail.providers import register
from amail.providers.resend.provider import ResendProvider

register("resend", ResendProvider)

__all__ = ["ResendProvider"]
